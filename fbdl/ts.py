"""
Module for code utilizing tree-sitter.
"""
import sys

thismodule = sys.modules[__name__]

from tree_sitter import Language, Parser, TreeCursor

Language.build_library('build/fbdl.so', ['submodules/tree-sitter-fbdl/'])

FBDLANG = Language('build/fbdl.so', 'fbdl')

parser = Parser()
parser.set_language(FBDLANG)


class Cursor:
    def __init__(self, tree, code):
        self.code = code
        self.tc = tree.walk()

    def __getattr__(self, name):
        return self.tc.__getattribute__(name)

    def get_node_value(self, node):
        return self.code[node.start_byte : node.end_byte].decode('utf8')


def parse(packages):
    for package, list_ in packages.items():
        for pkg in list_:
            for f in pkg['Files']:
                f['Symbols'] = parse_file(f['Handle'])


def parse_file(f):
    """
    Parameters:
    -----------
    f
        File handle.
    """
    f.seek(0)

    symbols = {}
    code = bytes(f.read(), 'utf8')

    tree = parser.parse(code)
    cursor = Cursor(tree, code)

    if cursor.goto_first_child() == False:
        return symbols

    while True:
        node_type = cursor.node.type
        # Imports have to be handled in different way, as they are not classical symbols.
        if node_type == 'single_import_statement':
            parse_single_import_statement(cursor)
        else:
            name, symbol = getattr(thismodule, 'parse_' + node_type)(cursor)
            if name and name in symbols:
                raise Exception(
                    f"Symbol '{name}' defined at least twice in file 'f.name'."
                )
            elif name:
                symbols[name] = symbol

        if not cursor.goto_next_sibling():
            break

    return symbols


def parse_element_anonymous_instantiation(cursor):
    symbol = {'Kind': 'Element'}
    return None, None


def parse_single_constant_definition(cursor):
    symbol = {'Kind': 'Constant'}
    name = cursor.get_node_value(cursor.node.children[1])

    return name, symbol


def parse_single_import_statement(cursor):
    return None, None
