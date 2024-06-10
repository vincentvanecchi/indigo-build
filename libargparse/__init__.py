import msvc

def build_project(target: str) -> msvc.Project:
    root_directory = msvc._Path_Dir(__file__)

    argparse = msvc.Project(
        name = 'argparse',
        type = msvc.ProjectType.LIB,
        config = msvc.Config(msvc.ConfigType.Debug),
        source_directory = msvc._Path_Join(root_directory, 'src'),
        build_directory = msvc._Path_Join(root_directory, '.build'),
        tests_directory = msvc._Path_Join(root_directory, 'test')
    )
    argparse.config.cflags[2] = msvc._CFlag.WAll # TODO: ?

    if target == 'test':
        argparse.test()
        exit(0)

    if target != 'build':
        argparse.clean()
    
    argparse.build([
        'argparse.ixx'
    ])

    return argparse

__all__ = ['build_project']

if __name__ == '__main__':
    target = msvc._Parse_Target()
    build_project(target)
