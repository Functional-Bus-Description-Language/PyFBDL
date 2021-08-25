class RefDict(dict):
    def __init__(self, d):
        super().__init__()
        self.d = d
        self.id = self.d['Id']

    # TODO: Report the problem with __repr__ as issue somewhere.
    def __repr__(self):
        return f"RD to '{self.id}'"
        # return f"{{'RefDict to' : {self.id}}}"

    def __getitem__(self, key):
        return self.d[key]

    def __setitem__(self, key):
        raise Exception("Trying to set key via RefDict.")

    def get(self, key):
        return self.d.get(key)

    def items(self):
        return self.d.items()
