from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from argparse import ArgumentParser, Namespace

from indigo.filesystem import PathLike, \
    join, path_exists, \
    create_directory, remove_directory, \
    clean_directory, list_directory, \
    relative_directory, current_directory, \
    is_modified_after, get_dot_path, get_file_name, get_file_extension

from indigo.options import Options
from indigo.console_text_styles import *

class CompilationError(RuntimeError):
    pass

class TestingError(RuntimeError):
    pass

@dataclass
class Target(ABC):
    name: str

    source_directory: PathLike
    build_directory: PathLike
    source_files: list[PathLike]
    
    root_directory: PathLike = None
    cache_directory: PathLike = None
    tests_directory: PathLike = None
    output_directory: PathLike = None

    header_units: set[PathLike] = field(default_factory=set)
    module_interfaces: set[PathLike] = field(default_factory=set)
    module_implementations: set[PathLike] = field(default_factory=set)
    translation_units: set[PathLike] = field(default_factory=set)
    main_translation_unit: Optional[PathLike] = None
    object_files: set[PathLike] = field(default_factory=set)

    dependencies: list[str] = field(default_factory=list)
    options: Options = field(default_factory=Options)

    _subtargets: list['Target'] = field(default_factory=list, init=False, repr=False, hash=False, compare=False, kw_only=True)
    _is_visited: bool = field(default=False, init=False, repr=False, hash=False, compare=False, kw_only=True)
    _should_relink: bool = field(default=False, init=False, repr=False, hash=False, compare=False, kw_only=True)

    def __post_init__(self):
        assert self.name
        assert self.source_directory
        assert self.build_directory

        if not path_exists(self.build_directory):
            create_directory(self.build_directory)

        if not self.cache_directory:
            self.cache_directory = join(self.build_directory, 'obj')
        
        if not path_exists(self.cache_directory):
            create_directory(self.cache_directory)

        if not self.tests_directory:
            _tests_directory_candidate = join(self.root_directory if self.root_directory else self.source_directory, 'test')
            if path_exists(_tests_directory_candidate):
                self.tests_directory = _tests_directory_candidate

        if not self.root_directory:
            self.root_directory = current_directory()

    @property
    def executable_path(self) -> PathLike:
        return join(self.build_directory, f'{self.name}.exe')
    
    @property
    def static_library_path(self) -> PathLike:
        return join(self.build_directory, f'{self.name}.lib')
    
    @property
    def dynamic_library_path(self) -> PathLike:
        return join(self.build_directory, f'{self.name}.dll')
    
    @property
    def debug_information_path(self) -> PathLike:
        return join(self.build_directory, f'{self.name}.pdb')

    def _on_clean(self):
        pass

    def _on_build(self, building: bool):
        pass

    def _on_built(self, elapsed: float):
        pass

    def _on_test(self, running: bool):
        pass

    def _on_test_start(self, test: PathLike):
        pass

    def _on_test_finish(self, test: PathLike, code: int):
        pass 

    def _on_config(self):
        pass

    def add_dependencies(self, *projects: 'Target'):
        for project in projects:
            assert not project.name in self.dependencies
            self.dependencies[project.name] = project

    def clean(self):
        assert self.build_directory and self.cache_directory
        clean_directory(self.cache_directory)
        self._on_clean()

    def build(self, force: bool = False):
        assert self.source_directory and path_exists(self.source_directory)
        if not self.source_files:
            return self._on_build(False)
        
        modified_files = list()

        if force:
            self.clean()
            modified_files = self.source_files # look but don't touch
        else:
            for source_file in self.source_files:
                cached_file = self.cached_object_path(source_file)
                if is_modified_after(join(self.source_directory, source_file), cached_file):
                    modified_files.append(source_file)
        
        modified_files = self.resolve_modified_dependencies(modified_files)
        
        if not modified_files:
            for subtarget in self._subtargets:
                if not subtarget.static_library_path \
                    or is_modified_after(subtarget.static_library_path, self.static_library_path):
                    self._should_relink = True
                    break
            if not self._should_relink:
                return self._on_build(False)
        
        self._on_build(True)

        from time import time
        _start = time()

        for modified_file in modified_files:
            self.compile_source_file(modified_file)
        
        if self.main_translation_unit:
            self.build_executable()
        else:
            self.build_static_library()

        _finish = time()
        self._on_built(_finish - _start)

    def test(self, force: bool = False):
        if not self.tests_directory or not path_exists(self.tests_directory):
            return self._on_test(False)


        unit_tests_sources = list_directory(self.tests_directory, prefix='test_', suffix='.uxx')
        
        unit_tests_to_build = list()
        if force:
            unit_tests_to_build = unit_tests_sources
        else:
            for uxx in unit_tests_sources:
                if is_modified_after(join(self.tests_directory, uxx), self.unit_test_executable(uxx)):
                    unit_tests_to_build.append(uxx)

        for uxx in unit_tests_to_build:
            obj = self.compile_unit_test(uxx)
            self.build_unit_test(uxx, obj)

        unit_test_exes = list_directory(self.build_directory, prefix='test_', suffix='.exe')
        self._on_test(bool(unit_test_exes))

        for exe in unit_test_exes:
            unit_test_exe = join(self.build_directory, exe)
            self._on_test_start(unit_test_exe)
            if not self.run_unit_test_async(unit_test_exe):
                break
        if not self.await_unit_tests():
            raise TestingError()


    @abstractmethod
    def resolve_modified_dependencies(self, modified_files: list[PathLike]) -> list[PathLike]:
        """
            Analyze modified files and sources that depend on them.
            Returns ordered list of all sources files that have to be built this time.
        """
        pass

    @abstractmethod
    def cached_object_path(self, source: PathLike) -> PathLike:
        """
            Returns .obj file path that was/will be produced from given source file.
        """
        pass
    
    @abstractmethod
    def unit_test_object_path(self, uxx: PathLike) -> PathLike:
        """
            Returns .obj file path that was/will be produced from given unit test file.
        """
        pass
    
    @abstractmethod
    def unit_test_executable(self, uxx: PathLike) -> PathLike:
        """
            Returns .exe file path that was/will be produced from given unit test file.
        """
        pass

    @abstractmethod
    def unit_test_debug_information(self, uxx: PathLike) -> PathLike:
        """
            Returns .pdb file path that was/will be produced from given unit test file.
        """
        pass
    
    @abstractmethod
    def run_unit_test(self, exe: PathLike) -> bool:
        """
            Runs unit test and produces errors report if any.
            Returns True on success.
        """
        pass

    @abstractmethod
    def run_unit_test_async(self, exe: PathLike) -> bool:
        """
            Runs unit test asynchronously in the background.
            Returns True on success.
        """
        pass

    @abstractmethod
    def await_unit_tests(self) -> bool:
        """
            Awaits running unit tests if any.
            Returns True if there were no errors.
        """
        pass

    @abstractmethod
    def compile_source_file(self, source: PathLike):
        """
            Calls appropriate compile_* function by source file extension.
            Automatically handles main translation units if any.
        """
        pass

    @abstractmethod
    def compile_header_unit(self, hxx: PathLike):
        pass
    
    @abstractmethod
    def compile_module_interface(self, ixx: PathLike):
        pass
    
    @abstractmethod
    def compile_module_implementation(self, cxx: PathLike):
        pass
    
    @abstractmethod
    def compile_c_translation_unit(self, c: PathLike):
        pass
    
    @abstractmethod
    def compile_cpp_translation_unit(self, cpp: PathLike):
        pass

    @abstractmethod
    def compile_unit_test(self, uxx: PathLike) -> PathLike:
        pass


    @abstractmethod
    def build_unit_test(self, obj: PathLike):
        """
            Produces unit test executable from given .obj file.
        """
        pass

    @abstractmethod
    def build_dynamic_library(self):
        """
            Produces dynamic library from this Project's compiled object files.
        """
        pass

    @abstractmethod
    def build_static_library(self):
        """
            Produces static library from this Project's compiled object files.
        """
        pass

    @abstractmethod
    def build_executable(self):
        """
            Produces executable from this Project's compiled object files if main translation unit was discovered.
        """
        pass
    
    def print_config(self):
        #cts_print(section='project', subsection=self.name, text=f'configuration')
        print()
        print(f'[{cts_header("project")}: {cts_okcyan(self.name)}]')
        cts_print_config_category('directories')
        for dir in ("root directory", "source directory", "tests directory", "build directory", "cache directory"):
            cts_print_config_pair(dir, getattr(self, dir.replace(' ', '_')))

        cts_print_config_category('sources')
        main_file = None
        for source_file in self.source_files:
            if get_file_name(source_file) in ('main.cpp', 'main.c'):
                assert not main_file, "can't have two main translation units in a single project"
                main_file = source_file
            else:
                source_type = None
                match get_file_extension(source_file):
                    case '.hxx':
                        source_type = 'header unit'
                    case '.ixx':
                        source_type = 'module interface'
                    case '.cxx':
                        source_type = 'module implementation'
                    case '.c':
                        source_type = 'C translation unit'
                    case '.cpp':
                        source_type = 'CXX translation unit'
                    case '.uxx':
                        source_type = 'unit test'
                    case _:
                        source_type = 'external'
                cts_print_config_pair(source_type, source_file)
        
        if main_file:
            cts_print_config_pair('main', main_file)
        
        cts_print_config_category('output')
        if self.options.enable_debug_information:
            cts_print_config_pair('debug information', self.debug_information_path)
        
        cts_print_config_pair('static library', self.static_library_path)
        if main_file:
            cts_print_config_pair('executable', self.executable_path)

        self._on_config()

    def on_command(self, args: Namespace):
        for subtarget in self._subtargets:
            if subtarget._is_visited:
                continue
            subtarget.on_command(args)

        self._is_visited = True

        if args.target and not args.target == self.name:
            return

        match args.command:
            case 'build': 
                self.build(force=False)
            case 'rebuild': 
                self.build(force=True)
            case 'clean': 
                self.clean()
            case 'test': 
                self.test()
            case 'config':
                self.print_config()
            case _:
                raise ValueError(f'unsupported command \"{args.command}\"')
            


