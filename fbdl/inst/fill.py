"""
Module for code related with filling missing properties.
"""
import sys

this_module = sys.modules[__name__]

# Bus width must be easy to read globally, as whether access to an element
# is atomic or not depends on the bus width.
DEFAULT_WIDTH = 32
BUS_WIDTH = None


def set_bus_width(packages):
    global BUS_WIDTH

    properties = packages['main'][0]['Symbols']['main'].get('Properties')
    if not properties:
        BUS_WIDTH = DEFAULT_WIDTH
        return

    width = properties.get("width")
    if not width:
        BUS_WIDTH = DEFAULT_WIDTH
        return

    BUS_WIDTH = width['Value'].value


def fill_missing_properties(inst):
    return getattr(this_module, 'fill_missing_properties_' + inst['Base Type'])(inst)


def fill_missing_properties_block(inst):
    pass

def fill_missing_properties_config(inst):
    if 'width' not in inst['Properties']:
        inst['Properties']['width'] = DEFAULT_WIDTH
    if 'atomic' not in inst['Properties']:
        val = False
        if inst['Properties']['width'] > BUS_WIDTH:
            val = True
        inst['Properties']['atomic'] = val


fill_missing_properties_status = fill_missing_properties_config


def fill_missing_properties_param(inst):
    if 'width' not in inst['Properties']:
        inst['Properties']['width'] = DEFAULT_WIDTH


def fill_missing_properties_func(inst):
    pass


def fill_missing_properties_bus(inst):
    if 'masters' not in inst['Properties']:
        inst['Properties']['masters'] = 1

    if 'width' not in inst['Properties']:
        inst['Properties']['width'] = BUS_WIDTH


def fill_missing_properties_mask(inst):
    if 'width' not in inst['Properties']:
        inst['Properties']['width'] = DEFAULT_WIDTH
    if 'atomic' not in inst['Properties']:
        val = False
        if inst['Properties']['width'] > BUS_WIDTH:
            val = True
        inst['Properties']['atomic'] = val
