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

from . import expr
from .packages import Packages
from .refdict import RefDict


class ParserBase:
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
                f"Found errors in file '{self.this_file['Path']}':"
                + msg
                + "\nBe careful, error location returned by the tree-sitter might be misleading."
                + "\nEspecially if more than one error is reported."
            )


class Parser(ParserBase):
    def __init__(self, tree, code, this_file, this_pkg, packages):
        self.tree = tree
        self.cursor = tree.walk()
        self.code = code
        self.this_file = this_file
        self.this_pkg = this_pkg
        self.packages = packages


class ParserFromNode(ParserBase):
    def __init__(self, parser, node):
        self.tree = parser.tree
        self.cursor = node.walk()
        self.code = parser.code
        self.this_file = parser.this_file
        self.this_pkg = parser.this_pkg
        self.packages = parser.packages


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
    for pkg_name, pkgs in packages.items():
        for pkg in pkgs:
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
    parser = Parser(tree, code, this_file, this_pkg, packages)
    parser.check_for_errors()

    if parser.goto_first_child() == False:
        return

    while True:
        node_type = parser.node.type
        # Imports have to be handled in different way, as they are not classical symbols.
        if node_type == 'single_import_statement':
            parse_single_import_statement(parser)
        elif node_type == 'comment':
            pass
        else:
            for name, symbol in getattr(this_module, 'parse_' + node_type)(parser):
                symbol['Id'] = hex(id(symbol))
                if name and name in this_file['Symbols']:
                    raise Exception(
                        f"Symbol '{name}' defined at least twice in file '{this_file['Path']}'."
                    )
                elif name:
                    this_file['Symbols'][name] = symbol

                if name and name in this_pkg['Symbols']:
                    raise Exception(
                        f"Symbol '{name}' defined at least twice in package '{this_pkg['Path']}'."
                    )
                elif name:
                    this_pkg['Symbols'][name] = RefDict(symbol)

        if not parser.goto_next_sibling():
            break


def parse_element_anonymous_instantiation(parser):
    symbol = {'Kind': 'Element Anonymous Instantiation'}
    return [(None, None)]


def parse_element_definition(parser):
    name = parser.get_node_string(parser.node.children[1])
    symbol = {
        'Kind': 'Element Definition',
        'Type': parser.get_node_string(parser.node.children[0])
    }

    if parser.node.children[2].type == 'parameter_list':
        symbol['Parameter List'] = parse_parameter_list(ParserFromNode(parser, parser.node.children[2]))

    return [(name, symbol)]


def parse_multi_constant_definition(parser):
    symbols = []

    for i in range(len(parser.node.children) // 3):
        symbol = {'Kind': 'Constant'}
        name = parser.get_node_string(parser.node.children[i * 3 + 1])

        expression = {'String': parser.get_node_string(parser.node.children[i * 3 + 3])}
        symbol['Value'] = expression

        symbols.append((name, symbol))

    return symbols


def parse_parameter_list(parser):
    params = []

    name = None
    for i, node in enumerate(parser.node.children):
        if node.type == ')':
            break

        param = {'Default Value': None}

        if node.type == 'identifier':
            name = parser.get_node_string(node)

        if node.type == 'expression':
            param['Default Value'] = expr.build_expression(parser, node)

        if parser.node.children[i + 1].type in [',', ')']:
            if name in params:
                raise Exception(
                    f"Parameter {name} defined at least twice in parameter list. " +
                    f"File '{parser.this_file['Path']}', line {node.start_point[0] + 1}."
                )

            if name:
                param['Name'] = name
                params.append(param)

    # Check if parameters without default value precede parameters with default value.
    with_defalut = False
    for p in params:
        if with_defalut and p['Default Value'] is None:
            raise Exception(
                "Parameters without default value must precede the ones with default value. " +
                f"File '{parser.this_file['Path']}', line {parser.node.start_point[0] + 1}."
            )

        if p["Default Value"]:
            with_defalut = True

    return tuple(params)


def parse_single_constant_definition(parser):
    symbol = {'Kind': 'Constant'}
    name = parser.get_node_string(parser.node.children[1])

    expression = expr.build_expression(parser, parser.node.children[3])
    symbol['Value'] = expression

    return [(name, symbol)]


def parse_single_import_statement(parser):
    if len(parser.node.children) == 2:
        path_pattern = parser.get_node_string(parser.node.children[1])[1:-1]
        as_ = Packages.get_pkg_name(path_pattern)
    else:
        path_pattern = parser.get_node_string(parser.node.children[2])[1:-1]
        as_ = parser.get_node_string(parser.node.children[1])

    actual_name = path_pattern.split('/')[-1]
    if actual_name.startswith('fbd-'):
        actual_name = actual_name[4:]

    import_ = {
        'Actual Name': actual_name,
        'Package': RefDict(parser.packages.get_ref_to_pkg(path_pattern)),
    }

    if 'Imports' not in parser.this_file:
        parser.this_file['Imports'] = {}

    if as_ in parser.this_file['Imports']:
        raise Exception(
            f"At least two packages imported as '{as_}' in file '{parser.this_file['Path']}'."
        )

    parser.this_file['Imports'][as_] = import_
