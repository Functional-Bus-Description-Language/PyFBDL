"""
Module containing code that must or should be run before running the parser.
It includes:
  1. Package discovery.
  2. Files sanity checks.
"""

import logging as log
import os
from pprint import pformat
import sys

from .packages import Packages
from . import idgen


def check_path(path, packages):
    pkg_name = ""
    files = []
    ls_files = os.listdir(path)
    ls_files.sort()
    for f in ls_files:
        file_ = {}
        file_path = os.path.join(path, f)
        if os.path.isfile(file_path) and f.endswith(".fbd"):
            if not pkg_name:
                pkg_name = Packages.get_pkg_name(os.path.basename(path))
            file_['Id'] = idgen.generate()
            file_['Kind'] = 'File'
            file_['Path'] = file_path
            file_['Handle'] = open(file_path, encoding='UTF-8')
            files.append(file_)

    if pkg_name:
        if pkg_name == "main":
            raise Exception(f"Package can not be named 'main': {path}.")

        log.debug(f"Adding package '{pkg_name}', path '{path}'.")

        pkg = {}
        pkg['Path'] = path
        pkg['Files'] = tuple(files)
        pkg['Id'] = idgen.generate()
        pkg['Kind'] = 'Package'
        if pkg_name in packages:
            packages[pkg_name].append(pkg)
        else:
            packages[pkg_name] = [pkg]


def discover_packages():
    paths_to_look = []

    cwd = os.getcwd()
    cwdfbd = os.path.join(cwd, 'fbd')
    if os.path.exists(cwdfbd):
        paths_to_look.append(cwdfbd)

    fbdpath = os.getenv('FBDPATH')
    if fbdpath:
        paths_to_look += fbdpath.split(':')

    if sys.platform == 'linux':
        home = os.getenv('$HOME')
        if home:
            homefbd = os.path.join(home, ".local/lib/fbd")
            if homefbd:
                paths_to_look.append(homefbd)
    else:
        raise Exception("%s platform is not supported, fire an issue." % sys.platform)

    packages = Packages()

    log.info(f"Looking for packages in following paths:\n{pformat(paths_to_look)}")
    for path_to_look in paths_to_look:
        dirs = next(os.walk(path_to_look))[1]
        paths = [os.path.join(path_to_look, d) for d in dirs]

        for p in paths:
            check_path(p, packages)

    log.info(f"Looking for packages in 'fbd-' directories.")
    for p, _, _ in os.walk(cwd):
        if p.startswith(cwdfbd):
            continue

        basename = os.path.basename(p)
        if not basename.startswith('fbd-'):
            continue

        check_path(p, packages)

    for pkg_name, pkgs in packages.items():
        packages[pkg_name] = tuple(pkgs)

    return packages


def get_indent(line):
    indent = 0
    for char in line:
        if char == '\t':
            indent += 1
        elif char == ' ':
            return None
        else:
            break
    return indent


def check_indent(file_):
    current_indent = 0
    for i, line in enumerate(file_):
        # Ignore empty lines.
        if line == '\n':
            continue

        indent = get_indent(line)
        if indent is None:
            raise Exception(
                "Space character ' ' is not allowed in indent.\n"
                + "Use tab character '\\t'.\n"
                + f"File '{file_.name}', line number {i + 1}."
            )

        if indent > current_indent + 1:
            raise Exception(
                f"Multi indent detected.\n"
                + f"File '{file_.name}', line number {i + 1}."
            )
        current_indent = indent


def add_main_file(main, packages):
    """Add main file to the packages dictionary.

    Parameters
    ----------
    main
        Path to the main file.
    packages
        Package dictionary.
    """
    path = os.path.join(os.getcwd(), main)
    packages['main'] = []
    packages['main'].append(
        {
            'Files': [
                {
                    'Id': idgen.generate(),
                    'Kind': 'File',
                    'Path': main,
                    'Handle': open(main, encoding='UTF-8'),
                }
            ],
            'Path': path,
            'Kind': 'Package',
        }
    )
    packages['main'][0]['Id'] = idgen.generate()


def prepare_packages(main):
    """
    Parameters
    ----------
    main
        Path to the main file.

    Returns
    -------
        Package dictionary.
    """
    log.info("Discovering packages.")
    packages = discover_packages()

    add_main_file(main, packages)
    log.debug(f"Found following packages:\n{pformat(packages)}")

    for pkg_name, pkgs in packages.items():
        for pkg in pkgs:
            for f in pkg['Files']:
                check_indent(f['Handle'])

    return packages
