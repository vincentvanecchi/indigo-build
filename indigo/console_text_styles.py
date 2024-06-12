from typing import Iterable, Callable

# https://svn.blender.org/svnroot/bf-blender/trunk/blender/build_files/scons/tools/bcolors.py
class _Console_Text_Styles:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def cts_header(text: str) -> str:
    if not text:
        return ''
    return _Console_Text_Styles.HEADER + text + _Console_Text_Styles.ENDC

def cts_okblue(text: str) -> str:
    if not text:
        return ''
    return _Console_Text_Styles.OKBLUE + text + _Console_Text_Styles.ENDC

def cts_okcyan(text: str) -> str:
    if not text:
        return ''
    return _Console_Text_Styles.OKCYAN + text + _Console_Text_Styles.ENDC

def cts_okgreen(text: str) -> str:
    if not text:
        return ''
    return _Console_Text_Styles.OKGREEN + text + _Console_Text_Styles.ENDC

def cts_warning(text: str) -> str:
    if not text:
        return ''
    return _Console_Text_Styles.WARNING + text + _Console_Text_Styles.ENDC

def cts_fail(text: str) -> str:
    if not text:
        return ''
    return _Console_Text_Styles.FAIL + text + _Console_Text_Styles.ENDC

def cts_bold(text: str) -> str:
    if not text:
        return ''
    return _Console_Text_Styles.BOLD + text + _Console_Text_Styles.ENDC

def cts_underline(text: str) -> str:
    if not text:
        return ''
    return _Console_Text_Styles.UNDERLINE + text + _Console_Text_Styles.ENDC

def cts_break(text: str, style: str = _Console_Text_Styles.BOLD) -> str:
    if not text:
        return ''
    return _Console_Text_Styles.ENDC + text + style

def cts_pass(text: str) -> str:
    return text

def cts_repr(text: str) -> str:
    return text.__repr__()

def cts_print(
    text: str|Iterable[str], 
    section: str = '', 
    subsection: str = None,
    section_style: Callable[[str], str] = cts_header,
    subsection_style: Callable[[str], str] = cts_okcyan,
    text_style: Callable[[str], str] = cts_pass,
    tab: str = '', 
    width: int = 120
):
    prefix = f'{tab}:'
    if section:
        prefix += section_style(section)
    if subsection:
        prefix += f': {subsection_style(subsection)} '
    prefix += '>'

    for textline in (text.split('\n') if isinstance(text, str) else text):
        line = prefix
        current_width = width - len(tab)
        for textword in (textline.split(' ') if isinstance(text, str) else text):
            if not isinstance(textword, str):
                textword = str(textword)

            new_line_length = len(line) + len(textword) + 1
            
            if new_line_length < current_width:
                line += ' '
                line += text_style(textword)
                continue
            
            print(line)
            line = f'{tab}  ` ' + text_style(textword)
        print(line)

def cts_print_info(text: str, section: str = '', tab='  '):
    cts_print(text=text, section=section, tab=tab)

def cts_print_error(text: str, section: str = '', tab: str = '  '):
    cts_print(text=text, section=section, text_style=cts_fail, tab=tab)
    
def cts_print_warning(text: str, section: str = '', tab: str = '  '):
    cts_print(text=text, section=section, text_style=cts_warning, tab=tab)

def cts_print_note(text: str, section: str = '', tab: str = '  '):
    cts_print(text=text, section=section, text_style=cts_underline, tab=tab)

def cts_print_subprocess(result: tuple[str, str, int], tab: str = '  '):
    stdout, stderr, returncode = result
    cts_print(text=stdout, section='out', section_style=cts_okgreen, tab=tab)
    cts_print(text=stderr, section='err', section_style=cts_fail, tab=tab)
    cts_print(text=str(returncode), section='int', section_style=cts_okcyan, tab=tab)


def cts_print_config_category(category: str):
    print(f'  [{cts_warning(category)}]')

def cts_print_config_pair(key: str, value: str):
    print(f"  - {cts_okcyan(key):<30} :: '{value}'")


__all__ = [
    'cts_header',
    'cts_okblue',
    'cts_okcyan',
    'cts_okgreen',
    'cts_warning',
    'cts_fail',
    'cts_bold',
    'cts_underline',
    'cts_break',
    'cts_pass',
    'cts_repr',

    'cts_print',
    'cts_print_info',
    'cts_print_error',
    'cts_print_warning',
    'cts_print_note',
    'cts_print_subprocess',

    'cts_print_config_category',
    'cts_print_config_pair'
]
