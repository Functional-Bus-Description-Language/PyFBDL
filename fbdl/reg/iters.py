import math


class RegisterArray:
    def __init__(self, bus_width, count, base_addr, width):
        self.bus_width = bus_width
        self.count = count
        self.base_addr = base_addr
        self.width = width

        self.accesses_per_item = math.ceil(width / bus_width)
        self.items_per_access = math.floor(bus_width / width)
        # Number of items in bunch.
        if (width % bus_width) == 0:
            self.bunch_size = 1
        else:
            self.bunch_size = bus_width // (width % bus_width)
        # Number of accesses for bunch transfer.
        self.accesses_per_bunch = self.bunch_size * width // bus_width + 1

        if self.accesses_per_item == 1 and self.items_per_access == 1:
            self.strategy = 'single'
            self.registers_count = count
        elif self.accesses_per_item == 1 and self.items_per_access > 1:
            self.strategy = 'multiple'
            self.registers_count = math.ceil(count / self.items_per_access)
        else:
            self.strategy = 'bunch'
            self.registers_count = 0

    def __repr__(self):
        repr = (
            f"'Base Address': {self.base_addr}, "
            + f"'Items': {self.count}, "
            + f"'Accesses per Item': {self.accesses_per_item}, "
            + f"'Items per Access': {self.items_per_access}, "
            + f"'Bunch Size': {self.bunch_size}, "
            + f"'Accesses per Bunch': {self.accesses_per_bunch}, "
            + f"'Strategy': {self.strategy}, "
            + f"'Registers Count': {self.registers_count}"
        )
        return repr

    def __len__(self):
        return self.count

    def __getitem__(self, idx):
        if idx < 0 or self.count <= idx:
            raise IndexError()

        if self.strategy == 'single':
            return self._get_item_single(idx)

        # item_addr = self.base_addr + self.item_width * idx

        # registers = []
        # for i in self.item_width:
        #    registers.append(
        #        [
        #            item_addr,
        #            (
        #                self.bus_width - 1
        #                if self.width - i * self.bus_width > self.bus_width
        #                else self.width - 1 - i * self.bus_width,
        #                0,
        #            ),
        #        ]
        #    )
        #    item_addr += 1

        # return tuple(registers)

    def _get_item_single(self, idx):
        item_addr = self.base_addr + idx

        return ((item_addr, (self.width, 0)),)

    def _get_item_multiple(self, idx):
        item_addr = self.base_addr + idx // self.items_per_access
        item_in_access = idx % self.items_per_access

        return (
            (
                item_addr,
                (self.width * (item_in_access + 1) - 1, self.width * (item_in_access)),
            ),
        )


class AddressSpace:
    def __init__(self, base_addr, count, block_size):
        self.base_addr = base_addr
        self.count = count
        self.block_size = block_size

    def __repr__(self):
        repr = (
            f"'Base Address': {self.base_addr}, "
            + f"'Count': {self.count}, "
            + f"'Block Size': {self.block_size}"
        )
        return repr

    def __len__(self):
        return self.count

    def __getitem__(self, idx):
        if idx < 0 or self.count <= idx:
            raise IndexError()

        beginning = self.base_addr + idx * self.block_size
        end = beginning + self.block_size - 1

        return beginning, end
