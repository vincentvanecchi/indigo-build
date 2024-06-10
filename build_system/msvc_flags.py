from build_system.filesystem import PathLike, get_dot_path, join

class _CFlag:
    CStandard = '/std:c17'
    CXXStandard = '/std:c++latest'
    CXXExceptions = '/EHsc'
    Linkless = '/c'
    
    @staticmethod
    def EnableRTTI(enable: bool = True):
        return '/GR' if enable else '/GR-'
    
    WarningLevelAll = '/Wall'
    @staticmethod
    def WarningLevel(level: int = 4):
        return f'/W{level}'
    TreatWarningsAsErrors = '/WX'

    @staticmethod
    def OBJPath(path: PathLike):
        return f'/Fo{path}'
    @staticmethod
    def PDBPath(path: PathLike):
        return f'/Fd{path}'
    @staticmethod
    def EXEPath(path: PathLike):
        return f'/Fe{path}'
    @staticmethod
    def LIBPath(path: PathLike):
        return f'/Fe{path}'
    @staticmethod
    def DLLPath(path: PathLike):
        return f'/Fe{path}'
    
    EnableDebugInformation = '/Zi'
    LegacyDebugInformation = '/Z7'
    DisableOptimizations = '/Od'
    EnableDebugInformationSynchronization = '/FS'
    
    InlineFunctionsExpansion = '/Ob2'
    WholeProgramOptimization = '/GL'

    @staticmethod
    def IncludeDirectory(dir: PathLike):
        from os import sep
        assert dir
        if dir[-1] != sep:
            dir += sep
        return f'/I{dir}'
    
class _LFlag:
    MachineX64 = '/MACHINE:X64'
    TreatWarningsAsErrors = '/WX'
    EnableDebugInformation = '/DEBUG:FULL'
    LinkTimeCodeGeneration = '/LTCG'
    
    @staticmethod
    def DLLPath(path: PathLike):
        return f'/OUT:{path}'

    @staticmethod
    def LIBPath(path: PathLike):
        return f'/OUT:{path}'

    @staticmethod
    def EXEPath(path: PathLike):
        return f'/OUT:{path}'

class _IfcFlag:
    ExplicitCTranslationUnit = '/Tc'
    ExplicitCXXTranslationUnit = '/Tp'
    ExplicitModuleInterface = '/interface'
    ExplicitModulePartition = '/internalPartition' # not using module partitions (yet?) 'cause they are retarded af
    
    ExportLocalHeaderUnit = '/exportHeader /headerName:quote'
    ExportGlobalHeaderUnit = '/exportHeader /headerName:angle'
    IncludeLocalHeaderUnit = '/headerUnit:quote'
    IncludeGlobalHeaderUnit = '/headerUnit:angle'
    
    IfcSearchDir = '/ifcSearchDir'
    IfcOutput = '/ifcOutput'
    IfcMap = '/ifcMap'

class _Warnings_Mode:
    Flawless = f'{_CFlag.WarningLevelAll} {_CFlag.TreatWarningsAsErrors}'
    Annoying = _CFlag.WarningLevelAll
    Understandable = f'{_CFlag.WarningLevel(3)} {_CFlag.TreatWarningsAsErrors}'
    Noisy = _CFlag.WarningLevel(3)
    Decent = f'{_CFlag.WarningLevel(2)} {_CFlag.TreatWarningsAsErrors}'
    Odd = _CFlag.WarningLevel(2)
    Retarded = f'{_CFlag.WarningLevel(1)} {_CFlag.TreatWarningsAsErrors}'
    Degenerate = _CFlag.WarningLevel(1)
    Off = ''

    @staticmethod
    def _Match(level: int = 5, wx: bool = True) -> str:
        result = ''
        
        if not level:
            return result

        if level < 0:
            raise ValueError(f'unsupported warning level {level}')
        
        if level > 4:
            result = f'{_CFlag.WarningLevelAll}'
        else:
            result = _CFlag.WarningLevel(level)
        
        if result and wx:
            result += f' {_CFlag.TreatWarningsAsErrors}'
        
        return result
    
class _Debug_Mode:
    Debug = f'{_CFlag.EnableDebugInformation} {_CFlag.DisableOptimizations}'
    DebugOptimized = f'{_CFlag.EnableDebugInformation} {_CFlag.InlineFunctionsExpansion} {_CFlag.WholeProgramOptimization}'
    LegacyDebug = f'{_CFlag.LegacyDebugInformation} {_CFlag.DisableOptimizations}'
    LegacyDebugOptimized = f'{_CFlag.LegacyDebugInformation} {_CFlag.InlineFunctionsExpansion} {_CFlag.WholeProgramOptimization}'
    ReleaseOptimized = f'{_CFlag.InlineFunctionsExpansion} {_CFlag.WholeProgramOptimization}'
    Off = ''

    @staticmethod
    def _Match(enable_debug_information: bool, 
        disable_optimizations: bool, 
        legacy_debug_information: bool = False
    ) -> str:
        if enable_debug_information:
            match (legacy_debug_information, disable_optimizations):
                case False, True:
                    return _Debug_Mode.Debug
                case False, False:
                    return _Debug_Mode.DebugOptimized
                case True, True:
                    return _Debug_Mode.LegacyDebug
                case True, False:
                    return _Debug_Mode.LegacyDebugOptimized
        elif disable_optimizations:
            return _Debug_Mode.Off
        else:
            return _Debug_Mode.ReleaseOptimized


