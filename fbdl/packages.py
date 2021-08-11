"""
Module for packages dictionary.
"""
import logging as log
from pprint import pformat
import networkx as nx


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

    def evaluate(self):
        """Evaluate expressions within packages."""
        self._build_dependency_graph()
        self._check_dependency_graph()

        pkgs = self._get_pkgs_in_evaluation_order()

        for pkg in pkgs:
            log.info(f"Evaluating package '{pkg['Path']}'")
            # Number of evaluations tries can be arbitraly changed.
            # The required number depends on the nesting of symbols in expressions.
            for i in range(16):
                log.debug(f"Package evaluation iteration number {i}")
                all_evaluated = True

                # TODO: Rethink this as not all symbols are constants with 'Value' key.
                for _, symbol in pkg['Symbols'].items():
                    if symbol['Value'].value == None:
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
