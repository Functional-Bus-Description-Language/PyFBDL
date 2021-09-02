import logging as log
from pprint import pprint

from . import args
from .fill import set_bus_width, fill_missing_properties
from ..validation import ValidElements

packages = None

def instantiate(after_parse_packages):
    global packages
    packages = after_parse_packages

    if 'main' not in packages['main'][0]['Symbols']:
        return {}

    set_bus_width(packages)

    args.resolve_argument_lists(packages)

    bus = {'main': instantiate_element(packages['main'][0]['Symbols']['main'])}

    return bus


def resolve_to_base_type(symbol):
    type_chain = []

    if symbol['Type'] not in ValidElements.keys():
        type_chain += resolve_to_base_type(packages.get_symbol(symbol['Type'], symbol))

    type_chain.append(symbol)
    return type_chain


def instantiate_type(type, from_type, resolved_arguments):
    if resolved_arguments is not None:
        type['Resolved Arguments'] = resolved_arguments

    from_type_type = "None"
    if from_type is not None:
        from_type_type = from_type['Previous Type']
    log.debug(f"Instantiating type '{type['Type']}' from type '{from_type_type}'.")

    if from_type == None:
        inst = {'Base Type': type['Type'], 'Properties': {}, 'Previous Type': type['Type']}
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
            if symbol['Kind'] in [
                'Element Anonymous Instantiation',
                'Element Definitive Instantiation',
            ]:
                elem = instantiate_element(symbol)
                if (
                    elem['Base Type']
                    not in ValidElements[inst['Base Type']]['Valid Elements']
                ):
                    raise Exception("Invalid Element.")

                if 'Elements' not in inst:
                    inst['Elements'] = {}
                if name in inst['Elements']:
                    raise Exception("Can not override element.")
                inst['Elements'][name] = instantiate_element(symbol)

    return inst


def instantiate_type_chain(type_chain):
    inst = None
    for i, t in enumerate(type_chain):
        resolved_arguments = None
        if (i + 1) < len(type_chain) and 'Resolved Arguments' in type_chain[i + 1]:
            resolved_arguments = type_chain[i + 1]['Resolved Arguments']
        inst = instantiate_type(t, inst, resolved_arguments)

    inst.pop('Previous Type')
    fill_missing_properties(inst)
    return inst


def instantiate_element(element):
    type_chain = resolve_to_base_type(element)
    type_instance = instantiate_type_chain(type_chain)

    # TODO: Instantiate also own body.

    return type_instance
