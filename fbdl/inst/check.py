"""
Module for various checking functions.
"""

from .utils import get_file_path


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
        for i, group in enumerate(value[:-1]):
            if group in value[i + 1 :]:
                raise Exception(
                    "Duplicate in the 'groups' property.\n"
                    f"Duplicated value \"{group}\".\n" + file_line_msg()
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


def _check_groups(inst, type):
    elems_with_groups = []

    elements = inst.get('Elements')
    if not elements:
        return None

    for name, elem in elements.items():
        if elem['Base Type'] == type:
            props = elem.get('Properties')
            if props and 'groups' in props:
                elems_with_groups.append((name, props['groups']))

    for i, status in enumerate(elems_with_groups[:-1]):
        name, groups = status
        for status2 in elems_with_groups[i + 1 :]:
            name2, groups2 = status2
            indexes = []
            for j, group in enumerate(groups):
                if group in groups2:
                    indexes.append(groups2.index(group))

            prev_id = -1
            for id in indexes:
                if id <= prev_id:
                    return (
                        f"Group \"{groups2[id]}\" is before group \"{groups2[id+1]}\" in element '{name2}', "
                        f"but after group \"{groups2[id+1]}\" in element '{name}'."
                    )
                prev_id = id


def check_groups(inst):
    for type in ['config', 'status']:
        conflict = _check_groups(inst, type)
        if conflict:
            return type, conflict

    return None, None
