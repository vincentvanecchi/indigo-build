
import subprocess
from typing import Callable
from dataclasses import dataclass, field

from build_system.filesystem import PathLike, get_file_name

class _Console_Text_Style:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def cts_header(text: str) -> str:
    return _Console_Text_Style.HEADER + text + _Console_Text_Style.ENDC

def cts_okblue(text: str) -> str:
    return _Console_Text_Style.OKBLUE + text + _Console_Text_Style.ENDC

def cts_okcyan(text: str) -> str:
    return _Console_Text_Style.OKCYAN + text + _Console_Text_Style.ENDC

def cts_okgreen(text: str) -> str:
    return _Console_Text_Style.OKGREEN + text + _Console_Text_Style.ENDC

def cts_warning(text: str) -> str:
    return _Console_Text_Style.WARNING + text + _Console_Text_Style.ENDC

def cts_fail(text: str) -> str:
    return _Console_Text_Style.FAIL + text + _Console_Text_Style.ENDC

def cts_bold(text: str) -> str:
    return _Console_Text_Style.BOLD + text + _Console_Text_Style.ENDC

def cts_underline(text: str) -> str:
    return _Console_Text_Style.UNDERLINE + text + _Console_Text_Style.ENDC

def cts_break(text: str, style: str = _Console_Text_Style.UNDERLINE) -> str:
    return _Console_Text_Style.ENDC + text + style

def _Shell_Exec(
    executable: PathLike,
    args: tuple|str = tuple(), 
    logger: Callable[[PathLike, tuple|str], None] = None,
    parser: Callable[[str, str, int], tuple[str, str, int]] = None
) -> tuple[str, str, int]:
    assert executable

    if logger:
        logger(get_file_name(executable), args)

    r = subprocess.run(executable=executable, args=args, capture_output=True)
    
    stdout = r.stdout.decode().strip()
    stderr = r.stderr.decode().strip()
    returncode = r.returncode

    if parser:
        return parser(stdout, stderr, returncode)
    else:
        return (stdout, stderr, returncode)

@dataclass 
class _Async_Command:
    name: str
    executable: PathLike
    process: subprocess.Popen = None
    logger: Callable[[PathLike, tuple|str], None] = None
    parser: Callable[[str, str, int], tuple[str, str, int]] = None

    def _Await(self, input = None, timeout = None) -> tuple[str, str, int]:
        returncode = 0
        stdout = b''
        stderr = b''
        with self.process:
            try:
                stdout, stderr = self.process.communicate(input=input, timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                self.process.kill()
                if subprocess._mswindows:
                    # Windows accumulates the output in a single blocking
                    # read() call run on child threads, with the timeout
                    # being done in a join() on those threads.  communicate()
                    # _after_ kill() is required to collect that and add it
                    # to the exception.
                    exc.stdout, exc.stderr = self.process.communicate()
                else:
                    # POSIX _communicate already populated the output so
                    # far into the TimeoutExpired exception.
                    self.process.wait()
                raise
            except:  # Including KeyboardInterrupt, communicate handled that.
                self.process.kill()
                # We don't call process.wait() as .__exit__ does that for us.
                raise
            returncode = self.process.poll()

        self.logger(f'await{cts_break(": ")}{self.name}', tuple())
        
        stdout = stdout.decode().strip()
        stderr = stderr.decode().strip()

        if self.parser:
            return self.parser(stdout, stderr, returncode)
        else:
            return (stdout, stderr, returncode)

def _Shell_Exec_Async(
    name: str,
    executable: PathLike,
    args: tuple|str = tuple(), 
    logger: Callable[[str, tuple|str], None] = None,
    parser: Callable[[str, str, int], tuple[str, str, int]] = None
) -> _Async_Command:
    if logger:
        logger(f'async{cts_break(": ")}{name}', args)

    return _Async_Command(
        name=name,
        executable=executable,
        process=subprocess.Popen(executable=executable, 
                                args=args, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE
                                ),
        logger=logger,
        parser=parser
    )
