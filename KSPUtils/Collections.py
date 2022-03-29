from copy import deepcopy


class ListDict(object):
    def __init__(self):
        self._values = []
        self._index = {}

    def __bool__(self):
        return bool(self._values)

    def __iter__(self):
        return self._values.__iter__()

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        elif isinstance(key, str):
            return self._values[self._index[key][0]]

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self._values[key] = value
        elif isinstance(key, str):
            idx = self._index.get(key, [])
            if idx:
                self._values[idx[0]] = value
            else:
                self.add(key, value)

    def __contains__(self, key):
        return key in self._index

    def __len__(self):
        return len(self._values)

    def keys(self):
        return list(self._index.keys())

    def add(self, key, value):
        idx = len(self._values)
        self._values.append(value)
        lst = self._index.get(key, None)
        if lst:
            lst.append(idx)
        else:
            self._index[key] = [idx]

    def get(self, key, default=None, idx=0):
        try:
            return self._values[self._index[key][idx]]
        except (IndexError, KeyError):
            return default

    def get_all(self, key):
        idx = self._index.get(key, [])
        return [self._values[i] for i in idx]


class ValueCollection(object):
    class Value(object):
        def __init__(self, name, value, comment=""):
            self.name = name
            self.value = value
            self.comment = comment

        def __str__(self):
            s = "%s = %s" % (self.name, self.value)
            if self.comment:
                s += " //%s" % self.comment
            return s

    def __init__(self):
        self.values = ListDict()

    def Clone(self, other):
        self.values = deepcopy(other.values)

    def __getitem__(self, key):
        return self.values[key]

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return bool(self.values)

    def AddValue(self, name, value):
        self.values.add(name, self.Value(name, value))

    def AddValueItem(self, value):
        self.values.add(value.name, value)

    def GetValue(self, name, idx=0):
        val = self.values.get(name, None, idx)
        return val.value if val is not None else None

    def GetValues(self, name):
        return self.values.get_all(name)

    def SetValue(self, name, value, idx=0):
        val = self.values.get(name, None, idx)
        if val is not None:
            val.value = value
        else:
            self.values[name] = self.Value(name, value)

    def SetComment(self, name, comment, idx=0):
        val = self.values.get(name, None, idx)
        if val is not None:
            val.comment = comment

    def HasValue(self, name):
        return name in self.values
