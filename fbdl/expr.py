"""
Module for code related with expressions.

Some build functions call name.value before returning.
This is a try to evluate the value during parsing.
This makes the post parsing expression evaluations shorter.
"""
import sys

this_module = sys.modules[__name__]


class ExprDict(dict):
    def __init__(self, cursor, node):
        super().__init__()
        self._value = None

        self['String'] = cursor.get_node_string(node)
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
        pass



def build_binary_operation(cursor, node):
    bo = ExprDict(cursor, node)

    left_child = node.children[0]
    right_child = node.children[2]

    bo['Left'] = getattr(this_module, 'build_' + left_child.type)(cursor, left_child)
    bo['Operator'] = cursor.get_node_string(node.children[1])
    bo['Right'] = getattr(this_module, 'build_' + right_child.type)(cursor, right_child)

    bo.value

    return bo


def build_decimal_literal(cursor, node):
    dl = ExprDict(cursor, node)
    dl.value = int(dl['String'])

    return dl


def build_expression(cursor, node):
    e = ExprDict(cursor, node)

    child_node = node.children[0]
    e['Child'] = getattr(this_module, 'build_' + child_node.type)(cursor, child_node)

    e.value

    return e


def build_identifier(cursor, node):
    i = ExprDict(cursor, node)

    i.value

    return i

def build_primary_expression(cursor, node):
    pe = ExprDict(cursor, node)

    child_node = node.children[0]
    pe['Child'] = getattr(this_module, 'build_' + child_node.type)(cursor, child_node)

    pe.value

    return pe


def build_true(cursor, node):
    t = ExprDict(cursor, node)
    t.value = True

    return t
