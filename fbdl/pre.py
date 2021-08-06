"""
Module containing code that must or should be run before running the parser.
It includes:
  1. Package discovery.
  2. Package dependency discovery.
  3. Files sanity checks.
"""

import logging as log
import os
from pprint import pformat
import sys


def check_path(path, packages):
    print(path)
    pkg_name = ""
    files = []
    for f in os.listdir(path):
        file_path = os.path.join(path, f)
        if os.path.isfile(file_path) and f.endswith(".fbd"):
            if not pkg_name:
                pkg_name = os.path.basename(path)
                if pkg_name.startswith("fbd-"):
                    pkg_name = pkg_name[4:]
            files.append(file_path)
    if pkg_name:
        dir = {}
        dir["Path"] = path
        dir["Files"] = files
        if pkg_name in packages:
            packages[pkg_name].append(dir)
        else:
            packages[pkg_name] = [dir]


def discover_packages():
    paths_to_look = []

    cwd = os.getcwd()
    cwdfbd = os.path.join(cwd, "fbd")
    if os.path.exists(cwdfbd):
        paths_to_look.append(cwdfbd)

    fbdpath = os.getenv("FBDPATH")
    if fbdpath:
        paths_to_look += fbdpath.split(":")

    if sys.platform == "linux":
        home = os.getenv("$HOME")
        if home:
            homefbd = os.path.join(home, ".local/lib/fbd")
            if homefbd:
                paths_to_look.append(homefbd)
    else:
        raise Exception("%s platform is not supported, fire an issue" % sys.platform)

    packages = {}

    log.debug(f"Looking for packages in following paths:\n{pformat(paths_to_look)}")
    for path_to_look in paths_to_look:
        dirs = next(os.walk(path_to_look))[1]
        paths = [os.path.join(path_to_look, d) for d in dirs]

        for p in paths:
            check_path(p, packages)

    for p, _, _ in os.walk(cwd):
        if p.startswith(cwdfbd):
            continue

        basename = os.path.basename(p)
        if not basename.startswith("fbd-"):
            continue

        check_path(p, packages)

    return packages
