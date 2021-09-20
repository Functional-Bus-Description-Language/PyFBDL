import logging as log
from pprint import pformat, pprint

from . import args
from .fill import set_bus_width, fill_missing_properties
from .utils import get_file_path
from ..validation import ValidElements

packages = None


def instantiate(after_parse_packages):
    global packages
    packages = after_parse_packages

    if 'main' not in packages['main'][0]['Symbols']:
        return {}

    set_bus_width(packages)

    args.resolve_argument_lists(packages)

    main_bus = None

    for pkg_name, pkgs in packages.items():
        for pkg in pkgs:
            for name, symbol in pkg['Symbols'].items():
                if symbol['Kind'] in [
                    'Element Anonymous Instantiation',
                    'Element Definitive Instantiation',
                    'Element Type Definition',
                ]:
                    # Do not instantiate basic elements.
                    # They are already checked during parsing phase.
                    if name != 'main' and symbol['Type'] in ValidElements.keys():
                        continue

                    if pkg_name == 'main' and name == 'main':
                        main_bus = {'main': instantiate_element(symbol)}
                    else:
                        instantiate_element(symbol)

    return main_bus


def resolve_to_base_type(symbol):
    type_chain = []

    if symbol['Type'] not in ValidElements.keys():
        type_chain += resolve_to_base_type(packages.get_symbol(symbol['Type'], symbol))

    type_chain.append(symbol)
    return type_chain


def check_property(name, prop, elem_type):
    """Check property value type, value and conflicting properties within element."""

    def file_line_msg():
        return f"File '{get_file_path(elem_type)}', line {prop['Line Number']}."

    def wrong_type_msg(excepted_type):
        return (
            f"The '{name}' property must be of type '{excepted_type}'.\n"
            + f"Current type '{type_.__name__}'.\n"
            + file_line_msg()
        )

    def negative_value_msg():
        return (
            f"Negative value ({prop['Value'].value}) of the '{name}' property.\n"
            + file_line_msg()
        )

    value = prop['Value'].value
    type_ = type(value)
    if name in ['atomic', 'once']:
        if type_ != bool:
            raise Exception(wrong_type_msg('bool'))
    elif name == 'doc':
        if type_ != str:
            raise Exception(wrong_type_msg('str'))
    elif name == 'groups':
        if type_ != list:
            raise Exception(wrong_type_msg('list'))
        for group in value:
            if type(group) != str:
                raise Exception(
                    "All values in the 'groups' property value list must be of type 'str'.\n"
                    f"'{group}' is of type '{type(group).__name__}'.\n"
                    + file_line_msg()
                )
    elif name == 'masters':
        if type_ != int:
            raise Exception(wrong_type_msg('int'))
        if value < 1:
            raise Exception(
                f"Value of the 'masters' property must be positive.\n"
                + f"Current value {value}.\n"
                + file_line_msg()
            )
    elif name == 'range':
        if type_ != list:
            raise Exception(wrong_type_msg('list'))
        elif len(value) != 2:
            raise Exception(
                "Length of the 'range' property value list must equal two.\n"
                + f"Current length {len(value)}.\n"
                + file_line_msg()
            )
        elif type(value[0]) != int or type(value[1]) != int:
            raise Exception(
                "Both values in the 'range' property value list must be of type 'int'.\n"
                f"Current types '{type(value[0]).__name__}' and '{type(value[1]).__name__}'.\n"
                + file_line_msg()
            )
        elif value[0] >= value[1]:
            raise Exception(
                "Second value in the 'range' property value list must be greater than the first one.\n"
                + f"First value {value[0]}, second value {value[1]}.\n"
                + file_line_msg()
            )
    elif name == 'width':
        if type_ != int:
            raise Exception(wrong_type_msg('int'))
        if value < 0:
            raise Exception(negative_value_msg())
        if 'range' in elem_type['Properties']:
            raise Exception(
                "Can not set the 'width' property, because the 'range' property is "
                + f"already set in line {elem_type['Properties']['range']['Line Number']}.\n"
                + file_line_msg()
            )


