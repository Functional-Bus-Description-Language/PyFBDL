"""
Module for various utilities not matching to any specific module.
"""

def get_ref_to_package(path_pattern, packages):
    """Get reference to the package based on the path pattern."""
    pkg_name = path_pattern.split('/')[-1]

    if pkg_name.startswith('fbd-'):
        pkg_name = pkg_name[4:]

    if pkg_name not in packages:
        raise Exception(f"Package '{pkg_name}' not found.")

    list_ = packages[pkg_name]
    if len(list_) == 1:
        return packages[pkg_name][0]

    pkg = None
    for p in list_:
        if p['Path'].endswith(path_pattern):
            if pkg is not None:
                raise Exception(f"At least two packages match path pattern '{path_pattern}'.")
            pkg = p

    if pkg is None:
        raise Exception(f"Can't match any package for path pattern '{path_pattern}'.")

    return pkg
