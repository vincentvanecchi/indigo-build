from indigo import fs, Project

PROJECT_NAME = 'whistleblower'
PROJECT_DIRECTORY = fs.get_parent_directory(__file__)
PROJECT_DEPENDENCIES = [ 'libargparse', 'libfswatch' ]
PROJECT_SOURCES = [ 'main.cpp' ]

def configure_project(*dependencies: Project, build_directory: fs.PathLike = None) -> Project:
    satisfied_dependencies: dict[str, Project] = dict()

    for dependency in dependencies:
        if dependency.name in PROJECT_DEPENDENCIES:
            satisfied_dependencies[dependency.name] = dependency
        else:
           raise ValueError(f'project {PROJECT_NAME} does not depend on {dependency.name}')

    for dependency_name in PROJECT_DEPENDENCIES:
        if not dependency_name in satisfied_dependencies:
            raise ValueError(f'unsatisfied dependency: {dependency_name}')
    
    project = Project(
        name = PROJECT_NAME, 
        root_directory = PROJECT_DIRECTORY,
        source_directory = fs.join(PROJECT_DIRECTORY, 'src'),
        build_directory = fs.join(build_directory, PROJECT_NAME) if build_directory else fs.join(PROJECT_DIRECTORY, '.build'),
        source_files = PROJECT_SOURCES
    )
    
    project.add_dependencies(*satisfied_dependencies.values())

    return project
