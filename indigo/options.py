from enum import IntEnum
from dataclasses import dataclass, field

from indigo.filesystem import PathLike, path_exists, get_dot_path

class WarningLevel(IntEnum):
    Basic = 1
    Advanced = 2
    Extra = 3
    Max = 4
    All = 5

@dataclass
class Options:
    enable_rtti: bool = True
    enable_debug_information: bool = True
    disable_optimizations: bool = True
    warning_level: WarningLevel = WarningLevel.All
    treat_warnings_as_errors: bool = True

    # whatever corner cases
    # TODO: implement
    explicit_compiler_c_flags: list[str] = field(default_factory=list)
    explicit_compiler_cxx_flags: list[str] = field(default_factory=list)
    explicit_linker_flags: list[str] = field(default_factory=list)
    explicit_include_directories: list[PathLike] = field(default_factory=list)
    explicit_libraries: list[PathLike] = field(default_factory=list)
    explicit_properties: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def _Release(**kwargs) -> 'Options':
        return Options(
            enable_debug_information=True, 
            disable_optimizations=False, 
            treat_warnings_as_errors=False, 
            **kwargs
            )

    @staticmethod
    def TryImport(path: PathLike = 'project_options.py') -> 'Options':
        if path_exists(path):
            import importlib
            try:
                m = importlib.import_module( get_dot_path(path, strip_ext=True) )
                _BUILD_SYSTEM_OPTIONS_ATTRIBUTE = 'PROJECT_OPTIONS'
                if hasattr(m, _BUILD_SYSTEM_OPTIONS_ATTRIBUTE):
                    options = getattr(m, _BUILD_SYSTEM_OPTIONS_ATTRIBUTE)
                    assert isinstance(options, Options)
                    return options
            except ImportError:
                pass
        return Options()