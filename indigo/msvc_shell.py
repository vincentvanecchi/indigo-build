from enum import Enum
from dataclasses import dataclass, field
from typing import Callable

from indigo.filesystem import PathLike, remove_file, get_file_name, get_file_line

from indigo.console_text_styles import *
from indigo.basic_shell import _Shell_Exec, _Shell_Exec_Async, _Async_Command


class _Msvc_Error(RuntimeError):
    pass

class _Msvc_Tool(Enum):
    CL = 'CL.EXE'
    LINK = 'LINK.EXE'
    LIB = 'LIB.EXE'

@dataclass 
class _Msvc_Job:
    name: str
    command: _Async_Command
    callback: Callable[[int], bool] = None

    def _Await(self) -> bool:
        try:
            _, _, returncode = self.command._Await()
            if self.callback:
                try:
                    return self.callback(returncode)
                except AssertionError as e:
                    import traceback
                    cts_print_warning(section='task', text=f'in task {self.name}: AssertionError:')
                    traceback.print_tb(e.__traceback__)
                    return False
            else: 
                return returncode == 0
        except _Msvc_Error as e:
            # consume error locations
            _Msvc._Error_Summary(e)
            return False 

_Msvc_Instance = None
class _Msvc:
    def __init__(self, jobs: int = 0):
        self._cl = None
        self._link = None
        self._lib = None

        if not jobs:
            from os import cpu_count
            jobs = cpu_count()
        self._max_jobs = jobs
        self._jobs = list()

        assert self._Available(), \
            "MSVC tools were not found. Try Launch-VSDevShell.ps1 [-Arch amd64] first."
    
    @staticmethod
    def _Instance() -> '_Msvc':
        global _Msvc_Instance
        if not _Msvc_Instance:
            _Msvc_Instance = _Msvc()
        return _Msvc_Instance
        
    def _Available(self) -> bool:
        import subprocess
        try:
            self._cl = subprocess.run(f"CMD.EXE /C \"WHERE.EXE {_Msvc_Tool.CL.value}\"", 
                                        capture_output=True, check=True
                                    ).stdout.decode().strip()
            self._link = subprocess.run(f"CMD.EXE /C \"WHERE.EXE {_Msvc_Tool.LINK.value}\"", 
                                        capture_output=True, check=True
                                    ).stdout.decode().strip()
            self._lib = subprocess.run(f"CMD.EXE /C \"WHERE.EXE {_Msvc_Tool.LIB.value}\"", 
                                       capture_output=True, check=True
                                    ).stdout.decode().strip()
            return True
        except subprocess.CalledProcessError:
            pass
        return False

    @staticmethod
    def _Default_Logger(section: str, subsection: str, text: str):
        cts_print(section=section, subsection=subsection, text=text)

    @staticmethod
    def _Default_Parser(
        stdout: str,
        stderr: str,
        returncode: int
    ) -> tuple[str, str, int]:
        cts_print_subprocess((stdout, stderr, returncode))
        return stdout, stderr, returncode
    
    @staticmethod
    def _Parser(
        stdout: str,
        stderr: str,
        returncode: int
    ) -> tuple[str, str, int]:
        if not stdout:
            return stdout, stderr, returncode

        stdoutlines = stdout.splitlines()
        if len(stdoutlines) > 1 and not stdoutlines[0].startswith('Microsoft (R)'):
            cts_print(text=stdoutlines[0], text_style=cts_underline, tab='  ')
        
        errors = list()
        for line in stdoutlines[1:]:
            if not line:
                continue
            elif line.startswith('Microsoft (R)') or line.startswith('Copyright (C)'):
                continue
            elif 'error C' in line or 'error LNK' in line:
                cts_print_error(text=line)
                _ = line.split(':')
                __ = _[0].strip()
                if len(__) < 3:
                    # drive
                    __ = _[1].strip()
                errors.append(__ if __.endswith(')') else line)
            elif 'warning C' in line or 'warning LNK' in line:
                cts_print_warning(text=line)
            else:
                cts_print_info(text=line)
        
        if errors:
            raise _Msvc_Error(*errors)

        return stdout, stderr, returncode
        
    @staticmethod
    def _Error_Summary(err: _Msvc_Error):
        if err.args:
            cts_print(section='mvsc', text='error locations summary:')
            # remove duplicates
            locations = []
            [ locations.append(l) for l in err.args if l not in locations ]
            # log locations
            for error_location in locations:
                _ = error_location.split('(')
                assert len(_) == 2, f'bad error location: {error_location}'
                filename, line = _
                line = line[:-1]
                line_content = get_file_line(filename, int(line) - 1) or 'N/A'
                cts_print(
                    section=get_file_name(filename), 
                    section_style=cts_underline,
                    subsection=str(line), 
                    subsection_style=cts_pass,
                    text=line_content,
                    tab='  '
                )

    def _Tool_Path(self, tool: _Msvc_Tool) -> PathLike:
        # aight
        if isinstance(tool, str):
            if not tool.endswith('.exe'):
                raise ValueError(type(tool))
            return tool

        match tool:
            case _Msvc_Tool.CL:
                return self._cl
            case _Msvc_Tool.LINK:
                return self._link
            case _Msvc_Tool.LIB:
                return self._lib
            case _:
                raise ValueError(f'no such tool {tool}')


    def _Exec(self, tool: _Msvc_Tool, args: tuple[str]|str) -> bool:
        try:
            is_build_job = isinstance(tool, _Msvc_Tool)
            executable = self._Tool_Path(tool)

            if isinstance(args, str):
                args = [ tool.value if is_build_job else tool, *(args.split(' ')) ]
            else:
                args = [ tool.value if is_build_job else tool, *args ]
                
            _, _, returncode = _Shell_Exec(
                executable=executable, 
                args=args,
                logger=_Msvc._Default_Logger, 
                parser=_Msvc._Parser if is_build_job else _Msvc._Default_Parser
            )
            return returncode == 0
        except _Msvc_Error as e:
            # consume error locations
            _Msvc._Error_Summary(e)
            return False

    def _Fail_Fast(self):
        for job in self._jobs:
            job._Await()
        self._jobs.clear()

    def _Exec_Async(self, name: str, tool: _Msvc_Tool, args: tuple[str]|str, callback: Callable[[], bool] = None) -> bool:
        while len(self._jobs) >= self._max_jobs:
            job: _Msvc_Job = self._jobs.pop(0)
            if not job._Await():
                self._Fail_Fast()
                return False

        is_build_job = isinstance(tool, _Msvc_Tool)
        if isinstance(args, str):
            args = [ tool.value if is_build_job else tool, *(args.split(' ')) ]
        else:
            args = [ tool.value if is_build_job else tool, *args ]

        try:
            executable = self._Tool_Path(tool)
            logger = _Msvc._Default_Logger
            parser = _Msvc._Default_Parser
            if is_build_job:
                parser = _Msvc._Parser

            cmd = _Shell_Exec_Async(name, executable, args, logger, parser)
            self._jobs.append( _Msvc_Job(name, cmd, callback) )
            return True
        except:
            self._Fail_Fast()
            raise

    
    def produce_object(self, args: tuple[str]|str) -> bool:
        return self._Exec(_Msvc_Tool.CL, args)

    def produce_object_async(self, path: PathLike, args: tuple[str]|str, callback: Callable[[int], bool] = None) -> bool:
        return self._Exec_Async(path, _Msvc_Tool.CL, args, callback)
    
    def await_jobs(self) -> bool:
        if not self._jobs:
            return True
        success = True
        while self._jobs:
            job = self._jobs.pop(0)
            success = success and job._Await()
        return success
        
    def produce_executable(self, args: tuple[str]|str) -> bool:
        return self._Exec(_Msvc_Tool.LINK, args)
    
    def produce_dynamic_library(self, args: tuple[str]|str) -> bool:
        return self._Exec(_Msvc_Tool.LINK, args)
        
    def produce_static_library(self, args: tuple[str]|str) -> bool:
        return self._Exec(_Msvc_Tool.LIB, args)

