from os import PathLike
import os
import shutil

def join(*parts: PathLike) -> PathLike:
    """
        f.e. ("a", "b", "c") => "a/b/c" ("a\\b\\c" on Windows)
    """
    return os.path.normpath(os.path.realpath(os.path.join(*parts)))

def get_parent_directory(path: PathLike) -> PathLike:
    """
        f.e. "a/b/c.ext" => "a/b" ("a\\b" on Windows)
    """
    return os.path.normpath(os.path.dirname(os.path.realpath(path)))

def get_file_name(path: PathLike, add_ext: str = "", strip_ext: bool = False) -> PathLike:
    """
        Transforms filesystem paths to file names.
        Optionally transforms file extension.
        f.e. "a/b/c.ext" => "c.ext"
    """
    assert path
    if strip_ext:
        path = os.path.splitext(path)[0]
    if add_ext:
        path += add_ext
    return os.path.basename(path)

def get_file_extension(path: PathLike) -> str:
    """
        "a/b/c.ext" => ".ext"
    """
    return os.path.splitext(path)[1]

def get_dot_path(path: PathLike, add_ext: str = "", strip_ext: bool = False) -> PathLike:
    """
        Transforms filesystem paths to module names.
        Optionally transforms file extension.
        f.e. "a/b/c.ext" => "a.b.c.ext"
    """
    if strip_ext:
        path = os.path.splitext(path)[0]
    if add_ext:
        path += add_ext
    parts = os.path.normpath(path).split(os.sep)
    return '.'.join( (p for p in parts if p) )

def path_exists(path: PathLike) -> bool:
    return os.path.exists(path)

def remove_file(path: PathLike):
    if path_exists(path):
        os.remove(path)

def get_file_line(path: PathLike, line: int) -> str:
    if path_exists(path):
        with open(path, 'r') as f:
            # its retarded, but whatever
            lines = f.readlines()
            if len(lines) > line:
                return lines[line].strip()
    return ''

def current_directory() -> PathLike:
    return os.getcwd()

def relative_directory(path: PathLike, root: PathLike) -> PathLike:
    return os.path.relpath(path, root)

def create_directory(path: PathLike):
    os.makedirs(path, exist_ok=True)

def remove_directory(path: PathLike):
    shutil.rmtree(path, ignore_errors=True)

def clean_directory(path: PathLike):
    if path_exists(path):
        remove_directory(path)
    create_directory(path)

def list_directory(path: PathLike, prefix: str = None, suffix: str = None):
    def cond(p: PathLike) -> bool:
        if not isinstance(p, str):
            p = str(p)
        return (not prefix or p.startswith(prefix)) and (not suffix or p.endswith(suffix))
    
    return [ os.path.normpath(p) for p in os.listdir(path) if cond(p) ]

def is_modified_after(src: PathLike, dst: PathLike) -> bool:
    """
        Checks if @src was modified after @dst.
        ```
            if is_modified_after("main.c", "main.obj"):
                _Rebuild_("main.c")
                ...
        ```
    """
    assert os.path.exists(src), f'no such file or directory: {src}'
    return (not os.path.exists(dst)) or (os.path.getmtime(src) > os.path.getmtime(dst))
