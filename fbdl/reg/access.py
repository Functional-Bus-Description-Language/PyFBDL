import math


def single(bus_width, base_addr, width):
    access = {
        'Address': base_addr,
        'Count': math.ceil(width / bus_width)
    }

    if width > bus_width:
        access['Strategy'] = "Linear"
        access['Mask'] = ((width - 1) % bus_width, 0)
    else:
        access['Strategy'] = "Single"
        access['Mask'] = (width - 1, 0)

    return access


def array(bus_width, count, base_addr, width):
    access = {
        'Address': base_addr,
        'Accesses per Item': math.ceil(width / bus_width),
        'Items per Access': math.floor(bus_width / width)
    }

    if access['Accesses per Item'] == 1 and access['Items per Access'] == 1:
        access['Strategy'] = 'Single'
        access['Count'] = count
        access['Mask'] = (width - 1, 0)
    elif access['Accesses per Item'] == 1 and access['Items per Access'] > 1:
        access['Strategy'] = 'Multiple'
        access['Count'] = math.ceil(count / access['Items per Access'])
    else:
        access['Strategy'] = 'Bunch'
        # TODO: Calculate it correctly.
        access['Count'] = 0
        # Number of items in bunch.
        if (width % bus_width) == 0:
            access['Bunch Size'] = 1
        else:
            access['Bunch Size'] = bus_width // (width % bus_width)
        # Number of accesses for bunch transfer.
        access['Accesses per Bunch'] = access['Bunch Size'] * width // bus_width + 1

    return access
