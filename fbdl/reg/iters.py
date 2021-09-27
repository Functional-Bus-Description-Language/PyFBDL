import math


class RegisterArray:
    def __init__(self, bus_width, count, base_addr, width):
        self.bus_width = bus_width
        self.count = count
        self.base_addr = base_addr
        self.width = width
        self.item_width = math.ceil(width / bus_width)

    def __repr__(self):
        return f"'Base Address': {self.base_addr}, 'Items': {self.count}, 'Item Width': {self.item_width}"

    def __len__(self):
        return self.count

    def __getitem__(self, idx):
        if idx < 0 or self.count <= idx:
            raise IndexError()

        item_addr = self.base_addr + self.item_width * idx

        registers = []
        for i in self.item_width:
            registers.append(
                [
                    item_addr,
                    (
                        self.bus_width - 1
                        if self.width - i * self.bus_width > self.bus_width
                        else self.width - 1 - i * self.bus_width,
                        0,
                    ),
                ]
            )
            item_addr += 1

        return registers


class AddressSpace:
    def __init__(self, base_addr, count, block_size):
        self.base_addr = base_addr
        self.count = count
        self.block_size = block_size

    def __repr__(self):
        pass

    def __len__(self):
        return self.count

    def __getitem__(self, idx):
        if idx < 0 or self.count <= idx:
            raise IndexError()

        beginning = self.base_addr + idx * self.block_size
        end = beginning + self.block_size - 1

        return beginning, end
