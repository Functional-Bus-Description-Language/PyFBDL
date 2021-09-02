"""
Module for code validating elements.
"""
ValidElements = {
    'block': {
        'Valid Elements': ('block', 'config', 'func', 'mask', 'status'),
        'Valid Properties': ('doc'),
    },
    'bus': {
        'Valid Elements': ('block', 'config', 'func', 'mask', 'status'),
        'Valid Properties': ('doc', 'masters', 'width'),
    },
    'config': {
        'Valid Elements': (),
        'Valid Properties': ('atomic', 'doc', 'once', 'width'),
    },
    'func': {'Valid Elements': ('param'), 'Valid Properties': ('doc')},
    'mask': {
        'Valid Elements': (),
        'Valid Properties': ('atomic', 'default', 'doc', 'width'),
    },
    'param': {
        'Valid Elements': (),
        'Valid Properties': ('default', 'doc', 'range', 'width'),
    },
    'status': {
        'Valid Elements': (),
        'Valid Properties': ('atomic', 'doc', 'once', 'width'),
    },
}


def validate_properties(properties, element_type):
    for p in properties:
        if p not in ValidElements[element_type]['Valid Properties']:
            return p

    return None


def validate_elements(elements, element_type):
    for e, v in elements.items():
        if v['Type'] not in ValidElements[element_type]['Valid Elements']:
            return e, v['Type']

    return None, None
