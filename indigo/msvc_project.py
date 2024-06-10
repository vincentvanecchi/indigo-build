from dataclasses import dataclass, field
from typing import Callable
from functools import cache, cached_property

from indigo.filesystem import *

from indigo.msvc_flags import \
    _CFlag, _LFlag, _IfcFlag, _Warnings_Mode, _Debug_Mode, \
    build_msvc_compile_flags, \
    build_msvc_lib_flags, \
    build_msvc_link_flags, \
    build_msvc_c_flags, \
    build_msvc_cpp_flags, \
    build_msvc_ifc_flags, \
    build_msvc_hxx_flags, \
    build_msvc_ixx_flags, \
    build_msvc_cxx_flags, \
    build_msvc_uxx_flags, \
    dump_msvc_ifc_map, \
    _Module, _Header_Unit, _Translation_Unit

from indigo.msvc_shell import _Msvc, _Msvc_Error, _Msvc_Job, \
    cts_header, cts_warning, cts_fail, cts_underline, cts_okcyan, cts_okgreen, cts_bold

from indigo.project import Project, CompilationError

@dataclass
class _Msvc_Project(Project):
    ifc_search_directory: PathLike = None
    
    _msvc: _Msvc = field(default_factory=_Msvc._Instance)
    _deferred_commands: list[ Callable[[], bool] ] = field(default_factory=list)
    _rebuilt_files: int = 0

    def __post_init__(self):
        Project.__post_init__(self)

        if not self.ifc_search_directory:
            self.ifc_search_directory = join(self.build_directory, 'ifc')
        
        if not path_exists(self.ifc_search_directory):
            create_directory(self.ifc_search_directory)

    def _on_clean(self):
        assert self.ifc_search_directory
        clean_directory(self.ifc_search_directory)
        print(f':{cts_header("project")}: {cts_okcyan(self.name)} > cleaned')

    def _on_build(self, building: bool):
        if building:
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > building ...')
        else:
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > nothing to build')

    def _on_built(self, elapsed: float):
        print(f':{cts_header("project")}: {cts_okcyan(self.name)} > {cts_okgreen("built")} in {elapsed:.3f}s')

    def _on_test(self, running: bool):
        if running:
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > testing ...')
        else:
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > nothing to test')

    def _on_test_start(self, test: PathLike):
        print(f':{cts_header("project")}: {cts_okcyan(self.name)} > test {cts_warning(get_file_name(test, strip_ext=True)[len("test_"):])}')
    
    def _on_test_finish(self, test: PathLike, code: int):
        if code == 0:
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > test {cts_warning(get_file_name(test, strip_ext=True)[len("test_"):])}: {cts_okgreen("SUCCESS")} (exited with code {code})')
        else:
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > test {cts_warning(get_file_name(test, strip_ext=True)[len("test_"):])}: {cts_fail("FAILURE")} (exited with code {code})')

    def _on_config(self):
        cts_pass = lambda x: f"'{x}'"
        print(f'  {"[" + cts_warning("msvc") + "]"}')
        print(f'    {cts_okgreen("ifc search directory"):<30} = {cts_pass(self.ifc_search_directory)}')
        print(f'    {cts_okgreen("ifc map path"):<30} = {cts_pass(self.ifc_map_path)}')

    @cached_property
    def ifc_map_path(self) -> PathLike:
        assert self.ifc_search_directory
        return join(self.ifc_search_directory, 'ifcMap.toml')

    def dump_ifc_map(self) -> PathLike:
        ifc_map = self.ifc_map_path
        if (self.header_units or self.module_interfaces) \
            and path_exists(self.static_library_path) \
            and is_modified_after(self.static_library_path, ifc_map):
            dump_msvc_ifc_map(
                ifc_map, 
                self.ifc_search_directory, 
                self.module_interfaces, 
                self.header_units
                )
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > {cts_okgreen("wrote")} ifc map to {ifc_map}')
            return ifc_map
        else:
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > nothing to write in ifc map')
            return None
        
    def resolve_modified_dependencies(self, modified_files: list[PathLike]) -> list[PathLike]:
        if modified_files:
            # TODO: incremental builds
            return self.source_files
        return modified_files

    def cached_object_path(self, source: PathLike) -> PathLike:
        assert self.cache_directory
        return join(self.cache_directory, get_dot_path(source, add_ext='.obj'))
    
    def unit_test_object_path(self, uxx: PathLike) -> PathLike:
        assert self.cache_directory
        return join(self.cache_directory, get_dot_path(uxx, add_ext='.obj'))
    
    def unit_test_executable(self, uxx: PathLike) -> PathLike:
        assert self.build_directory
        return join(self.build_directory, get_dot_path(uxx, add_ext='.exe', strip_ext=True))
    
    def unit_test_debug_information(self, uxx: PathLike) -> PathLike:
        assert self.build_directory
        return join(self.build_directory, get_dot_path(uxx, add_ext='.pdb', strip_ext=True))

    def run_unit_test(self, exe: PathLike) -> bool:
        return self._msvc._Exec(exe, tuple())

    def run_unit_test_async(self, exe: PathLike) -> bool:
        def callback(code: int) -> bool:
            self._on_test_finish(exe, code)
            return code == 0
        
        return self._msvc._Exec_Async(get_file_name(exe), exe, tuple(), callback)

    def await_unit_tests(self) -> bool:
        return self._msvc.await_jobs()

    def compile_source_file(self, source: PathLike):
        ext = get_file_extension(source)
        match ext:
            case '.c':
                self.compile_c_translation_unit(source)
            case '.cpp':
                self.compile_cpp_translation_unit(source)
            case '.hxx':
                self.compile_header_unit(source)
            case '.ixx':
                self.compile_module_interface(source)
            case '.cxx':
                self.compile_module_implementation(source)
            case '.uxx':
                self.compile_unit_test(source)
            case _:
                raise ValueError(f'unsupported source file extension: {ext}')

    def _Basic_compiler_flags(self, cxx: bool = True):
        warnings = _Warnings_Mode._Match(self.options.warning_level, self.options.treat_warnings_as_errors)
        debug = _Debug_Mode._Match(self.options.enable_debug_information, self.options.disable_optimizations, False)
        flags = build_msvc_compile_flags(
            standard=_CFlag.CXXStandard if cxx else _CFlag.CStandard, 
            exceptions=_CFlag.CXXExceptions if cxx else '',
            warnings=warnings, 
            debug=debug
            )
        
        flags.append(_CFlag.IncludeDirectory(
            self.source_directory
            # relative_directory(self.source_directory, self.root_directory)
        ))
        
        for dependency in self.dependencies.values():
            if not path_exists(dependency.static_library_path):
                dependency.build()
            assert path_exists(dependency.static_library_path)

            flags.append(_CFlag.IncludeDirectory(
                dependency.source_directory
                # relative_directory(dependency.source_directory, self.root_directory)
            ))
            
            if isinstance(dependency, _Msvc_Project) and path_exists(dependency.ifc_map_path):
                flags.append(_IfcFlag.IfcMap)
                flags.append(dependency.ifc_map_path)

        # this options is ignored in linkless builds (cl.exe /c)
        # flags.append(_CFlag.EXEPath(self.executable_path))
        
        if self.options.enable_debug_information: # and not self.options.legacy_debug_information:
            flags.append(_CFlag.EnableDebugInformationSynchronization)
            flags.append(_CFlag.PDBPath(self.debug_information_path))

        return flags
    
    def _Dependencies_static_libraries(self) -> list[str]:
        libs = []
        
        for dependency in self.dependencies.values():
            if not path_exists(dependency.static_library_path):
                dependency.build()
            assert path_exists(dependency.static_library_path)

            libs.append(dependency.static_library_path)
        
        return libs
    
    def _Basic_dll_flags(self):
        flags = build_msvc_link_flags(self.options.warning_level > 0, self.options.enable_debug_information)

        flags.append( _LFlag.DLLPath(self.dynamic_library_path) )
        flags += self._Dependencies_static_libraries()

        return flags
    
    def _Basic_exe_flags(self):
        flags = build_msvc_link_flags(self.options.warning_level > 0, self.options.enable_debug_information)

        flags.append( _LFlag.EXEPath(self.executable_path) )
        
        if path_exists(self.static_library_path):
            flags.append(self.static_library_path)
        else:
            flags += self._Dependencies_static_libraries()

        return flags

    def _Basic_lib_flags(self):
        flags = build_msvc_lib_flags(self.options.warning_level > 0, self.options.enable_debug_information)
    
        flags.append( _LFlag.LIBPath(self.static_library_path) )
        flags += self._Dependencies_static_libraries()

        return flags
    

    def compile_header_unit(self, hxx: PathLike):
        flags = self._Basic_compiler_flags()
        
        flags += build_msvc_hxx_flags(hxx, 
            self.header_units, 
            self.source_directory, 
            self.ifc_search_directory, 
            self.cache_directory
            )
        
        if not self._msvc.produce_object(flags):
            raise CompilationError(hxx)

        self.header_units.add(hxx)
        self.object_files.add(self.cached_object_path(hxx))
        self._rebuilt_files += 1

    
    def compile_module_interface(self, ixx: PathLike):
        flags = self._Basic_compiler_flags()
        
        flags += build_msvc_ixx_flags(ixx, 
            self.header_units, 
            self.source_directory, 
            self.ifc_search_directory, 
            self.cache_directory
            )
        
        if not self._msvc.produce_object(flags):
            raise CompilationError(ixx)

        self.module_interfaces.add(ixx)
        self.object_files.add(self.cached_object_path(ixx))
        self._rebuilt_files += 1
    
    def compile_module_implementation(self, cxx: PathLike):
        args = self._Basic_compiler_flags()
        
        args += build_msvc_cxx_flags(cxx, 
            self.header_units, 
            self.source_directory, 
            self.ifc_search_directory, 
            self.cache_directory
            )

        def command() -> bool:
            def callback(code: int) -> bool:
                if code != 0:
                    return False
                self.module_implementations.add(cxx)
                self.object_files.add(self.cached_object_path(cxx))
                self._rebuilt_files += 1
                return True
            
            if not self._msvc.produce_object_async(cxx, args, callback):
                raise CompilationError(cxx)

            return True
        
        self._deferred_commands.append(command)
    
    def compile_c_translation_unit(self, c: PathLike):
        args = self._Basic_compiler_flags(cxx=False)
        
        args += build_msvc_c_flags(c,
            self.source_directory,
            self.cache_directory)
        
        def command() -> bool:
            def callback(code: int) -> bool:
                if code != 0:
                    return False
                self.translation_units.add(c)
                if get_file_name(c) == 'main.c':
                    assert not self.main_translation_unit
                    self.main_translation_unit = c
                else:
                    self.object_files.add(self.cached_object_path(c))
                self._rebuilt_files += 1
                return True

            if not self._msvc.produce_object_async(c, args, callback):
                raise CompilationError(c)

            return True
        
        self._deferred_commands.append(command)
    
    def compile_cpp_translation_unit(self, cpp: PathLike):
        args = self._Basic_compiler_flags()
        
        args += build_msvc_cpp_flags(cpp, 
            self.header_units, 
            self.source_directory, 
            self.ifc_search_directory, 
            self.cache_directory
            )
        
        if get_file_name(cpp) == 'main.cpp':
            assert not self.main_translation_unit
            self.main_translation_unit = cpp
            self.build_static_library()

            if path_exists(self.ifc_map_path):
                args.append(_IfcFlag.IfcMap)
                args.append(self.ifc_map_path)
            
            if not self._msvc.produce_object(args):
                raise CompilationError(cpp)
            
            self._rebuilt_files += 1
            return
        
        def command() -> bool:
            def callback(code: int) -> bool:
                if code != 0:
                    return False
                self.translation_units.add(cpp)
                self.object_files.add(self.cached_object_path(cpp))
                self._rebuilt_files += 1
                return True
            
            if not self._msvc.produce_object_async(cpp, args, callback):
                raise CompilationError(cpp)
            
            return True

        self._deferred_commands.append(command)

    def compile_unit_test(self, uxx: PathLike) -> PathLike:
        obj = self.unit_test_object_path(uxx)

        args = build_msvc_compile_flags()
        args += build_msvc_uxx_flags(uxx, 
            self.header_units, 
            self.tests_directory, 
            self.ifc_search_directory, 
            self.cache_directory)
        
        args.append(_CFlag.PDBPath(self.unit_test_debug_information(uxx)))
        
        args.append(_CFlag.IncludeDirectory(self.source_directory))
        args.append(_CFlag.IncludeDirectory(self.tests_directory))

        for dependency in self.dependencies.values():
            if not path_exists(dependency.static_library_path):
                dependency.build()
            assert path_exists(dependency.static_library_path)

            args.append(_CFlag.IncludeDirectory(
                dependency.source_directory
                # relative_directory(dependency.source_directory, self.root_directory)
            ))
            
            if isinstance(dependency, _Msvc_Project) and path_exists(dependency.ifc_map_path):
                args.append(_IfcFlag.IfcMap)
                args.append(dependency.ifc_map_path)
        
        if path_exists(self.ifc_map_path):
            args.append(_IfcFlag.IfcMap)
            args.append(self.ifc_map_path)

        if not self._msvc.produce_object_async(uxx, args):
            raise CompilationError(uxx)

        return obj

    def _Await_deferred_commands(self):
        if self._deferred_commands:
            for command in self._deferred_commands:
                if not command():
                    self._deferred_commands.clear()
                    raise CompilationError()
            self._deferred_commands.clear()

        if not self._msvc.await_jobs():
            raise CompilationError()

    def build_unit_test(self, uxx: PathLike, obj: PathLike):
        if not self._msvc.await_jobs():
            raise CompilationError()
        
        args = build_msvc_link_flags()

        args.append(_LFlag.EXEPath(self.unit_test_executable(uxx)))
        args.append(obj)

        if path_exists(self.static_library_path):
            args.append(self.static_library_path)
        else:
            args += self._Dependencies_static_libraries()

        self._msvc.produce_executable(args)

    def build_dynamic_library(self):
        """
            Produces dynamic library from this Project's compiled object files.
        """
        pass

    def build_static_library(self):
        self._Await_deferred_commands()

        if self.object_files and path_exists(self.static_library_path) and not self._rebuilt_files:
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > Not linking static library: no changes since last build.')
            return

        args = self._Basic_lib_flags()
        
        for object in self.object_files:
            args.append(object)

        self._msvc.produce_static_library(args)
        self.dump_ifc_map()

    def build_executable(self):
        self._Await_deferred_commands()

        if not self.main_translation_unit:
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > Not linking executable: main translation unit was not found')
            return
        
        if path_exists(self.executable_path) and not self._rebuilt_files:
            print(f':{cts_header("project")}: {cts_okcyan(self.name)} > Not linking executable: no changes since last build.')
            return
        
        args = self._Basic_exe_flags()
        
        args.append(self.cached_object_path(self.main_translation_unit))

        self._msvc.produce_executable(args)


if __name__ == '__main__':
    pass
