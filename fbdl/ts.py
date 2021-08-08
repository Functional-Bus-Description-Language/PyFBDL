"""
Module for code utilizing tree-sitter.
"""

from tree_sitter import Language, Parser

Language.build_library('build/fbdl.so', ['submodules/tree-sitter-fbdl/'])

FBDLANG = Language('build/fbdl.so', 'fbdl')

parser = Parser()
parser.set_language(FBDLANG)


def parse(packages):
    for package, list_ in packages.items():
        for pkg in list_:
            for f in pkg['Files']:
                f['Description'] = parse_file(f['Handle'])


def parse_file(f):
    """
    Parameters:
    -----------
    f
        File handle.
    """
    description = {}
    code = bytes(f.read(), 'utf8')

    tree = parser.parse(code)

    return description
