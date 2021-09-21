"""
Module for packages dictionary.
"""
import logging as log
from pprint import pformat, pprint
import networkx as nx

from .refdict import RefDict
from .validation import ValidElements


class Packages(dict):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_pkg_name(path):
        """Get package name based on path or pattern."""
        name = path.split('/')[-1]
        if name.startswith('fbd-'):
            name = name[4:]
        return name

    @staticmethod
    def _get_symbol_foreign_pkg(symbol, start_node):
        pkg_name, sym = symbol.split('.')
        node = start_node

        while True:
            if node['Kind'] == 'File':
                break
            else:
                node = node['Parent']

        imports = node.get('Imports')
        if not imports:
            raise Exception(
                f"Reference to the foreign symbol '{symbol}' in file '{node['Path']}', but file does not import any package."
            )

        pkg = None
        for name, dict_ in imports.items():
            if name == pkg_name:
                pkg = dict_['Package']
                break

        if pkg is None:
            raise Exception(
                f"Reference to the foreign symbol '{symbol}' in file '{node['Path']}', but file does not import package '{pkg_name}'."
            )

        if sym not in pkg['Symbols']:
            raise Exception(
                f"Can not get symbol '{symbol}' in file '{node['Path']}'.\n"
                + f"Package 'pkg_name' does not have symbol '{sym}'."
            )

        return pkg['Symbols'][sym]

    @staticmethod
    def get_symbol(symbol, scope):
        """Get reference to the symbol. Start searching from given scope."""
        node = scope

        log.debug(f"Looking for symbol '{symbol}', starting from node '{node['Id']}'.")

        if '.' in symbol:
            return Packages._get_symbol_foreign_pkg(symbol, node)

        while True:
            if node.get('Symbols'):
                if symbol in node['Symbols']:
                    return node['Symbols'][symbol]

            if node.get('Resolved Arguments'):
                if symbol in node['Resolved Arguments']:
                    return node['Resolved Arguments'][symbol]

            if node['Kind'] == 'Package':
                raise Exception(
                    f"Can not find symbol '{symbol}' in package '{node['Path']}' starting from node 'foo'."
                )

            node = node['Parent']

    def get_ref_to_pkg(self, path_pattern):
        """Get reference to the package based on the path pattern."""
        # Main package always consists of single file.
        if path_pattern.endswith('.fbd'):
            return self['main'][0]

        pkg_name = self.get_pkg_name(path_pattern)

        if pkg_name not in self:
            raise Exception(f"Package '{pkg_name}' not found.")

        pkgs = self[pkg_name]
        if len(pkgs) == 1:
            return self[pkg_name][0]

        found_pkg = None
        for pkg in pkgs:
            if pkg['Path'].endswith(path_pattern):
                if found_pkg is not None:
                    raise Exception(
                        f"At least two self match path pattern '{path_pattern}'."
                    )
                found_pkg = pkg

        if found_pkg is None:
            raise Exception(
                f"Can't match any package for path pattern '{path_pattern}'."
            )

        return found_pkg

    def _build_dependency_graph(self):
        """Build directed graph for packages dependency."""
        used_packages = [self['main'][0]]
        edges = []

        for pkg in used_packages:
            for f in pkg['Files']:
                if 'Imports' not in f:
                    continue

                for _, imported_pkg in f['Imports'].items():
                    edge = (pkg['Path'], imported_pkg['Package']['Path'])
                    if edge not in edges:
                        edges.append(edge)

                    if imported_pkg['Package'] not in used_packages:
                        used_packages.append(imported_pkg['Package'])

        log.debug(f"Package dependency graph edges:\n{pformat(edges)}")
        self.dependency_graph = nx.DiGraph(edges)

    def _check_dependency_graph(self):
        """Check dependency graph for cycles."""
        cycles = list(nx.simple_cycles(self.dependency_graph))

        if cycles:
            raise Exception(
                f"Found following package dependency cycles:\n{pformat(cycles)}."
            )

    def _get_pkgs_in_evaluation_order(self):
        paths = list(nx.topological_sort(self.dependency_graph))
        paths.reverse()

        # If path is empty, then there is only the main package.
        if not paths:
            paths.append(self['main'][0]['Path'])

        return [self.get_ref_to_pkg(p) for p in paths]

    def _get_expressions(self, node):
        from .expr import ExprDict

        expressions = []

        type_ = type(node)

        if type == list or type_ == tuple:
            for e in node:
                expressions += self._get_expressions(e)
        elif type_ == RefDict or type_ == dict:
            for _, v in node.items():
                expressions += self._get_expressions(v)
        elif type_ == ExprDict:
            expressions.append(node)

        return expressions

    def evaluate(self):
        """Evaluate expressions within packages."""
        self._build_dependency_graph()
        self._check_dependency_graph()

        pkgs = self._get_pkgs_in_evaluation_order()

        for pkg in pkgs:
            log.info(f"Evaluating package '{pkg['Path']}'")

            # Collect expressions to evaluate.
            expressions = []
            for _, symbol in pkg['Symbols'].items():
                expressions += self._get_expressions(symbol)

            # Number of evaluations tries can be arbitraly changed.
            # The required number depends on the order and nesting of the symbols in expressions.
            for i in range(16):
                log.debug(f"Package evaluation iteration number {i}")
                all_evaluated = True

                for e in expressions:
                    if e.value == None:
                        all_evaluated = False

                if all_evaluated:
                    log.debug(
                        f"Package '{pkg['Path']}' evaluated after {i + 1} iterations."
                    )
                    break
            else:
                raise Exception(
                    f"Can't evaluate package '{pkg['Path']}'. Try to increase the evaluation tries number."
                )

    def _check_instantiations(self):
        invalid_types = list(ValidElements.keys())
        invalid_types.remove('bus')

        for pkg_name, pkgs in self.items():
            for pkg in pkgs:
                for f in pkg['Files']:
                    for name, symbol in f['Symbols'].items():
                        if symbol['Kind'] in [
                            'Element Definitive Instantiation',
                            'Element Anonymous Instantiation',
                        ]:
                            if symbol['Type'] in invalid_types:
                                raise Exception(
                                    f"Element of type '{symbol['Type']}' can not be instantiated at the package level.\n"
                                    + f"File '{f['Path']}', line number {symbol['Line Number']}."
                                )
                            elif symbol['Type'] == 'bus':
                                if name != 'main' or pkg_name != 'main':
                                    raise Exception(
                                        f"Bus instantiation must be named 'main', and must be placed in the 'main' package.\n"
                                        + f"File '{f['Path']}', line number {symbol['Line Number']}."
                                    )

    def check(self):
        self._check_instantiations()
        self._build_dependency_graph()
        self._check_dependency_graph()