def check_property_conflict(name, prop, elem_type, inst):
    """Check properties conflict between types."""

    def conflict_msg(first, second):
        return (
            f"Can not set the '{first}' property, because the '{second}' "
            + "property is already set in one of the ancestor types.\n"
            + f"File '{get_file_path(elem_type)}', line {prop['Line Number']}."
        )

    if name == 'range':
        if 'width' in inst['Properties']:
            raise Exception(conflict_msg('range', 'width'))
    elif name == 'width':
        if 'range' in inst['Properties']:
            raise Exception(conflict_msg('width', 'range'))


def instantiate_type(type, from_type, resolved_arguments):
    if resolved_arguments is not None:
        type['Resolved Arguments'] = resolved_arguments

    from_type_type = "None"
    if from_type is not None:
        from_type_type = from_type['Previous Type']
    log.debug(f"Instantiating type '{type['Type']}' from type '{from_type_type}'.")

    if from_type == None:
        inst = {
            'Base Type': type['Type'],
            'Properties': {},
            'Previous Type': type['Type'],
        }
    else:
        inst = from_type

    properties = type.get('Properties')
    if properties:
        for name, prop in properties.items():
            if name not in ValidElements[inst['Base Type']]['Valid Properties']:
                raise Exception(
                    f"Property '{name}' is not valid property for element '{type['Name']}' of base type '{inst['Base Type']}'.\n"
                    + f"File '{get_file_path(type)}', line {prop['Line Number']}.\n"
                    + f"Valid properties for '{inst['Base Type']}' are: "
                    + f"{pformat(ValidElements[inst['Base Type']]['Valid Properties'])}."
                )

            check_property(name, prop, type)
            check_property_conflict(name, prop, type, inst)

            if name in inst['Properties']:
                raise Exception(
                    f"{type['Kind']}, can not set property '{name}' in symbol '{type['Name']}'.\n"
                    + "The property is alrady set in one of the ancestor types.\n"
                    + f"File '{get_file_path(type)}', line {prop['Line Number']}."
                )

            inst['Properties'][name] = prop['Value'].value

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
                    raise Exception(
                        f"Element '{name}', of base type '{elem['Base Type']}', can not be "
                        + f"instantiated in element '{type['Name']}' of base type '{inst['Base Type']}'.\n"
                        + f"File '{get_file_path(type)}', line {symbol['Line Number']}.\n"
                        + f"Valid inner element types for '{inst['Base Type']}' are: "
                        + f"{pformat(ValidElements[inst['Base Type']]['Valid Elements'])}."
                    )

                if 'Elements' not in inst:
                    inst['Elements'] = {}

                if name in inst['Elements']:
                    raise Exception(
                        f"Can not instantiate element '{name}'.\n"
                        + "Element with such name is already instantiated in one of the ancestor types.\n"
                        + f"File '{get_file_path(type)}', line {symbol['Line Number']}."
                    )
                inst['Elements'][name] = elem

    return inst


def instantiate_type_chain(type_chain):
    inst = None
    for i, t in enumerate(type_chain):
        resolved_arguments = None
        if (i + 1) < len(type_chain) and 'Resolved Arguments' in type_chain[i + 1]:
            resolved_arguments = type_chain[i + 1]['Resolved Arguments']
        inst = instantiate_type(t, inst, resolved_arguments)

    inst.pop('Previous Type')

    count = type_chain[-1].get('Count')
    if count:
        val = count.value

        if type(val) != int:
            raise Exception(
                "Size of array must be of type 'int'.\n"
                + f"Current type '{type(val).__name__}'.\n"
                + f"File '{get_file_path(type_chain[-1])}', line {type_chain[-1]['Line Number']}."
            )

        if val < 0:
            raise Exception(
                f"Negative size ({val}) of '{type_chain[-1]['Name']}' array.\n"
                f"File '{get_file_path(type_chain[-1])}', line {type_chain[-1]['Line Number']}."
            )

        inst['Count'] = val

    fill_missing_properties(inst)

    return inst


def instantiate_element(element):
    log.debug(f"Instantiating element '{element['Name']}'.")
    type_chain = resolve_to_base_type(element)
    instance = instantiate_type_chain(type_chain)

    return instance
