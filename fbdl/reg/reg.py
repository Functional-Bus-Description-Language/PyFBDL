"""
Module for packing functionalities into registers and assigning addresses.

Current implemenation is very trivial.
Optinal implemenation is not an easy task.
"""

import math
import logging as log
import math
import random
import time


BUS_WIDTH = None


def registerify(bus):
    global BUS_WIDTH

    if 'main' not in bus:
        log.warn("Registerification. There is no main bus. Returning empty dictionary.")
        return {}

    BUS_WIDTH = bus['main']['Properties']['width']

    # 0 and 1 are reserved for _uuid_ and _timestamp_.
    current_addr = 2

    current_addr = registerify_statuses(bus['main'], current_addr)

    if 'Elements' not in bus['main']:
        bus['main']['Elements'] = {}

    bus['main']['Elements']['_uuid_'] = {
        'Registers': ((0, (BUS_WIDTH - 1, 0)),),
        'Base Type': 'status',
        'Properties': {'default': random.randint(0, 2 ** BUS_WIDTH - 1)},
    }
    bus['main']['Elements']['_timestamp_'] = {
        'Registers': ((1, (BUS_WIDTH - 1, 0)),),
        'Base Type': 'status',
        'Properties': {'default': int(time.time()) & (2 ** BUS_WIDTH - 1)},
    }

    bus['main']['Size'] = current_addr
    #    bus['main']['Aligned Size'] = 2** math.ceil(math.log(current_addr, 2))

    return bus


def registerify_statuses(block, current_addr):
    """This is extremely trivial approach. Even groups are not respected."""
    elements = block.get('Elements')
    if not elements:
        return None

    class ArrayIterator:
        def __init__(self, count, base_addr, width):
            self.count = count
            self.base_addr = base_addr
            self.width = width
            self.item_width = math.ceil(width / BUS_WIDTH)

        def __repr__(self):
            return f"'Base Address': {self.base_addr}, 'Items': {self.count}, 'Item Width': {self.item_width}"

        def __len__(self):
            return self.count

        def __getitem__(self, idx):
            if idx < 0 or self.count <= idx:
                raise IndexError()

            item_addr = self.base_addr + item_width * idx

            registers = []
            for i in self.item_width:
                registers.append(
                    (
                        item_addr,
                        (
                            BUS_WIDTH - 1
                            if self.width - i * BUS_WIDTH > BUS_WIDTH
                            else self.width - 1 - i * BUS_WIDTH,
                            0,
                        ),
                    )
                )
                item_addr += 1

            return registers

    statuses = [elem for _, elem in elements.items() if elem['Base Type'] == 'status']

    for status in statuses:
        registers = []
        width = status['Properties']['width']

        if 'Count' in status:
            status['Registers'] = ArrayIterator(status['Count'], current_addr, width)
            current_addr += math.ceil(width / BUS_WIDTH) * status['Count']
        else:
            for i in range(math.ceil(width / BUS_WIDTH)):
                registers.append(
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

            status['Registers'] = tuple(registers)

    return current_addr
