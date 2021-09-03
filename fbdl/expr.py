"""
Module for code related with expressions.

All build_* and evaluate_* functions are in alphabetical order.
"""
import logging as log
import sys
from pprint import pprint

this_module = sys.modules[__name__]

from .packages import Packages


class ExprDict(dict):
    def __init__(self, parser, node, symbol):
        super().__init__()
        self.parser = parser
        self.symbol = symbol
        self._value = None

        self['String'] = parser.get_node_string(node)
        self['Kind'] = node.type

    @property
    def value(self):
        # Below cache mechanism had to be removed.
        # This is because it breaks current mechanism
        # of parametrized type instantiation.
        # If already evaluated return.
        # if self._value:
        #    return self._value

        kind = self['Kind']
        log.debug(f"Evaluating {kind}: '{self['String']}'")
        if kind in ['expression', 'parenthesized_expression', 'primary_expression']:
            self.value = self['Child'].value
        else:
            self.value = getattr(self, 'evaluate_' + kind)()

        # If evaluated successfully return.
        if self._value:
            return self._value

    @value.setter
    def value(self, v):
        self._value = v
        self['Value'] = v

    def evaluate_binary_operation(self):
        left = self['Left'].value
        operator = self['Operator']
        right = self['Right'].value

        if left is None or right is None:
            return None

        if operator == '+':
            return left + right
        elif operator == '-':
            return left - right
        elif operator == '*':
            return left * right
        elif operator == '/':
            return left / right
        elif operator == '%':
            return left % right
        elif operator == '**':
            return left ** right
        elif operator == '<<':
            return left << right
        elif operator == '>>':
            return left >> right

    def evaluate_decimal_literal(self):
        return self._value

    def evaluate_false(self):
        return self._value

    def evaluate_identifier(self):
        sym = Packages.get_symbol(self['String'], self.symbol)

        if 'Value' in sym:
            return sym['Value'].value

        return sym.value

    def evaluate_true(self):
        return self._value

    def evaluate_qualified_identifier(self):
        pkg_name = self['Package']
        exception_msg = f"File '{self.parser.this_file['Path']}' doesn't import package '{pkg_name}'."
        if 'Imports' not in self.parser.this_file:
            raise Exception(exception_msg)

        imported_packages = self.parser.this_file['Imports']

        if pkg_name not in imported_packages:
            raise Exception(exception_msg)
        symbols = imported_packages[pkg_name]['Package']['Symbols']

        return symbols[self['Identifier']]['Value'].value

    def evaluate_string_literal(self):
        return self._value

    def evaluate_unary_operation(self):
        operator = self['Operator']
        operand = self['Operand'].value

        if operator == '+':
            return operand
        elif operator == '-':
            return -operand

def build_binary_operation(parser, node, symbol):
    bo = ExprDict(parser, node, symbol)

    left_child = node.children[0]
    right_child = node.children[2]

    bo['Left'] = getattr(this_module, 'build_' + left_child.type)(parser, left_child, symbol)
    bo['Operator'] = parser.get_node_string(node.children[1])
    bo['Right'] = getattr(this_module, 'build_' + right_child.type)(parser, right_child, symbol)

    return bo


def build_binary_literal(parser, node, symbol):
    bl = ExprDict(parser, node, symbol)
    bl.value = int(bl['String'], base=2)

    return bl


def build_decimal_literal(parser, node, symbol):
    dl = ExprDict(parser, node, symbol)
    dl.value = int(dl['String'])

    return dl


def build_expression(parser, node, symbol):
    e = ExprDict(parser, node, symbol)

    child_node = node.children[0]
    e['Child'] = getattr(this_module, 'build_' + child_node.type)(
        parser, child_node, symbol
    )

    return e


def build_false(parser, node, symbol):
    f = ExprDict(parser, node, symbol)
    f.value = False

    return f


def build_hex_literal(parser, node, symbol):
    hl = ExprDict(parser, node, symbol)
    hl.value = int(hl['String'], base=16)

    return hl


def build_identifier(parser, node, symbol):
    i = ExprDict(parser, node, symbol)

    return i


def build_octal_literal(parser, node, symbol):
    ol = ExprDict(parser, node, symbol)
    ol.value = int(ol['String'], base=8)

    return ol


def build_parenthesized_expression(parser, node, symbol):
    pe = ExprDict(parser, node, symbol)

    child_node = node.children[1]
    pe['Child'] = getattr(this_module, 'build_' + child_node.type)(parser, child_node)

    return pe


def build_primary_expression(parser, node, symbol):
    pe = ExprDict(parser, node, symbol)

    child_node = node.children[0]
    pe['Child'] = getattr(this_module, 'build_' + child_node.type)(parser, child_node, symbol)

    return pe


def build_true(parser, node, symbol):
    t = ExprDict(parser, node, symbol)
    t.value = True

    return t


def build_qualified_identifier(parser, node, symbol):
    qi = ExprDict(parser, node, symbol)
    qi['Package'], qi['Identifier'] = qi['String'].split('.')

    if not qi['Identifier'][0].isupper():
        raise Exception(
            f"Symbol '{qi['Identifier']}', imported from package '{qi['Package']}', "
            + f"starts with lower case letter in file "
            + f"'{parser.this_file['Path']}', line {node.start_point[0] + 1}.\nMaybe you "
            + f"meant '{qi['Package'] + '.'+ qi['Identifier'][0].upper() + qi['Identifier'][1:]}'?"
            + f" or '{qi['Identifier']}' instead of {qi['String']}."
        )

    return qi


def build_string_literal(parser, node, symbol):
    sl = ExprDict(parser, node, symbol)
    sl.value = str(sl['String'][1:-1])

    return sl


def build_unary_operation(parser, node, symbol):
    bo = ExprDict(parser, node, symbol)

    operand = node.children[1]

    bo['Operator'] = parser.get_node_string(node.children[0])
    bo['Operand'] = getattr(this_module, 'build_' + operand.type)(parser, operand, symbol)

    return bo