def build_msvc_compile_flags(
    standard: str = _CFlag.CXXStandard,
    exceptions: str = _CFlag.CXXExceptions,
    rtti: str = _CFlag.EnableRTTI(True),
    warnings: str = _Warnings_Mode.Flawless,
    debug: str = _Debug_Mode.Debug
) -> list[str]:
    flags = [ _CFlag.Linkless, exceptions, standard, rtti ]
    flags += warnings.split(' ')
    flags += debug.split(' ')
    return flags

def build_msvc_link_flags(
    warnings: bool = True,
    debug: bool = True
) -> list[str]:
    flags = [ _LFlag.MachineX64 ]
    
    if warnings:
        flags.append(_LFlag.TreatWarningsAsErrors)
    
    if debug:
        flags.append(_LFlag.EnableDebugInformation)
    else:
        flags.append(_LFlag.LinkTimeCodeGeneration)
    
    return flags 

def build_msvc_lib_flags(
    warnings: bool = True,
    debug: bool = True
) -> list[str]:
    flags = [ _LFlag.MachineX64 ]

    if warnings:
        flags.append(_LFlag.TreatWarningsAsErrors)
    
    if not debug:
        flags.append(_LFlag.LinkTimeCodeGeneration)

    return flags

class _Module:
    @staticmethod
    def ifc(ixx: PathLike, ifc_search_directory: PathLike) -> PathLike:
        return join(ifc_search_directory, get_dot_path(ixx, add_ext='.ifc', strip_ext=True))
    
    @staticmethod
    def obj(ixx: PathLike, cache_directory: PathLike) -> PathLike:
        return join(cache_directory, get_dot_path(ixx, add_ext='.obj'))

    @staticmethod
    def name(ixx: PathLike) -> str:
        return get_dot_path(ixx, strip_ext=True)

class _Header_Unit:
    @staticmethod
    def ifc(hxx: PathLike, ifc_search_directory: PathLike):
        return join(ifc_search_directory, get_dot_path(hxx, add_ext='.ifc'))

    @staticmethod
    def obj(hxx: PathLike, cache_directory: PathLike) -> PathLike:
        return join(cache_directory, get_dot_path(hxx, add_ext='.obj'))

class _Translation_Unit:
    @staticmethod
    def obj(cpp: PathLike, cache_directory: PathLike) -> PathLike:
        return join(cache_directory, get_dot_path(cpp, add_ext='.obj'))

def produce_module_flags(
    ixx: PathLike,
    source_directory: PathLike,
    ifc_search_directory: PathLike
) -> list[str]:
    ifc = _Module.ifc(ixx, ifc_search_directory)

    flags = []
    
    flags.append(_IfcFlag.ExplicitModuleInterface)
    flags.append(join(source_directory, ixx))

    flags.append(_IfcFlag.IfcOutput)
    flags.append(ifc)
    
    return flags 

def produce_header_unit_flags(
    hxx: PathLike,
    source_directory: PathLike,
    ifc_search_directory: PathLike
) -> list[str]:
    ifc = _Header_Unit.ifc(hxx, ifc_search_directory)

    flags = []
    
    flags.append(_IfcFlag.ExportGlobalHeaderUnit)
    flags.append(hxx)

    flags.append(_IfcFlag.IncludeGlobalHeaderUnit)
    flags.append(f'{hxx}={ifc}')

    flags.append(_IfcFlag.IfcOutput)
    flags.append(ifc)
    
    return flags

def consume_header_unit_flags(
    hxx: PathLike,
    source_directory: PathLike,
    ifc_search_directory: PathLike
) -> list[str]:
    ifc = _Header_Unit.ifc(hxx, ifc_search_directory)

    flags = []
    
    flags.append(_IfcFlag.IncludeGlobalHeaderUnit)
    flags.append(f'{hxx}={ifc}')
    
    return flags

def build_msvc_ifc_flags(
    header_units: set[PathLike],
    source_directory: PathLike,
    ifc_search_directory: PathLike,
    with_ifc_search_dir: bool = True
) -> list[str]:
    flags = []

    for hxx in header_units:
        flags += consume_header_unit_flags(hxx, source_directory, ifc_search_directory)

    if with_ifc_search_dir:
        flags.append(_IfcFlag.IfcSearchDir)
        flags.append(ifc_search_directory)

    return flags

