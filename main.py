import argparse
import logging as log
from pprint import pformat
import sys

from fbdl import pre
from fbdl import ts

VERSION = "0.0.0"


def parse_cmd_line_args():
    parser = argparse.ArgumentParser(
        prog='fbdl',
        description="Functional Bus Description Language compiler front-end written in Python.",
    )

    parser.add_argument('main', help="Path to the main file.")

    parser.add_argument('-d', help="Log debug messages.", action='store_true')

    parser.add_argument(
        '-p',
        help="Dump packages dictionary to a file.",
        type=argparse.FileType('w'),
        metavar='file_path',
    )

    return parser.parse_args()


def main():
    cmd_line_args = parse_cmd_line_args()

    log_level = log.INFO
    if cmd_line_args.d:
        log_level = log.DEBUG
    log.basicConfig(
        level=log_level, format="%(levelname)s: %(message)s", stream=sys.stderr
    )

    packages = pre.prepare_packages(cmd_line_args.main)
    ts.parse(packages)
    packages.evaluate()

    if cmd_line_args.p:
        cmd_line_args.p.write(pformat(packages))
        cmd_line_args.p.close()


if __name__ == "__main__":
    main()
