"""
Module for packing functionalities into registers and assigning addresses.

Current implemenation is very trivial.
Optinal implemenation is not an easy task.
"""

import logging as log
import math
import time
import zlib

from . import access
from . import iters


BUS_WIDTH = None


def align_to_power_of_2(val):
    return 2 ** math.ceil(math.log(val, 2))


def registerify(bus):
    global BUS_WIDTH

    if 'main' not in bus:
        log.warn("Registerification. There is no main bus. Returning empty dictionary.")
        return {}

    BUS_WIDTH = bus['main']['Properties']['width']

    # addr is current block internal access address, not global address.
    # 0 and 1 are reserved for x_uuid_x and x_timestamp_x.
    addr = 2

    addr = _registerify_functionalities(bus['main'], addr)
    sizes = {'Block Aligned': 0, 'Own': addr, 'Compact': addr}

    if 'Elements' not in bus['main']:
        bus['main']['Elements'] = {}

    for _, element in bus['main']['Elements'].items():
        if element['Base Type'] == 'block':
            elem_sizes = registerify_block(element)
            count = element.get('Count', 1)
            sizes['Compact'] += count * elem_sizes['Compact']
            sizes['Block Aligned'] += count * elem_sizes['Block Aligned']

    bus['main']['Elements']['x_uuid_x'] = {
        'Access': access.single(BUS_WIDTH, 0, BUS_WIDTH),
        'Base Type': 'status',
        'Properties': {
            'default': zlib.adler32(bytes(repr(bus), 'utf-8')) & (2 ** BUS_WIDTH - 1),
            'width': BUS_WIDTH,
        },
    }
    bus['main']['Elements']['x_timestamp_x'] = {
        'Access': access.single(BUS_WIDTH, 1, BUS_WIDTH),
        'Base Type': 'status',
        'Properties': {
            'default': int(time.time()) & (2 ** BUS_WIDTH - 1),
            'width': BUS_WIDTH,
        },
    }

    sizes['Block Aligned'] = align_to_power_of_2(sizes['Own'] + sizes['Block Aligned'])
    bus['main']['Sizes'] = sizes

    # Currently base address property is not yet supported so it starts from 0.
    assign_global_access_addresses(bus['main'], 0)

    return bus


def _registerify_functionalities(element, start_addr):
    """Function grouping functionalities registerification functions."""
    addr = registerify_statuses(element, start_addr)

    return addr


def registerify_statuses(block, addr):
    """This is extremely trivial approach. Even groups are not respected."""
    elements = block.get('Elements')
    if not elements:
        return addr

    statuses = [elem for _, elem in elements.items() if elem['Base Type'] == 'status']

    for status in statuses:
        registers = []
        width = status['Properties']['width']

        if 'Count' in status:
            status['Access'] = access.array(BUS_WIDTH, status['Count'], addr, width)
            addr += status['Access']['Count']
        else:
            status['Access'] = access.single(BUS_WIDTH, addr, width)
            addr += status['Access']['Count']

    return addr


def registerify_block(block):
    # addr is current block internal access address, not global address.
    addr = 0

    addr = _registerify_functionalities(block, addr)
    sizes = {'Block Aligned': 0, 'Own': addr, 'Compact': addr}

    if 'Elements' in block:
        for _, element in block['Elements'].items():
            if element['Base Type'] == 'block':
                elem_sizes = registerify_block(element)
                count = element.get('Count', 1)
                sizes['Compact'] += count * elem_sizes['Compact']
                sizes['Block Aligned'] += count * elem_sizes['Block Aligned']

    sizes['Block Aligned'] = align_to_power_of_2(addr + sizes['Block Aligned'])

    block['Sizes'] = sizes

    return sizes


def assign_global_access_addresses(element, base_addr):
    # Currently there is only Block Align strategy.
    # In the future there may also be Compact and Full Align.
    if 'Count' in element:
        element['Address Space'] = iters.AddressSpace(
            base_addr, element['Count'], element['Sizes']['Block Aligned']
        )
    else:
        element['Address Space'] = (
            (base_addr, base_addr + element['Sizes']['Block Aligned'] - 1),
        )

    subblocks = [
        elem for _, elem in element['Elements'].items() if elem['Base Type'] == 'block'
    ]

    if not subblocks:
        return

    subblocks.sort(key=lambda b: b['Sizes']['Block Aligned'], reverse=True)

    subblock_base_addr = element['Address Space'][-1][1] + 1
    for sb in subblocks:
        count = sb.get('Count', 1)
        subblock_base_addr -= count * sb['Sizes']['Block Aligned']
        assign_global_access_addresses(sb, subblock_base_addr)
