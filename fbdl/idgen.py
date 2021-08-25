"""
Module for generating ids for symbols in deterministic way.
"""

# Do not start from 0.
# Starting from greater value makes it easier to search for ids in packages dump.
current_id = 0xFFF


def generate():
    global current_id

    current_id += 1
    return current_id
