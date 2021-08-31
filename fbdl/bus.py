import sys
from pprint import pprint

from .validation import ValidElements

this_module = sys.modules[__name__]

packages = None

# Bus width must be easy to read globally, as whether access to an element
# is atomic or not depends on the bus width.
DEFAULT_BUS_WIDTH = 32
BUS_WIDTH = None

def set_bus_width():
    global BUS_WIDTH

    properties = packages['main'][0]['Symbols']['main'].get('Properties')
    if not properties:
        BUS_WIDTH = DEFAULT_BUS_WIDTH
        return

    width = properties.get("width")
    if not width:
        BUS_WIDTH = DEFAULT_BUS_WIDTH

def instantiate(after_parse_packages):
    global packages
    packages = after_parse_packages
    set_bus_width()

    resolve_argument_lists()

    bus = {
        'main': instantiate_element(packages['main'][0]['Symbols']['main'])
    }

    return bus


def resolve_argument_list(symbol, parameter_list):
    args = symbol.get('Argument List', ())

    resolved_argument_list = {}

    in_positional_arguments = True
    for i, p in enumerate(parameter_list):
        if in_positional_arguments:
            if i < len(args):
                arg_name = args[i].get('Name')
            else:
                in_positional_arguments = False
                arg_name = None

            if arg_name:
                in_positional_arguments = False
                if arg_name == p['Name']: 
                    resolved_argument_list[p['Name']] = args[i]['Value']
                else:
                    for a in args:
                        if a['Name'] == p['Name']:
                            resolved_argument_list[p['Name']] = a['Value']
                            break
                    else:
                        resolved_argument_list[p['Name']] = p['Default Value']
            else:
                if i < len(args):
                    resolved_argument_list[p['Name']] = args[i]['Value']
                else:
                    resolved_argument_list[p['Name']] = p['Default Value']
        else:
            for a in args:
                if a['Name'] == p['Name']:
                    resolved_argument_list[p['Name']] = a['Value']
                    break
            else:
                resolved_argument_list[p['Name']] = p['Default Value']

    return resolved_argument_list


def resolve_argument_lists_in_symbols(symbols):
    for name, symbol in symbols.items():
        # Base elements can not have parameter list.
        if symbol['Type'] in ValidElements:
            continue

        param_list = packages.get_symbol(symbol['Type'], symbol).get('Parameter List')
        if param_list:
            symbol['Resolved Argument List'] = resolve_argument_list(symbol, param_list)
        if 'Symbols' in symbol:
            resolve_argument_lists_in_symbols(symbol['Symbols'])


def resolve_argument_lists():
    for _, pkgs in packages.items():
        for pkg in pkgs:
            resolve_argument_lists_in_symbols(pkg['Symbols'])


def resolve_to_base_type(symbol):
    type_chain = []

    if symbol['Type'] not in ValidElements.keys():
        type_chain += resolve_to_base_type(packages.get_symbol(symbol['Type'], symbol))

    type_chain.append(symbol)
    return type_chain


def instantiate_type(type, from_type):
    if from_type == None:
        inst = {
            'Base Type': type['Type'],
            'Properties': {},
        }
    else:
        inst = from_type

    properties = type.get('Properties')
    if properties:
        for name, p in properties.items():
            if name in inst['Properties']:
                raise Exception("Can not override properties.")

            inst['Properties'][name] = p['Value'].value

    symbols = type.get('Symbols')
    if symbols:
        for name, symbol in symbols.items():
            if symbol['Kind'] in ['Element Anonymous Instantiation', 'Element Definitive Instantiation']:
                elem = instantiate_element(symbol)
                if elem['Base Type'] not in ValidElements[inst['Base Type']]['Valid Elements']:
                    raise Exception("Invalid Element.")

                list_name = elem['Base Type'].capitalize() + ' List'
                if 'Elements' not in inst:
                    inst['Elements'] = {}
                if name in inst['Elements']:
                    raise Exception("Can not override element.")
                inst['Elements'][name] = instantiate_element(symbol)

    return inst

def instantiate_type_chain(type_chain):
    inst = None
    for t in type_chain:
        inst = instantiate_type(t, inst)

    fill_missing_properties(inst)
    return inst


def instantiate_element(element):
    type_chain = resolve_to_base_type(element)
    type_instance = instantiate_type_chain(type_chain)

    return type_instance
#    return getattr(this_module, 'instantiate_' + element['Type'])(element, packages)


def fill_missing_properties(inst):
    return getattr(this_module, 'fill_missing_properties_' + inst['Base Type'])(inst)

def fill_missing_properties_config(inst):
    if 'width' not in inst['Properties']:
        inst['Properties']['width'] = 32
    if 'atomic' not in inst['Properties']:
        val = False
        if inst['Properties']['width'] > BUS_WIDTH:
            val = True
        inst['Properties']['atomic'] = val

fill_missing_properties_status = fill_missing_properties_config

def fill_missing_properties_param(inst):
    if 'width' not in inst['Properties']:
        inst['Properties']['width'] = 32

def fill_missing_properties_func(inst):
    pass

def fill_missing_properties_bus(inst):
    if 'masters' not in inst['Properties']:
        inst['Properties']['masters'] = 1
