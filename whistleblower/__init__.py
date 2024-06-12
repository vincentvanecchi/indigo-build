from indigo import fs, Options, Subproject
INDIGO_SUBPROJECT = Subproject(
    name = 'whistleblower',
    directory = fs.get_parent_directory(__file__),
    source_directory = 'src',
    tests_directory = 'test',
    options = Options(
        enable_rtti = True,
        enable_debug_information = True,
        disable_optimizations = True,
        warning_level = 5,
        treat_warnings_as_errors = True,
        explicit_compiler_c_flags = [],
        explicit_compiler_cxx_flags = [],
        explicit_linker_flags = [],
        explicit_include_directories = [],
        explicit_libraries = [],
        explicit_properties = {}
    ),
    dependencies = [ 
        'libargparse', 
        'libfswatch' 
    ],
    sources = [
        'main.cpp'
    ]
)