if __name__ == '__main__':
    def test():
        msvc = _Msvc()
        
        def cleanup():
            try:
                for f in ('example/goodmain.obj', 'example/goodmain.exe', 'example/badmain.obj', 'example/badmain.exe'):
                    remove_file(f)
            except:
                pass
        
        try:
            cleanup()
            print('[Building badmain.cpp]')
            compiled = msvc.produce_object('/EHsc /std:c++latest /C example/badmain.cpp /Fo:example/badmain.obj /Fe:example/badmain.exe') \
                        and msvc.produce_executable('/MACHINE:X64 example/badmain.obj /OUT:example/badmain.exe')
            assert not compiled, '[Built badmain.exe, expected to fail]'
            print('[Could not build badmain.exe as expected]')
            print()
            
            print('[Building goodmain.cpp]')
            compiled = msvc.produce_object('/EHsc /std:c++latest /C example/goodmain.cpp /Fo:example/goodmain.obj /Fe:example/goodmain.exe') \
                        and msvc.produce_executable('/MACHINE:X64 example/goodmain.obj /OUT:example/goodmain.exe')
            assert compiled, '[Could not build goodmain.exe, expected to succeed]'
            print('[Built goodmain.exe as expected]')
            cleanup()
        except AssertionError:
            cleanup()
            raise
    test()