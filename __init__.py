from indigo import fs, Options, Subproject, Solution
INDIGO_SOLUTION = Solution(
    name = 'indigo',
    directory = fs.get_parent_directory(__file__),
    build_directory = None,
    output_directory = None,
    subprojects = [
        'libargparse',
        'libfswatch',
        'whistleblower'
    ]
)
