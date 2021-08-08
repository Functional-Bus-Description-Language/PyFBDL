import argparse
import logging as log
import sys

VERSION = "0.0.0"


def parse_cmd_line_args():
    parser = argparse.ArgumentParser(
        prog="fbdl",
        description="Functional Bus Description Language compiler front-end written in Python."
    )

    parser.add_argument("main", help="Path to the main file.")

    parser.add_argument(
        "-l", help="Log level. The default is 'info'.", choices=["debug", "info", "warn", "error"], default="info"
    )

    return parser.parse_args()


def main():
    cmd_line_args = parse_cmd_line_args()

    log_levels = {'debug' : log.DEBUG, 'info' : log.INFO, 'warn' : log.WARN, 'error' : log.ERROR}
    log.basicConfig(
        level=log_levels[cmd_line_args.l], format="%(levelname)s: %(message)s", stream=sys.stderr
    )
    log.info("Hello from fbdl!")


if __name__ == "__main__":
    main()
