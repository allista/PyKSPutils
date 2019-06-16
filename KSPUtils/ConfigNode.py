from copy import deepcopy

from .Collections import ValueCollection, ListDict


class ConfigNode(ValueCollection):
    """
    Simple KSP ConfigNode reader/writer
    """

    def __init__(self, name=""):
        ValueCollection.__init__(self)
        self.subnodes = ListDict()
        self.name = name

    def Clone(self, other):
        ValueCollection.Clone(self, other)
        self.subnodes = deepcopy(other.subnodes)
        self.name = other.name

    def __bool__(self):
        return bool(self.values) or bool(self.subnodes)

    def AddNode(self, node):
        if isinstance(node, str):
            new_node = ConfigNode(node)
        elif isinstance(node, ConfigNode):
            new_node = node
        else:
            raise ValueError("node should be either a string or ConfigNode object")
        self.subnodes.add(new_node.name, new_node)
        return new_node

    def GetNode(self, name, idx=0):
        return self.subnodes.get(name, idx)

    def GetNodes(self, name):
        return self.subnodes.get_all(name)

    def HasNode(self, name):
        return name in self.subnodes

    def Parse(self, text):
        self.values = ListDict()
        self.subnodes = ListDict()
        lines = self._preformat(text.splitlines())
        self._parse(lines, self)
        if len(self.values) == 0 and len(self.subnodes) == 1:
            self.Clone(self.subnodes[0])

    @classmethod
    def FromText(cls, text):
        node = cls()
        node.Parse(text)
        return node

    @classmethod
    def Load(cls, filename):
        node = cls()
        try:
            with open(filename, encoding='utf8') as inp:
                node.Parse(inp.read())
        except Exception as exc:
            print(f'Unable to parse {filename}: {exc!s}')
        return node

    def Save(self, filename):
        with open(filename, 'w', encoding='utf8') as out:
            out.write(str(self).strip('\n\r'))

    @classmethod
    def _parse(cls, lines, node, index=0):
        nlines = len(lines)
        while index < nlines:
            line = lines[index]
            if len(line) == 2:
                node.AddValue(*line)
                index += 1
            elif line[0] == '{':
                subnode = node.AddNode("")
                index = cls._parse(lines, subnode, index + 1)
            else:
                if line[0] == '}': return index + 1
                if index < nlines - 1 and lines[index + 1][0] == '{':
                    subnode = node.AddNode(line[0].strip(' \t\xef\xbb\xbf\ufeff'))
                    index = cls._parse(lines, subnode, index + 2)
                else:
                    index += 1
        return index

    @staticmethod
    def _split_by(sym, l, lines):
        line = lines[l]
        try:
            idx = line.index(sym)
            if idx == 0 and len(line) == 1: return l
            if idx > 0:
                lines.insert(l, line[:idx])
                line = line[idx:]
                l += 1;
                idx = 0
                lines[l] = line
            if idx < len(line) - 1:
                lines.insert(l + 1, line[1:])
                lines[l] = sym
                l = min(len(lines) - 1, l + 2)
        except ValueError:
            pass
        return l

    def _preformat(self, lines):
        l = len(lines)
        while l > 0:
            l -= 1
            line = lines[l]
            try:
                idx = line.index('//')
                if idx == 0:
                    del lines[l]
                    continue
                elif idx > 0:
                    line = line[:idx]
            except ValueError:
                pass
            line = line.strip()
            if not line:
                del lines[l]
                continue
            lines[l] = line
            l = self._split_by('}', l, lines)
            l = self._split_by('{', l, lines)
        return [[w.strip() for w in line.split('=')] for line in lines]

    def __str__(self):
        s = '%s\n{\n' % self.name
        v = '\n'.join('    %s' % v for v in self.values)
        n = '\n'.join('    %s' % l for n in self.subnodes
                      for l in str(n).splitlines())
        if v and n: v += '\n'
        return ''.join((s, v, n, '\n}'))
