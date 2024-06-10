from indigo import fs, Project

PROJECT_NAME = 'libargparse'
PROJECT_DIRECTORY = fs.get_parent_directory(__file__)
PROJECT_DEPENDENCIES = []
PROJECT_SOURCES = ['argparse.ixx', 'main.cpp']

def configure_project(*dependencies: Project, build_directory: fs.PathLike = None) -> Project:
    assert not dependencies
    
    project = Project(
        name = PROJECT_NAME, 
        root_directory = PROJECT_DIRECTORY,
        source_directory = fs.join(PROJECT_DIRECTORY, 'src'),
        build_directory = fs.join(build_directory, PROJECT_NAME) if build_directory else fs.join(PROJECT_DIRECTORY, '.build'),
        source_files = PROJECT_SOURCES
    )
    
    return project
