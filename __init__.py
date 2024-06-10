from indigo import fs, Project, CompilationError

SOLUTION_DIRECTORY = fs.get_parent_directory(__file__)
BUILD_DIRECTORY = fs.join(SOLUTION_DIRECTORY, '.build')

def import_project(project_name, *args, **kwargs) -> Project:
    from importlib import import_module
    project_module = import_module(project_name)
    
    dependencies = []
    for dependency_name in getattr(project_module, 'PROJECT_DEPENDENCIES', []):
        dependencies.append( import_project(dependency_name, *args, **kwargs) )

    assert hasattr(project_module, 'configure_project')
    return getattr(project_module, 'configure_project')(*dependencies, *args, **kwargs)

if __name__ == '__main__':
    project = import_project('whistleblower', build_directory = BUILD_DIRECTORY)
    
    # TODO: indigo.Solution
    args = project.argument_parser().parse_args()
    try:
        for dependency in project.dependencies.values():
            dependency.build_from_args(args)
        project.build_from_args(args)
        exit(0)
    except CompilationError:
        exit(1)
