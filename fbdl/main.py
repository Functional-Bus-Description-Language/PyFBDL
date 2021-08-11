import argparse
import logging as log
from pprint import pformat
import sys

import pre
import ts
import utils

VERSION = "0.0.0"


def parse_cmd_line_args():
    parser = argparse.ArgumentParser(
        prog='fbdl',
        description="Functional Bus Description Language compiler front-end written in Python.",
    )

    parser.add_argument('main', help="Path to the main file.")

    parser.add_argument(
        '-l',
        help="Log level. The default is 'info'.",
        choices=['debug', 'info', 'warn'],
        default='info',
    )

    return parser.parse_args()


def main():
    cmd_line_args = parse_cmd_line_args()

    log_levels = {
        'debug': log.DEBUG,
        'info': log.INFO,
        'warn': log.WARN,
    }
    log.basicConfig(
        level=log_levels[cmd_line_args.l],
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    packages = pre.prepare_packages(cmd_line_args.main)

    ts.parse(packages)
    dependency_graph = utils.build_dependency_graph(packages)
    utils.check_packages_dependency_graph(dependency_graph)
    evaluation_order = utils.get_pkgs_in_evaluation_order(dependency_graph, packages)
    ts.evaluate(packages)


if __name__ == "__main__":
    main()
