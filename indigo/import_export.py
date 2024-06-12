from importlib.util import spec_from_file_location, module_from_spec
import sys
from dataclasses import is_dataclass

import indigo.filesystem as fs
from indigo.templates import *
from indigo.console_text_styles import *

def format_dataclass(object, replaced_directory: fs.PathLike = None):
    """
        Assumes that dataclass object only contains:
            - builtin types 
            - dataclasses that only contain builtin types
    """
    s = str(object)
    s = s.replace('(', '(\n')
    s = s.replace('=', ' = ')
    s = s.replace(')', '\n)')
    s = s.replace(', ', ',\n')
    s = s.replace('[\'', '[\n\'')
    s = s.replace('\']', '\'\n]')
    s = s.replace('{\'', '{\n\'')
    s = s.replace('\'}', '\'\n}')
    if replaced_directory:
        s = s.replace(replaced_directory.__repr__(), "fs.get_parent_directory(__file__)")

    result = ''
    tab = ''
    for line in s.splitlines():
        if line.strip().endswith('(') \
            or line.strip().endswith(' = [') \
            or line.strip().endswith(' = {'):
            result += f'{tab}{line}\n'
            tab += '    '
            continue
        elif line.strip() in ('),', ')') \
            or line.strip() in ('],', ']') \
            or line.strip() in ('},', '}'):
            tab = tab[:-4]
        
        result += f'{tab}{line}\n'

    return result

def import_dataclass(path: fs.PathLike, property: str, class_type: type = None):
    """
        Imports dataclass from property in .py file.
    """
    assert path and property and class_type
    _ = path
    if fs.os.path.isabs(path):
        path = fs.relative_directory(path, fs.current_directory())

    module_name = None
    if path == '__init__.py':
        module_name = fs.get_file_name(fs.get_parent_directory(path))
    elif fs.get_file_name(path) == '__init__.py':
        module_name = fs.get_dot_path(fs.get_parent_directory(path))
    else:
        module_name = fs.get_dot_path(fs.relative_directory(path, fs.current_directory()), strip_ext=True)
        path = fs.join(path, '__init__.py')
    assert module_name

    rel_path = fs.os.sep.join((".", fs.relative_directory(path, fs.current_directory())))
    import_type = class_type.__name__

    try:
        assert fs.path_exists(path), f'no such file: {path}'
        cts_print(
            section = 'import',
            subsection = import_type,
            subsection_style = cts_warning,
            text = f'{cts_okcyan(module_name)} from file \'{cts_warning(rel_path)}\''
        )
        spec = spec_from_file_location(module_name, path, submodule_search_locations=[fs.current_directory()])
        assert spec
        module = module_from_spec(spec)
        assert module
        sys.modules[spec.name] = module 
        spec.loader.exec_module(module)
        object = getattr(module, property)
        if class_type and not isinstance(object, class_type):
            raise ImportError(f'property {property} actual type is {type(object)} but expected {class_type}')
        return object
    finally:
        if spec and hasattr(sys.modules, spec.name):
            delattr(sys.modules, spec.name)

def export_dataclass(
    path: fs.PathLike, 
    property: str, 
    object, 
    imports: str = '', 
    replaced_directory: fs.PathLike = None,
    force: bool = True
):
    """
        Exports dataclass as property in .py file.
        Warning: Exportable dataclasses can only contain:
            - builtin types 
            - dataclasses that only contain builtin types
    """
    assert path and property and object
    assert is_dataclass(object)
    assert fs.get_file_extension(path) == '.py'
    assert force or not fs.path_exists(path)

    result = format_dataclass(object, replaced_directory=replaced_directory)
    with open(path, 'w') as f:
        f.write( exported_dataclass_template.format(imports=imports, property=property, object=result) )
