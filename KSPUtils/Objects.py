import os

from .Collections import ValueCollection, ListDict
from .ConfigNode import ConfigNode


class NamedObject(ValueCollection):
    _db = {}
    type = 'None'

    @classmethod
    def LoadFromFile(cls, path):
        for obj in cls.LoadFromNode(ConfigNode.Load(path)):
            yield obj

    @classmethod
    def LoadFromPath(cls, path, ext='.cfg', followlinks=True):
        if os.path.isfile(path):
            for obj in cls.LoadFromFile(path):
                yield obj
            return
        if not os.path.isdir(path):
            yield None
            return
        for dirpath, _dirnames, filenames in os.walk(path, followlinks=followlinks):
            for filename in filenames:
                if not filename.endswith(ext): continue
                for obj in cls.LoadFromFile(os.path.join(dirpath, filename)):
                    yield obj

    @classmethod
    def LoadFromNode(cls, node):
        if node.name == cls.type:
            yield cls.from_node(node)
        elif node.subnodes:
            for subnode in node.subnodes:
                for obj in cls.LoadFromNode(subnode):
                    yield obj

    @classmethod
    def Patch(cls, operator, name, spec=''):
        p = cls()
        node = '%s%s[%s]' % (operator, cls.type, name)
        if spec: node += spec
        p.type = node
        return p

    @classmethod
    def PatchValue(cls, operator, name, value):
        return ValueCollection.Value('%s%s' % (operator, name), value)

    @classmethod
    def register(cls, typename):
        NamedObject._db[typename] = cls
        cls.type = typename

    @classmethod
    def _create(cls, typename):
        T = cls._db.get(typename)
        if T is None: T = NamedObject
        o = T()
        o.type = typename
        return o

    @classmethod
    def from_node(cls, node):
        o = cls()
        o.type = node.name
        o.load(node)
        return o

    @classmethod
    def mirror_value(cls, name, T=str):
        def getter(self):
            try: return T(self.GetValue(name))
            except: return None
        def setter(self, val): self.SetValue(name, T(val))
        setattr(cls, name, property(getter, setter))

    @classmethod
    def setup_children_dict(cls, name, typename):
        def children(self):
            return dict((c.name, c) for c in self.children.get_all(typename))
        def has_children(self, *names):
            d = getattr(self, name)
            return all(n in d for n in names) if d else False
        setattr(cls, name, property(children))
        setattr(cls, 'has_'+name, has_children)

    def __init__(self):
        ValueCollection.__init__(self)
        self.children = ListDict()

    def AddChild(self, obj):
        self.children.add(obj.type, obj)

    def load(self, node):
        self.values = ListDict()
        [self.AddValueItem(v) for v in node.values]
        for n in node.subnodes:
            c = self._create(n.name)
            self.children.add(c.type, c)
            c.load(n)

    def save(self, node):
        [node.AddValueItem(v) for v in self.values]
        for c in self.children:
            c.save(node.AddNode(c.type))

    def __str__(self):
        node = ConfigNode(self.type)
        self.save(node)
        return str(node)
NamedObject.mirror_value('name')


class Part(NamedObject): pass
Part.register('PART')
Part.mirror_value('mass', float)
Part.mirror_value('cost', float)
Part.mirror_value('title')
Part.mirror_value('description')
Part.setup_children_dict('resources', 'RESOURCE')
Part.setup_children_dict('modules', 'MODULE')

class Resource(NamedObject): pass
Resource.register('RESOURCE')
Resource.mirror_value('amount', float)
Resource.mirror_value('maxAmount', float)

class Module(NamedObject): pass
Module.register('MODULE')
