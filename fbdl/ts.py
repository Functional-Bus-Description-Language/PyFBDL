"""
Module for code utilizing tree-sitter.
"""
import sys

this_module = sys.modules[__name__]

from tree_sitter import Language, Parser, TreeCursor

Language.build_library('build/fbdl.so', ['submodules/tree-sitter-fbdl/'])

FBDLANG = Language('build/fbdl.so', 'fbdl')

parser = Parser()
parser.set_language(FBDLANG)

import expr

class Cursor:
    def __init__(self, tree, code, file_path):
        self.tree = tree
        self.tree_cursor = tree.walk()
        self.code = code
        self.file_path = file_path

    def __getattr__(self, name):
        return self.tree_cursor.__getattribute__(name)

    def get_node_string(self, node):
        return self.code[node.start_byte : node.end_byte].decode('utf8')


def traverse_tree(tree):
    cursor = tree.walk()

    reached_root = False
    while reached_root == False:
        yield cursor.node

        if cursor.goto_first_child():
            continue

        if cursor.goto_next_sibling():
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True

            if cursor.goto_next_sibling():
                retracing = False


def check_for_errors(cursor):
    msg = ""
    for node in traverse_tree(cursor.tree):
        if node.type == 'ERROR':
            msg += (
                "\n  Line "
                + str(node.start_point[0] + 1)
                + ", character "
                + str(node.start_point[1] + 1)
            )

    if msg:
        raise Exception(
            f"Found errors in file '{cursor.file_path}':"
            + msg
            + "\nBe careful, error location returned by the tree-sitter might be misleading."
            + "\nEspecially if more than one error is reported."
        )


def parse(packages):
    for package, list_ in packages.items():
        for pkg in list_:
            for f in pkg['Files']:
                f['Symbols'] = parse_file(f['Handle'])


def parse_file(fh):
    """
    Parameters:
    -----------
    fh
        File handle.
    """
    fh.seek(0)

    symbols = {}
    code = bytes(fh.read(), 'utf8')

    tree = parser.parse(code)
    cursor = Cursor(tree, code, fh.name)
    check_for_errors(cursor)

    if cursor.goto_first_child() == False:
        return symbols

    while True:
        node_type = cursor.node.type
        # Imports have to be handled in different way, as they are not classical symbols.
        if node_type == 'single_import_statement':
            parse_single_import_statement(cursor)
        elif node_type == 'ERROR':
            raise Exception(f"ERROR parsing file '{fh.name}'")
        else:
            for name, symbol in getattr(this_module, 'parse_' + node_type)(cursor):
                if name and name in symbols:
                    raise Exception(
                        f"Symbol '{name}' defined at least twice in file 'fh.name'."
                    )
                elif name:
                    symbols[name] = symbol

        if not cursor.goto_next_sibling():
            break

    return symbols


def parse_element_anonymous_instantiation(cursor):
    symbol = {'Kind': 'Element'}
    return [(None, None)]


def parse_multi_constant_definition(cursor):
    symbols = []

    for i in range(len(cursor.node.children) // 3):
        symbol = {'Kind': 'Constant'}
        name = cursor.get_node_string(cursor.node.children[i * 3 + 1])

        expression = {'String': cursor.get_node_string(cursor.node.children[i * 3 + 3])}
        symbol['Expression'] = expression

        symbols.append((name, symbol))

    return symbols


def parse_single_constant_definition(cursor):
    symbol = {'Kind': 'Constant'}
    name = cursor.get_node_string(cursor.node.children[1])

    expression = expr.build_expression(cursor, cursor.node.children[3])
    symbol['Expression'] = expression

    return [(name, symbol)]


def parse_single_import_statement(cursor):
    return [(None, None)]
