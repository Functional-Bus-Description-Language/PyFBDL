"""
Module for code utilizing tree-sitter.
"""
import os

dirname = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-1])

from pprint import pprint, pformat
import sys

this_module = sys.modules[__name__]

from tree_sitter import Language, Parser, TreeCursor

Language.build_library(
    dirname + '/build/fbdl.so', [dirname + '/submodules/tree-sitter-fbdl/']
)
FBDLANG = Language(dirname + '/build/fbdl.so', 'fbdl')

ts_parser = Parser()
ts_parser.set_language(FBDLANG)

from . import expr
from . import idgen
from .packages import Packages
from .refdict import RefDict
from .validation import *


class ParserBase:
    def __getattr__(self, name):
        return self.cursor.__getattribute__(name)

    def get_node_string(self, node):
        return self.code[node.start_byte : node.end_byte].decode('utf8')

    def file_line_msg(self, node):
        return f"File '{self.this_file['Path']}', line {node.start_point[0] + 1}."

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
                f['Parent'] = RefDict(pkg)
                parse_file(f, pkg, packages)

    packages.check()


def parse_file(this_file, this_pkg, packages):
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
            for symbol in getattr(this_module, 'parse_' + node_type)(parser):
                if symbol['Name'] in this_file['Symbols']:
                    raise Exception(
                        f"Symbol '{symbol['Name']}' defined at least twice in file '{this_file['Path']}'.\n"
                        + f"First occurrence line {this_file['Symbols'][symbol['Name']]['Line Number']}, second line {symbol['Line Number']}."
                    )
                symbol['Parent'] = RefDict(this_file)
                this_file['Symbols'][symbol['Name']] = symbol

                if symbol['Name'] in this_pkg['Symbols']:
                    raise Exception(
                        f"Symbol '{symbol['Name']}' defined at least twice in package '{this_pkg['Path']}'."
                    )

                this_pkg['Symbols'][symbol['Name']] = RefDict(symbol)

        if not parser.goto_next_sibling():
            break


def parse_argument_list(parser, symbol):
    args = []

    names = []
    name = None
    for i, node in enumerate(parser.node.children):
        if node.type in ['(', ',', '=', ')']:
            continue

        if node.type == 'identifier':
            name = parser.get_node_string(node)
        else:
            val = expr.build_expression(parser, node, symbol)

        if parser.node.children[i + 1].type in [',', ')']:
            if name and name in names:
                raise Exception(
                    f"Argument '{name}' assigned at least twice in argument list.\n"
                    + parser.file_line_msg(node)
                )

            arg = {'Value': val}
            if name:
                names.append(name)
                arg['Name'] = name
                name = None

            args.append(arg)

    # Check if arguments without name precede arguments with name.
    with_name = False
    for a in args:
        if with_name and 'Name' not in a:
            raise Exception(
                "Arguments without name must precede the ones with name.\n"
                + parser.file_line_msg(node)
            )

        if 'Name' in a:
            with_name = True

    return tuple(args)


def parse_element_anonymous_instantiation(parser):
    symbol = {
        'Id': idgen.generate(),
        'Kind': 'Element Anonymous Instantiation',
        'Line Number': parser.node.start_point[0] + 1,
        'Name': parser.get_node_string(parser.node.children[0]),
    }

    if parser.node.children[1].type == '[':
        symbol['Count'] = expr.build_expression(parser, parser.node.children[2], symbol)

    if parser.node.children[1].type == 'element_type':
        symbol['Type'] = parser.get_node_string(parser.node.children[1])
    else:
        symbol['Type'] = parser.get_node_string(parser.node.children[4])

    if parser.node.children[-1].type == 'element_body':
        properties, symbols = parse_element_body(
            ParserFromNode(parser, parser.node.children[-1]), symbol
        )
        if properties:
            symbol['Properties'] = properties
        if symbols:
            for _, sym in symbols.items():
                sym['Parent'] = RefDict(symbol)
            symbol['Symbols'] = symbols

    if symbol['Name'] in ValidElements.keys():
        raise Exception(
            f"Invalid instance name '{symbol['Name']}'.\n"
            + "Element instance can not have the same name as base type.\n"
            + parser.file_line_msg(parser.node)
        )
    return [symbol]


def parse_element_body(parser, symbol):
    properties = {}
    symbols = {}

    for node in parser.node.children:
        if node.type == 'property_assignment':
            name, value, line_number = parse_propery_assignment(
                ParserFromNode(parser, node), symbol
            )

            if name in properties:
                raise Exception(
                    f"Property '{name}' assigned at least twice within the same element body.\n"
                    + parser.file_line_msg(node)
                )

            properties[name] = {'Value': value, 'Line Number': line_number}
        elif node.type in [
            'element_type_definition',
            'element_anonymous_instantiation',
            'element_definitive_instantiation',
            'single_constant_definition',
            'multi_constant_definition',
        ]:
            for symbol in getattr(this_module, 'parse_' + node.type)(
                ParserFromNode(parser, node)
            ):
                if symbol['Name'] in symbols:
                    raise Exception(
                        f"Symbol '{symbol['Name']}' defined at least twice within the same element body.\n"
                        + f"File '{parser.this_file['Path']}'.\n"
                        + f"First occurrence line {symbols[symbol['Name']]['Line Number']}, second line {symbol['Line Number']}."
                    )
                elif symbol['Name']:
                    symbols[symbol['Name']] = symbol

    return properties, symbols


