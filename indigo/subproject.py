from dataclasses import dataclass, field

import indigo.filesystem as fs
from indigo.options import Options
from indigo.import_export import import_dataclass, export_dataclass
from indigo.templates import *
from indigo.target import Target

@dataclass
class Subproject:
    name: str
    directory: fs.PathLike = field(default_factory=str)
    source_directory: fs.PathLike = field(default_factory=str)
    tests_directory: fs.PathLike = field(default_factory=str)
    options: Options = field(default_factory=Options)
    dependencies: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    @staticmethod
    def _Import(path: fs.PathLike) -> 'Subproject':
        return import_dataclass(path, 'INDIGO_SUBPROJECT', Subproject)

    def _Normalize_Sources(self):
        # remove duplicates and move main translation unit to the end
        # source files remain in the same order
        sources = [] 
        [ sources.append(s) for s in self.sources if s not in sources ] 

        main_c = None
        main_cpp = None
        try:
            main_c = sources.pop(sources.index('main.c'))
        except ValueError:
            pass

        try:
            main_cpp = sources.pop(sources.index('main.cpp'))
        except ValueError:
            pass

        if main_c:
            sources.append(main_c)
        if main_cpp:
            assert not main_c
            sources.append(main_cpp)
        
        self.sources = sources

    def _Export(self, path: fs.PathLike, force: bool = True):
        self._Normalize_Sources()
        export_dataclass(path, 
            property = 'INDIGO_SUBPROJECT', 
            object = self, 
            imports = 'from indigo import fs, Options, Subproject',
            replaced_directory = self.directory,
            force = force
        )

    @staticmethod
    def import_from(directory: fs.PathLike) -> 'Subproject':
        abs_directory = directory if fs.os.path.isabs(directory) else fs.join(fs.current_directory(), directory)
        __init__py = fs.join(abs_directory, '__init__.py')
        if fs.path_exists(__init__py):
            return Subproject._Import(__init__py)
        raise ImportError(f'could not import subproject from directory \"{directory}\"; no such file: {__init__py}')
        
    def export(self, force: bool = True):
        __init__py = fs.join(self.directory, '__init__.py')
        assert force or not fs.path_exists(__init__py), \
            f'could not export subproject {self.name}: {__init__py} already exists'
        self._Export(__init__py, force=force)
        
    @staticmethod
    def migrate(directory: fs.PathLike,
        source_directory: fs.PathLike = 'src',
        tests_directory: fs.PathLike = 'test',
        include_directory: fs.PathLike = 'include'
    ) -> 'Subproject':
        """
            Attempts to migrate subproject from other build system to indigo.
            Scans f'{directory}/{source_directory}' for source files.
            Generates f'{directory}/__init__.py'.
            
            You might need to adjust the source file extensions accordingly.
                f.e. CMake uses .cppm for module interfaces

            You might need to extract the `int main(int, char**)` function to main.cpp,
                If subproject is expected to produce executable.
            
            ### TODO: support multiple executables in a single project
            You might need to split main functions into sub-subprojects,
                If subproject has multiple executable targets. 
            
            It is **not** intended to work on any legacy project out of the box.
            Instead it produces an indigo subproject file (i.e. __init__.py),
                As a starting point to migration.
        """
        directory = directory if fs.os.path.isabs(directory) else fs.join(fs.current_directory(), directory)
        __init__py = fs.join(directory, '__init__.py')
        if fs.path_exists(__init__py):
            return Subproject._Import(__init__py)
        
        abs_source_directory = fs.join(directory, source_directory)
        abs_tests_directory = fs.join(directory, tests_directory)
        abs_include_directory = fs.join(directory, include_directory)

        assert fs.path_exists(abs_source_directory), f'no such directory: {directory}'
        if not fs.path_exists(abs_tests_directory):
            tests_directory = None
        if not fs.path_exists(abs_include_directory):
            include_directory = None
        
        sources = []
        for dir, _, files in fs.os.walk(abs_source_directory, topdown=False):
            for file in files:
                match fs.get_file_extension(file):
                    case '.hxx':
                        pass
                    case '.ixx':
                        pass
                    case '.cxx':
                        pass
                    case '.c':
                        pass
                    case '.cpp':
                        pass
                    case _:
                        continue
                abs_file = fs.join(dir, file)
                sources.append(fs.relative_directory(abs_file, abs_source_directory))

        assert sources, f'source files were not found in directory \'{abs_source_directory}\''

        options = Options()
        if include_directory:
            options.explicit_include_directories.append(include_directory)

        subproject = Subproject(
            name = fs.get_file_name(directory),
            directory = directory,
            options = options,
            sources = sources,
            dependencies = [],
            source_directory = source_directory,
            tests_directory = tests_directory
        )
        subproject._Export(__init__py)
        return subproject

    @staticmethod
    def generate(path: fs.PathLike,
        with_hxx: bool = True,
        with_ixx: bool = True,
        with_cxx: bool = True,
        with_main: bool = True,
        with_uxx: bool = True
    ) -> 'Subproject':
        """
            Generates subproject directory at @path with the following structure:
            - example/
                - __init__.py 
                - src/
                    - example.hxx
                    - example.ixx
                    - example.cxx
                    - main.cpp
                - test/
                    - test_example.uxx
        """
        abs_path = path if fs.os.path.isabs(path) else fs.join(fs.current_directory(), path)
        fs.create_directory(abs_path)

        src_dir = fs.join(abs_path, 'src')
        fs.create_directory(src_dir)

        tests_dir = fs.join(abs_path, 'test')
        fs.create_directory(tests_dir)

        project_name = fs.get_file_name(path)
        namespace = '::'.join(project_name.split('.'))

        sources = []
        hxx = fs.join(src_dir, f'{project_name}.hxx')
        if with_hxx and not fs.path_exists(hxx):
            with open(hxx, 'w') as f:
                f.write(hxx_template.format(module=project_name, namespace=namespace))
            sources.append(fs.get_file_name(hxx))

        ixx = fs.join(src_dir, f'{project_name}.ixx')
        if with_ixx and not fs.path_exists(ixx):
            with open(ixx, 'w') as f:
                f.write(ixx_template.format(module=project_name, namespace=namespace))
            sources.append(fs.get_file_name(ixx))

        cxx = fs.join(src_dir, f'{project_name}.cxx')
        if with_cxx and not fs.path_exists(cxx):
            with open(cxx, 'w') as f:
                f.write(cxx_template.format(module=project_name, namespace=namespace))
            sources.append(fs.get_file_name(cxx))

        cpp = fs.join(src_dir, 'main.cpp')
        if with_main and not fs.path_exists(cpp):
            with open(cpp, 'w') as f:
                f.write(main_cpp_template.format(module=project_name, namespace=namespace))
            sources.append(fs.get_file_name(cpp))

        uxx = fs.join(tests_dir, f'test_{project_name}.uxx')
        if with_uxx and not fs.path_exists(uxx):
            with open(uxx, 'w') as f:
                f.write(uxx_template.format(module=project_name, namespace=namespace))

        subproject = Subproject(
            name = project_name,
            directory = abs_path,
            options = Options(),
            sources = sources,
            dependencies = [],
            source_directory = fs.relative_directory(src_dir, abs_path),
            tests_directory = fs.relative_directory(tests_dir, abs_path)
        )
        subproject._Export( fs.join(abs_path, '__init__.py') )
        return subproject

    def add_header_unit(self, header_unit: fs.PathLike):
        """
            Expects @header_unit as relative path to the source directory.
            i.e. 'my/header/unit.hxx'
        """
        assert fs.get_file_extension(header_unit) == '.hxx'

        abs_path = None
        if fs.os.path.isabs(header_unit):
            abs_path = header_unit
            header_unit = fs.relative_directory(header_unit, self.directory)
        else:
            abs_path = fs.join(self.directory, self.source_directory, header_unit)
        
        if not fs.path_exists(abs_path):
            with open(abs_path, 'w') as f:
                f.write(hxx_template.format(module=self.name, namespace='::'.join(self.name.split('.'))))
        
        self.sources.append(header_unit)
        self._Export(fs.join(self.directory, '__init__.py'))

    def add_module(self, module_name: str, with_cxx: bool = True):
        """
            Expects @module_name as dot path
            i.e. 'my.sub.module'
            Generates following files in the source directory:
                - 'my/sub/module.ixx'
                - 'my/sub/module.cxx' if @with_cxx is True
            Creates 'my/sub' directory if it does not exist
        """
        path = fs.os.sep.join( module_name.split('.') )
        
        namespace = '::'.join( module_name.split('.') )
        ixx = fs.join(self.directory, self.source_directory, path + '.ixx')

        src_dir = fs.get_parent_directory(ixx)
        fs.create_directory(src_dir)

        if not fs.path_exists(ixx):
            with open(ixx, 'w') as f:
                f.write(ixx_template.format(module=module_name, namespace=namespace))
        
        cxx = fs.join(self.directory, self.source_directory, path + '.cxx')
        if with_cxx and not fs.path_exists(cxx):
            with open(cxx, 'w') as f:
                f.write(cxx_template.format(module=module_name, namespace=namespace))
        
        self.sources.append(path + '.ixx')
        if with_cxx:
            self.sources.append(path + '.cxx')

        self._Export( fs.join(self.directory, '__init__.py') )

    def add_translation_unit(self, translation_unit: fs.PathLike):
        """
            @translation_unit is relative to subproject's source directory
            i.e. "my/hidden/implementation/details.cpp"
        """
        assert fs.get_file_extension(translation_unit) == '.cpp'

        abs_path = fs.join(self.directory, self.source_directory, translation_unit)
        if not fs.path_exists(abs_path):
            fs.create_directory(fs.get_parent_directory(abs_path))
            with open(abs_path, 'w') as f:
                f.write(cpp_template.format(module=self.name, namespace='::'.join(self.name.split('.'))))
        
        self.sources.append(translation_unit)
        self._Export( fs.join(self.directory, '__init__.py') )

    def add_dependency(self, name: str):
        self.dependencies.append(name)
        self.export(True)

