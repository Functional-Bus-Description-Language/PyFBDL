"""
Module for code related with expressions.

Some build functions call name.value before returning.
This is a try to evluate the value during parsing.
This makes the post parsing expression evaluations shorter.
"""
import sys
from pprint import pprint

this_module = sys.modules[__name__]


class ExprDict(dict):
    def __init__(self, parser, node):
        super().__init__()
        self.parser = parser
        self._value = None

        self['String'] = parser.get_node_string(node)
        self['Kind'] = node.type

    @property
    def value(self):
        if self._value:
            return self._value

        kind = self['Kind']
        if kind in ['expression', 'primary_expression']:
            self.value = self['Child'].value
        else:
            self.value = getattr(self, 'evaluate_' + kind)()

    @value.setter
    def value(self, v):
        self._value = v
        self['Value'] = v

    def evaluate_binary_operation(self):
        left = self['Left'].value
        operator = self['Operator']
        right = self['Right'].value
        if operator == '+':
            return  left + right
        elif operator == '-':
            return  left - right
        elif operator == '*':
            return  left * right
        elif operator == '/':
            return  left / right
        elif operator == '%':
            return  left % right
        elif operator == '**':
            return  left ** right
        elif operator == '<<':
            return  left << right
        elif operator == '>>':
            return  left >> right

    def evaluate_identifier(self):
        pkg_symbols = self.parser.this_pkg['Symbols']
        if not self['String'] in pkg_symbols:
            raise KeyError(f"Can't find symbol '{self['String']}' in package '{self.parser.this_pkg['Path']}'.")

        return pkg_symbols[self['String']]['Value'].value


def build_binary_operation(parser, node):
    bo = ExprDict(parser, node)

    left_child = node.children[0]
    right_child = node.children[2]

    bo['Left'] = getattr(this_module, 'build_' + left_child.type)(parser, left_child)
    bo['Operator'] = parser.get_node_string(node.children[1])
    bo['Right'] = getattr(this_module, 'build_' + right_child.type)(parser, right_child)

    bo.value

    return bo


def build_decimal_literal(parser, node):
    dl = ExprDict(parser, node)
    dl.value = int(dl['String'])

    return dl


def build_expression(parser, node):
    e = ExprDict(parser, node)

    child_node = node.children[0]
    e['Child'] = getattr(this_module, 'build_' + child_node.type)(parser, child_node)

    e.value

    return e


def build_identifier(parser, node):
    i = ExprDict(parser, node)

    i.value

    return i


def build_primary_expression(parser, node):
    pe = ExprDict(parser, node)

    child_node = node.children[0]
    pe['Child'] = getattr(this_module, 'build_' + child_node.type)(parser, child_node)

    pe.value

    return pe


def build_true(parser, node):
    t = ExprDict(parser, node)
    t.value = True

    return t
