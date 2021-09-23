from . import pre
from . import ts
from .inst import inst
from .reg import reg


def compile(main):
    packages = pre.prepare_packages(main)
    ts.parse(packages)
    bus = inst.instantiate(packages)
    registerified_bus = reg.registerify(bus)

    return registerified_bus
