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
            for f in os.listdir(p):
                if f.endswith(".fbd"):
                    pkg_name = os.path.basename(p)
                    if pkg_name.startswith("fbd-"):
                        pkg_name = pkg_name[4:]
                    if pkg_name in packages:
                        packages[pkg_name].append(p)
                    else:
                        packages[pkg_name] = [p]

    for dirpath, _, _ in os.walk(cwd):
        if dirpath.startswith(cwdfbd):
            continue

        basename = os.path.basename(dirpath)
        if basename.startswith("fbd-"):
            pkg_name = basename[4:]
            if pkg_name in packages:
                packages[pkg_name].append(dirpath)
            else:
                packages[pkg_name] = [dirpath]

    return packages
