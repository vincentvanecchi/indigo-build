from indigo import fs, Project

PROJECT_NAME = 'libfswatch'
PROJECT_DIRECTORY = fs.get_parent_directory(__file__)
PROJECT_DEPENDENCIES = []
PROJECT_SOURCES = [
    'libfswatch/c/windows/realpath.c',
    'libfswatch/c/cevent.cpp',
    'libfswatch/c/libfswatch_log.cpp',
    'libfswatch/c/libfswatch.cpp',
    'libfswatch/c++/windows/win_strings.cpp',
    'libfswatch/c++/windows/win_paths.cpp',
    'libfswatch/c++/windows/win_error_message.cpp',
    'libfswatch/c++/windows/win_handle.cpp',
    'libfswatch/c++/windows/win_directory_change_event.cpp',
    'libfswatch/c++/string/string_utils.cpp',
    'libfswatch/c++/libfswatch_exception.cpp',
    'libfswatch/c++/event.cpp',
    'libfswatch/c++/filter.cpp',
    'libfswatch/c++/path_utils.cpp',
    'libfswatch/c++/windows_monitor.cpp',
    'libfswatch/c++/monitor.cpp',
    'libfswatch/c++/monitor_factory.cpp',

    'fswatch.ixx',
    'fswatch.cxx'
]

def configure_project(*dependencies: Project, build_directory: fs.PathLike = None) -> Project:
    assert not dependencies
    
    project = Project(
        name = PROJECT_NAME, 
        root_directory = PROJECT_DIRECTORY,
        source_directory = fs.join(PROJECT_DIRECTORY, 'src'),
        build_directory = fs.join(build_directory, PROJECT_NAME) if build_directory else fs.join(PROJECT_DIRECTORY, '.build'),
        source_files = PROJECT_SOURCES
    )

    project.options.warning_level = 2
    project.options.treat_warnings_as_errors = False

    return project
