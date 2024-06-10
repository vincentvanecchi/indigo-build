import msvc

def build_project(target: str) -> msvc.Project:
    root_directory = msvc._Path_Dir(__file__)

    fswatch = msvc.Project(
        name = 'fswatch',
        type = msvc.ProjectType.LIB,
        config = msvc.Config(msvc.ConfigType.Debug),
        source_directory = msvc._Path_Join(root_directory, 'src'),
        build_directory = msvc._Path_Join(root_directory, '.build'),
        tests_directory = msvc._Path_Join(root_directory, 'test')
    )
    fswatch.config.cflags[2] = msvc._CFlag.W2 # TODO: ?

    if target == 'test':
        fswatch.test()
        exit(0)

    if target != 'build':
        fswatch.clean()
    
    fswatch.build([
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
    ])

    return fswatch

__all__ = ['build_project']

if __name__ == '__main__':
    target = msvc._Parse_Target()
    build_project(target)
