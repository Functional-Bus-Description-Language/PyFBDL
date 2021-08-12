"""
Module for code validating elements.
"""
ValidElements = {
    'func': {'Valid Elements': ('param'), 'Valid Properties': ('doc')},
    'mask': {
        'Valid Elements': (),
        'Valid Properties': ('atomic', 'default', 'doc', 'width'),
    },
    'param': {
        'Valid Elements': (),
        'Valid Properties': ('default', 'doc', 'range', 'width'),
    },
}


def validate_properties(properties, element_type):
    for p in properties:
        if p not in ValidElements[element_type]['Valid Properties']:
            return p

    return None
