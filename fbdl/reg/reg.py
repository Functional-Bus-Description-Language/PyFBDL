"""
Module for packing functionalities into registers and assigning addresses.

Current implemenation is very trivial.
Optinal implemenation is not an easy task.
"""

import math
import random
import time


BUS_WIDTH = None

# Current access address within given block.
# This is global, so currentlu is is not possible to parallelize
# the access address assigning process.
current_addr = 0


def registerify_main(bus):
    global BUS_WIDTH
    global current_addr

    BUS_WIDTH = bus['main']['Properties']['width']

    # 0 and 1 are reserved for _uuid_ and _timestamp_.
    current_addr = 2

    registerify_statuses(bus['main'])

    if 'Elements' not in bus['main']:
        bus['main']['Elements'] = {}

    bus['main']['Elements']['_uuid_'] = {
        'Access Info': ((0, (BUS_WIDTH - 1, 0)),),
        'Base Type': 'status',
        'Properties': {'default': random.randint(0, 2 ** BUS_WIDTH - 1)},
    }
    bus['main']['Elements']['_timestamp_'] = {
        'Access Info': ((1, (BUS_WIDTH - 1, 0)),),
        'Base Type': 'status',
        'Properties': {'default': int(time.time()) & (2 ** BUS_WIDTH - 1)},
    }

    bus['main']['Size'] = current_addr

    return bus


def registerify_statuses(block):
    """This is extremely trivial approach. Even groups are not respected."""
    global current_addr

    elements = block.get('Elements')
    if not elements:
        return None

    for name, elem in elements.items():
        if elem['Base Type'] == 'status':
            access_info = []
            width = elem['Properties']['width']
            for i in range(math.ceil(width / BUS_WIDTH)):
                access_info.append(
                    (
                        current_addr,
                        (
                            BUS_WIDTH - 1
                            if width - i * BUS_WIDTH > BUS_WIDTH
                            else width - 1 - i * BUS_WIDTH,
                            0,
                        ),
                    )
                )
                current_addr += 1

            elem['Access Info'] = tuple(access_info)
