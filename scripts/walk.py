#!/bin/python3

# Simple script for walking the tree and printing the nodes.

from tree_sitter import Language, Parser
from pprint import pprint as pp

Language.build_library('build/fbdl.so', ['submodules/tree-sitter-fbdl/'])

FBDLANG = Language('build/fbdl.so', 'fbdl')

parser = Parser()
parser.set_language(FBDLANG)

code = bytes(open('bus.fbd').read(), 'utf8')

tree = parser.parse(code)
cursor = tree.walk()

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

for node in traverse_tree(tree):
    print(node)

c = tree.walk()
c.goto_first_child()
