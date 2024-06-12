from indigo import fs, Options, Subproject
INDIGO_SUBPROJECT = Subproject(
    name = 'libfswatch',
    directory = fs.get_parent_directory(__file__),
    source_directory = 'src',
    tests_directory = 'test',
    options = Options(
        enable_rtti = True,
        enable_debug_information = True,
        disable_optimizations = True,
        warning_level = 2,
        treat_warnings_as_errors = False,
        explicit_compiler_c_flags = [],
        explicit_compiler_cxx_flags = [],
        explicit_linker_flags = [],
        explicit_include_directories = [],
        explicit_libraries = [],
        explicit_properties = {}
    ),
    dependencies = [],
    sources = [
        'libfswatch\\c\\windows\\realpath.c',
        'libfswatch\\c\\cevent.cpp',
        'libfswatch\\c\\libfswatch.cpp',
        'libfswatch\\c\\libfswatch_log.cpp',
        'libfswatch\\c++\\string\\string_utils.cpp',
        'libfswatch\\c++\\windows\\win_directory_change_event.cpp',
        'libfswatch\\c++\\windows\\win_error_message.cpp',
        'libfswatch\\c++\\windows\\win_handle.cpp',
        'libfswatch\\c++\\windows\\win_paths.cpp',
        'libfswatch\\c++\\windows\\win_strings.cpp',
        'libfswatch\\c++\\event.cpp',
        'libfswatch\\c++\\filter.cpp',
        'libfswatch\\c++\\libfswatch_exception.cpp',
        'libfswatch\\c++\\monitor.cpp',
        'libfswatch\\c++\\monitor_factory.cpp',
        'libfswatch\\c++\\path_utils.cpp',
        'libfswatch\\c++\\windows_monitor.cpp',
        'fswatch.ixx',
        'fswatch.cxx'
    ]
)