def build_msvc_ixx_flags(
    ixx: PathLike,
    header_units: set[PathLike],
    source_directory: PathLike,
    ifc_search_directory: PathLike,
    cache_directory: PathLike,
) -> list[str]:
    assert ixx.endswith('.ixx')

    flags = build_msvc_ifc_flags(header_units, source_directory, ifc_search_directory)

    flags.append(_IfcFlag.ExplicitModuleInterface)
    flags.append(join(source_directory, ixx))

    flags.append(_IfcFlag.IfcOutput)
    flags.append(_Module.ifc(ixx, ifc_search_directory))

    flags.append(_CFlag.OBJPath(_Module.obj(ixx, cache_directory)))

    return flags

def build_msvc_cxx_flags(
    cxx: PathLike,
    header_units: set[PathLike],
    source_directory: PathLike,
    ifc_search_directory: PathLike,
    cache_directory: PathLike,
) -> list[str]:
    assert cxx.endswith('.cxx')

    flags = build_msvc_ifc_flags(header_units, source_directory, ifc_search_directory)

    flags.append(join(source_directory, cxx))
    flags.append(_CFlag.OBJPath(_Module.obj(cxx, cache_directory)))

    return flags 

def build_msvc_hxx_flags(
    hxx: PathLike,
    header_units: set[PathLike],
    source_directory: PathLike,
    ifc_search_directory: PathLike,
    cache_directory: PathLike,
) -> list[str]:
    assert hxx.endswith('.hxx')

    flags = build_msvc_ifc_flags(header_units, source_directory, ifc_search_directory)

    flags += produce_header_unit_flags(hxx, source_directory, ifc_search_directory)
    flags.append(_CFlag.OBJPath(_Header_Unit.obj(hxx, cache_directory)))

    return flags

def build_msvc_c_flags(
    c: PathLike,
    source_directory: PathLike,
    cache_directory: PathLike,
) -> list[str]:
    assert c.endswith('.c')

    flags = []

    flags.append(_IfcFlag.ExplicitCTranslationUnit)
    flags.append(join(source_directory, c))
    flags.append(_CFlag.OBJPath(_Translation_Unit.obj(c, cache_directory)))

    return flags

def build_msvc_cpp_flags(
    cpp: PathLike,
    header_units: set[PathLike],
    source_directory: PathLike,
    ifc_search_directory: PathLike,
    cache_directory: PathLike,
) -> list[str]:
    assert cpp.endswith('.cpp')

    flags = build_msvc_ifc_flags(
        header_units, 
        source_directory, 
        ifc_search_directory, 
        with_ifc_search_dir = not cpp.endswith('main.cpp')
    )
    
    flags.append(_IfcFlag.ExplicitCXXTranslationUnit)
    flags.append(join(source_directory, cpp))
    flags.append(_CFlag.OBJPath(_Translation_Unit.obj(cpp, cache_directory)))

    return flags

def build_msvc_uxx_flags(
    uxx: PathLike,
    header_units: set[PathLike],
    source_directory: PathLike,
    ifc_search_directory: PathLike,
    cache_directory: PathLike,
) -> list[str]:
    assert uxx.endswith('.uxx')

    flags = build_msvc_ifc_flags(
        header_units, 
        source_directory, 
        ifc_search_directory, 
        with_ifc_search_dir = False
    )

    flags.append(_IfcFlag.ExplicitCXXTranslationUnit)
    flags.append(join(source_directory, uxx))
    flags.append(_CFlag.OBJPath(_Translation_Unit.obj(uxx, cache_directory)))

    return flags

_IFC_MAP_TOML_MODULE_TEMPLATE="""[[module]]
name = '%s'
ifc = '%s'

"""
_IFC_MAP_TOML_HEADER_UNIT_TEMPLATE="""[[header-unit]]
name = ['angle', '%s']
ifc = '%s'

"""

def dump_msvc_ifc_map(
    ifc_map_filename: PathLike,
    ifc_search_directory: PathLike,
    # relative to source_directory
    module_interfaces: set[PathLike], # [ 'my/module.ixx', 'his/super/module.ixx' ]
    header_units: set[PathLike] # [ 'my/hu.hxx', 'his/super/hu.hxx' ]
):
    with open(ifc_map_filename, 'w') as f:
        for hxx in header_units:
            ifc = _Header_Unit.ifc(hxx, ifc_search_directory)
            f.write(_IFC_MAP_TOML_HEADER_UNIT_TEMPLATE % (hxx, join(ifc_search_directory, ifc)))
        
        for ixx in module_interfaces:
            name = get_dot_path(ixx, strip_ext=True)
            ifc = _Module.ifc(ixx, ifc_search_directory)
            f.write(_IFC_MAP_TOML_MODULE_TEMPLATE % (name, join(ifc_search_directory, ifc)))
    