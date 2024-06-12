from typing import ClassVar
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field, is_dataclass

import indigo.filesystem as fs
from indigo.options import Options
from indigo.subproject import Subproject
from indigo.target import Target
from indigo.import_export import import_dataclass, export_dataclass

# from indigo.templates import *
# from indigo.project import Project

@dataclass
class Solution:
    name: str
    directory: fs.PathLike
    build_directory: fs.PathLike = None
    output_directory: fs.PathLike = None
    subprojects: list[str] = field(default_factory=list)
    
    _imported_subprojects: dict[str, Subproject] = field(default_factory=dict, repr=False, hash=False, compare=False, init=False, kw_only=True)
    
    _targets: dict[str, Target] = field(default_factory=dict, repr=False, hash=False, compare=False, init=False, kw_only=True)

    def _Project_source_directory(self, project_name: str, subdirectory: fs.PathLike = 'src'):
        assert self.directory
        return fs.join(self.directory, project_name, subdirectory)
    
    def _Project_build_directory(self, project_name: str):
        assert self.build_directory
        return fs.join(self.build_directory, project_name)

    def _Project_output_directory(self, project_name: str):
        assert self.output_directory
        return fs.join(self.output_directory, project_name)
    
    def add_subproject():
        pass

    @staticmethod
    def _Import(directory: fs.PathLike = fs.current_directory()) -> 'Solution':
        __init__py = fs.join(directory, '__init__.py')
        return import_dataclass(__init__py, 'INDIGO_SOLUTION', Solution)

    def _Export(self, force: bool = True):
        __init__py = fs.join(self.directory, '__init__.py')
        export_dataclass(
            path = __init__py,
            property = 'INDIGO_SOLUTION',
            object = self,
            imports = 'from indigo import fs, Options, Subproject, Solution',
            replaced_directory = self.directory,
            force = force
        )

    def _Import_Subprojects(self):
        if len(self._imported_subprojects) != len(self.subprojects):
            for subproject_name in self.subprojects:
                if not subproject_name in self._imported_subprojects:
                    self._imported_subprojects[subproject_name] = Subproject._Import( fs.join(self.directory, subproject_name) )
        assert len(self._imported_subprojects) == len(self.subprojects)

    def find_subproject(self, name: str) -> Subproject:
        assert name in self.subprojects
        # self._Import_Subprojects()
        if name not in self._imported_subprojects:
            self._imported_subprojects[name] = Subproject._Import( fs.join(self.directory, name) )
        return self._imported_subprojects[name]

    def argument_parser(self) -> ArgumentParser:
        parser = ArgumentParser(self.name, description=f'{self.name} build system')
        
        parser.add_argument('command', type=str, choices=[
            'build', 
            'rebuild', 
            'clean', 
            'test',
            'config'
        ])

        self._Import_Subprojects()

        targets = [ 'all' ]
        
        def scan_targets_recursively(subproject: Subproject):
            if not subproject.name in targets:
                targets.append(subproject.name)
            for dependency_name in subproject.dependencies:
                scan_targets_recursively(self.find_subproject(dependency_name))
        
        for subproject in self._imported_subprojects.values():
            scan_targets_recursively(subproject)

        parser.add_argument('--target', '-T', type=str, choices=targets)

        parser.add_argument('--config', '-C', type=str)

        parser.add_argument('--build_directory', '-B', type=str)
        parser.add_argument('--output_directory', '-O', type=str)
        
        # parser.add_argument('--build-version', '-b', type=str)

        return parser

    
    def target(self, subproject: Subproject, build_directory: fs.PathLike, output_directory: fs.PathLike) -> Target:
        if subproject.name in self._targets:
            return self._targets[subproject.name]
        
        from indigo.msvc_target import MsvcTarget as CXXTarget

        target_build_directory = fs.join(build_directory, subproject.name)
        target_output_directory = fs.join(output_directory, subproject.name),

        subproject._Normalize_Sources()

        cxxtarget = CXXTarget(
            name = subproject.name,
            root_directory = subproject.directory,
            source_directory = fs.join(subproject.directory, subproject.source_directory),
            tests_directory = fs.join(subproject.directory, subproject.tests_directory),
            output_directory = target_output_directory,
            build_directory = target_build_directory,
            cache_directory = fs.join(target_build_directory, 'obj'),
            ifc_search_directory = fs.join(target_build_directory, 'ifc'),
            dependencies = subproject.dependencies,
            source_files = subproject.sources,
            options = subproject.options
        )

        self._targets[subproject.name] = cxxtarget

        for dependency_name in subproject.dependencies:
            dependency = self.find_subproject(dependency_name)
            dependency._Normalize_Sources()
            cxxtarget._subtargets.append(self.target(
                dependency, 
                build_directory, 
                output_directory
            ))
        
        return cxxtarget
    
    def on_command(self, args: Namespace):
        build_directory = self.build_directory 
        output_directory = self.output_directory 
        
        if args.build_directory:
            build_directory = fs.os.path.realpath(args.build_directory)
        if args.output_directory:
            output_directory = fs.os.path.realpath(args.output_directory)
        
        if not build_directory:
            build_directory = fs.join(self.directory, '.build')
        if not output_directory:
            output_directory = fs.join(self.directory, '.output')

        def target_on_command(target_name: str):
            if target_name not in self._targets:
                self.target(
                    self.find_subproject(target_name),
                    build_directory, output_directory
                ).on_command(args)
            else:
                self._targets[target_name].on_command(args)

        if args.target and args.target != 'all':
            target_on_command(args.target)
        else:
            for subproject_name in self.subprojects:
                target_on_command(subproject_name)




# def create_indigo_solution(directory: fs.PathLike = None):
#     if not directory:
#         directory = fs.current_directory()
#     elif not fs.os.path.isabs(directory):
#         directory = fs.join(fs.current_directory(), directory)