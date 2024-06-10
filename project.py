from build_system import Project, CompilationError, fs

if __name__ == '__main__':
    root = fs.get_parent_directory(__file__)

    libargparse = Project(name = 'libargparse', 
        source_directory = fs.join(root, 'libargparse', 'src'),
        tests_directory = fs.join(root, 'libargparse', 'test'),
        build_directory = fs.join(root, '.build', 'libargparse'),
        source_files = ['argparse.ixx', 'main.cpp']
        )
    
    libfswatch = Project(name = 'libfswatch', 
        source_directory = fs.join(root, 'libfswatch', 'src'),
        tests_directory = fs.join(root, 'libfswatch', 'test'),
        build_directory = fs.join(root, '.build', 'libfswatch'),
        source_files = [
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
    
    libfswatch.options.warning_level = 2
    libfswatch.options.treat_warnings_as_errors = False
    
    
    msvcaas = Project(name = 'msvcaas', 
        source_directory = fs.join(root, 'src'),
        tests_directory = fs.join(root, 'test'),
        build_directory = fs.join(root, '.build', 'msvcaas'),
        source_files = ['main.cpp']
        )

    try:
        args = libargparse.argument_parser().parse_args()
        libargparse.build_from_args(args)
        print()
        libfswatch.build_from_args(args)
        print()
        msvcaas.add_dependencies(libargparse, libfswatch)
        msvcaas.build_from_args(args)

        exit(0)
    except CompilationError:
        exit(1)
