"""
Module for code utilizing tree-sitter.
"""
import sys

this_module = sys.modules[__name__]

from tree_sitter import Language, Parser, TreeCursor

Language.build_library('build/fbdl.so', ['submodules/tree-sitter-fbdl/'])

FBDLANG = Language('build/fbdl.so', 'fbdl')

ts_parser = Parser()
ts_parser.set_language(FBDLANG)

import expr


class Parser():
    def __init__(self, tree, code, this_file, this_pkg, packages):
        self.tree = tree
        self.cursor = tree.walk()
        self.code = code
        self.this_file = this_file
        self.this_pkg = this_pkg
        self.packages = packages

    def __getattr__(self, name):
        return self.cursor.__getattribute__(name)

    def get_node_string(self, node):
        return self.code[node.start_byte : node.end_byte].decode('utf8')

    def check_for_errors(self):
        msg = ""
        for node in traverse_tree(self.tree):
            if node.type == 'ERROR':
                msg += (
                    "\n  Line "
                    + str(node.start_point[0] + 1)
                    + ", character "
                    + str(node.start_point[1] + 1)
                )

        if msg:
            raise Exception(
                f"Found errors in file '{self.file_path}':"
                + msg
                + "\nBe careful, error location returned by the tree-sitter might be misleading."
                + "\nEspecially if more than one error is reported."
            )


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


def parse(packages):
    for package, list_ in packages.items():
        for pkg in list_:
            for f in pkg['Files']:
                parse_file(f, pkg, packages)


def parse_file(this_file, this_pkg, packages):
    """
    Parameters:
    this_file
    this_pkg
    packages
    -----------
    """
    if 'Symbols' not in this_pkg:
        this_pkg['Symbols'] = {}

    this_file['Symbols'] = {}

    this_file['Handle'].seek(0)
    code = bytes(this_file['Handle'].read(), 'utf8')

    tree = ts_parser.parse(code)
    parser = Parser(tree, code, this_file['Path'], this_pkg, packages)
    parser.check_for_errors()

    if parser.goto_first_child() == False:
        return symbols

    while True:
        node_type = parser.node.type
        # Imports have to be handled in different way, as they are not classical symbols.
        if node_type == 'single_import_statement':
            parse_single_import_statement(parser)
        elif node_type == 'ERROR':
            raise Exception(f"ERROR parsing file '{fh.name}'")
        else:
            for name, symbol in getattr(this_module, 'parse_' + node_type)(parser):
                if name and name in this_file['Symbols']:
                    raise Exception(
                        f"Symbol '{name}' defined at least twice in file '{this_file['Path']}'."
                    )
                elif name:
                    this_file['Symbols'][name] = symbol

                if name and name in this_pkg['Symbols']:
                    raise Exception(
                        f"Symbol '{name}' defined at least twice in file '{this_file['Path']}'."
                    )
                elif name:
                    this_pkg['Symbols'][name] = symbol

        if not parser.goto_next_sibling():
            break


def parse_element_anonymous_instantiation(parser):
    symbol = {'Kind': 'Element'}
    return [(None, None)]


def parse_multi_constant_definition(parser):
    symbols = []

    for i in range(len(parser.node.children) // 3):
        symbol = {'Kind': 'Constant'}
        name = parser.get_node_string(parser.node.children[i * 3 + 1])

        expression = {'String': parser.get_node_string(parser.node.children[i * 3 + 3])}
        symbol['Value'] = expression

        symbols.append((name, symbol))

    return symbols


def parse_single_constant_definition(parser):
    symbol = {'Kind': 'Constant'}
    name = parser.get_node_string(parser.node.children[1])

    expression = expr.build_expression(parser, parser.node.children[3])
    symbol['Value'] = expression

    return [(name, symbol)]


def parse_single_import_statement(parser):
    return [(None, None)]