def parse_element_type_definition(parser):
    symbol = {
        'Id': idgen.generate(),
        'Kind': 'Element Type Definition',
        'Line Number': parser.node.start_point[0] + 1,
        'Name': parser.get_node_string(parser.node.children[1]),
    }

    type_node = None
    for node in parser.node.children[2:]:
        if node.type == 'parameter_list':
            symbol['Parameters'] = parse_parameter_list(
                ParserFromNode(parser, node), symbol
            )
        elif node.type == 'identifier':
            symbol['Type'] = parser.get_node_string(node)
            type_node = node
        elif node.type == 'qualified_identifier':
            qi = parser.get_node_string(node)
            pkg, id = qi.split('.')
            if not id[0].isupper():
                raise Exception(
                    f"Symbol '{id}', imported from package '{pkg}', starts with lower case letter.\n"
                    + f"Maybe you meant '{pkg + '.'+ id[0].upper() + id[1:]}' or '{id}' instead of '{qi}'?\n"
                    + parser.file_line_msg(parser.node)
                )
            symbol['Type'] = qi
            type_node = node
        elif node.type == 'argument_list':
            symbol['Arguments'] = parse_argument_list(
                ParserFromNode(parser, node), symbol
            )
        elif node.type == 'element_body':
            properties, symbols = parse_element_body(
                ParserFromNode(parser, parser.node.children[-1]), symbol
            )
            if properties:
                symbol['Properties'] = properties
            if symbols:
                for _, sym in symbols.items():
                    sym['Parent'] = RefDict(symbol)
                symbol['Symbols'] = symbols

    if 'Arguments' in symbol:
        if symbol['Type'] in ValidElements.keys():
            raise Exception(
                f"Base type '{symbol['Type']}' does not accept argument list.\n"
                + parser.file_line_msg(type_node)
            )

    return [symbol]


def parse_element_definitive_instantiation(parser):
    symbol = {
        'Id': idgen.generate(),
        'Kind': 'Element Definitive Instantiation',
        'Line Number': parser.node.start_point[0] + 1,
        'Name': parser.get_node_string(parser.node.children[0]),
    }

    if parser.node.children[1].type == '[':
        symbol['Count'] = expr.build_expression(parser, parser.node.children[2], symbol)

    if parser.node.children[1].type in ['identifier', 'qualified_identifier']:
        symbol['Type'] = parser.get_node_string(parser.node.children[1])
    else:
        symbol['Type'] = parser.get_node_string(parser.node.children[4])
    if '.' in symbol['Type']:
        pkg, id = symbol['Type'].split('.')
        if not id[0].isupper():
            raise Exception(
                f"Symbol '{id}', imported from package '{pkg}', starts with lower case letter.\n"
                + f"Maybe you meant '{pkg + '.'+ id[0].upper() + id[1:]}' or '{id}' instead of '{symbol['Type']}'?\n"
                + parser.file_line_msg(parser.node)
            )

    if parser.node.children[-2].type == 'argument_list':
        symbol['Arguments'] = parse_argument_list(
            ParserFromNode(parser, parser.node.children[-2]), symbol
        )

    if parser.node.children[-1].type == 'argument_list':
        symbol['Arguments'] = parse_argument_list(
            ParserFromNode(parser, parser.node.children[-1]), symbol
        )

    if parser.node.children[-1].type == 'element_body':
        properties, symbols = parse_element_body(
            ParserFromNode(parser, parser.node.children[-1]), symbol
        )
        if properties:
            symbol['Properties'] = properties
        if symbols:
            for _, sym in symbols.items():
                sym['Parent'] = RefDict(symbol)
            symbol['Symbols'] = symbols

    if symbol['Name'] in ValidElements.keys():
        raise Exception(
            f"Invalid instance name '{symbol['Name']}'.\n"
            + "Element instance can not have the same name as base type.\n"
            + parser.file_line_msg(parser.node)
        )

    return [symbol]


def parse_multi_constant_definition(parser):
    symbols = []

    for i in range(len(parser.node.children) // 3):
        symbol = {
            'Id': idgen.generate(),
            'Kind': 'Constant',
            'Line Number': parser.node.children[i * 3 + 1].start_point[0] + 1,
            'Name': parser.get_node_string(parser.node.children[i * 3 + 1]),
        }

        expression = expr.build_expression(
            parser, parser.node.children[i * 3 + 3], symbol
        )
        symbol['Value'] = expression

        symbols.append(symbol)

    return symbols


def parse_parameter_list(parser, symbol):
    params = []

    name = None
    for i, node in enumerate(parser.node.children):
        if node.type in ['(', '=', ',', ')']:
            continue

        default_value = None

        if node.type == 'identifier':
            name = parser.get_node_string(node)
        else:
            default_value = expr.build_expression(parser, node, symbol)

        if parser.node.children[i + 1].type in [',', ')']:
            for p in params:
                if name == p['Name']:
                    raise Exception(
                        f"Parameter '{name}' defined at least twice in parameter list.\n"
                        + parser.file_line_msg(node)
                    )

            param = {'Name': name}
            if default_value:
                param['Default Value'] = default_value
            params.append(param)

    # Check if parameters without default value precede parameters with default value.
    with_default = False
    for p in params:
        if with_default and p.get('Default Value') is None:
            raise Exception(
                "Parameters without default value must precede the ones with default value.\n"
                + parser.file_line_msg(node)
            )

        if p.get('Default Value'):
            with_default = True

    return tuple(params)


def parse_propery_assignment(parser, symbol):
    name = parser.get_node_string(parser.node.children[0])
    value = expr.build_expression(parser, parser.node.children[2], symbol)
    line_number = parser.node.start_point[0] + 1

    return name, value, line_number


def parse_single_constant_definition(parser):
    symbol = {
        'Id': idgen.generate(),
        'Kind': 'Constant',
        'Line Number': parser.node.children[1].start_point[0] + 1,
        'Name': parser.get_node_string(parser.node.children[1]),
    }

    expression = expr.build_expression(parser, parser.node.children[3], symbol)
    symbol['Value'] = expression

    return [symbol]


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
