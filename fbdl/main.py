import logging as log
import sys

VERSION = "0.0.0"


def main():
    log.basicConfig(
        level=log.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr
    )
    log.info("Hello from fbdl!")


if __name__ == "__main__":
    main()
