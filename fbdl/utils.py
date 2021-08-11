"""
Module for various utilities not matching to any specific module.
"""
from pprint import pformat
import networkx as nx


def get_pkg_name(path):
    """Get package name based on path or pattern."""
    name = path.split('/')[-1]
    if name.startswith('fbd-'):
        name = name[4:]
    return name


def get_ref_to_pkg(path_pattern, packages):
    """Get reference to the package based on the path pattern."""
    # Main package always consists of single file.
    if path_pattern.endswith('.fbd'):
        return packages['main'][0]

    pkg_name = get_pkg_name(path_pattern)

    if pkg_name not in packages:
        raise Exception(f"Package '{pkg_name}' not found.")

    pkgs = packages[pkg_name]
    if len(pkgs) == 1:
        return packages[pkg_name][0]

    found_pkg = None
    for pkg in pkgs:
        if pkg['Path'].endswith(path_pattern):
            if found_pkg is not None:
                raise Exception(
                    f"At least two packages match path pattern '{path_pattern}'."
                )
            found_pkg = pkg

    if found_pkg is None:
        raise Exception(f"Can't match any package for path pattern '{path_pattern}'.")

    return found_pkg


def build_dependency_graph(packages):
    """Build directed graph for packages dependency."""
    edges = []

    for pkg_name, pkgs in packages.items():
        for pkg in pkgs:
            for f in pkg['Files']:
                if 'Imports' not in f:
                    continue

                for _, imported_pkg in f['Imports'].items():
                    edge = (pkg['Path'], imported_pkg['Package']['Path'])
                    if edge not in edges:
                        edges.append(edge)

    return nx.DiGraph(edges)


def check_packages_dependency_graph(graph):
    """Check dependency graph for cycles."""
    cycles = list(nx.simple_cycles(graph))

    if cycles:
        raise Exception(
            f"Found following package dependency cycles:\n{pformat(cycles)}."
        )


def get_pkgs_in_evaluation_order(graph, packages):
    paths = list(nx.topological_sort(graph))
    paths.reverse()

    return [get_ref_to_pkg(p, packages) for p in paths]
