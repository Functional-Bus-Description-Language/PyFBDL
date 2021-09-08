"""
Module for resolving argument lists.
"""
from copy import copy

from ..validation import ValidElements


def resolve_arguments(symbol, parameters):
    # TODO: Veiryf if there is a need to copy here.
    # Probably not with the approach where the 'Resolved Arguments' attribute
    # is temporarily attached to the node with Element Type Definition.
    args = symbol.get('Arguments', ())
    resolved_arguments = {}
    in_positional_arguments = True
    for i, p in enumerate(parameters):
        if in_positional_arguments:
            if i < len(args):
                arg_name = args[i].get('Name')
            else:
                in_positional_arguments = False
                arg_name = None
            if arg_name:
                in_positional_arguments = False
                if arg_name == p['Name']:
                    resolved_arguments[p['Name']] = copy(args[i]['Value'])
                else:
                    for a in args:
                        if a['Name'] == p['Name']:
                            resolved_arguments[p['Name']] = copy(a['Value'])
                            break
                    else:
                        resolved_arguments[p['Name']] = copy(p['Default Value'])
            else:
                if i < len(args):
                    resolved_arguments[p['Name']] = copy(args[i]['Value'])
                else:
                    resolved_arguments[p['Name']] = copy(p['Default Value'])
        else:
            for a in args:
                if a['Name'] == p['Name']:
                    resolved_arguments[p['Name']] = copy(a['Value'])
                    break
            else:
                resolved_arguments[p['Name']] = copy(p['Default Value'])
    return resolved_arguments


def resolve_argument_lists_in_symbols(symbols, packages):
    for name, symbol in symbols.items():
        if symbol['Kind'] not in [
            'Element Anonymous Instantiation',
            'Element Definitive Instantiation',
            'Element Type Definition',
        ]:
            continue
        # Base elements can not have parameter list.
        if symbol['Type'] not in ValidElements:
            params = packages.get_symbol(symbol['Type'], symbol).get('Parameters')
            if params:
                symbol['Resolved Arguments'] = resolve_arguments(symbol, params)
        if 'Symbols' in symbol:
            resolve_argument_lists_in_symbols(symbol['Symbols'], packages)


def resolve_argument_lists(packages):
    for _, pkgs in packages.items():
        for pkg in pkgs:
            resolve_argument_lists_in_symbols(pkg['Symbols'], packages)
