import os

from .Collections import ValueCollection, ListDict
from .ConfigNode import ConfigNode

class NamedObject(ValueCollection):
    _db = {}
    type = 'None'

    @classmethod
    def LoadFromPath(cls, path, ext='.cfg', followlinks=True):
        objects = []
        for dirpath, _dirnames, filenames in os.walk(path, followlinks=followlinks):
            for filename in filenames:
                if not filename.endswith(ext): continue
                node = ConfigNode.Load(os.path.join(dirpath, filename))
                if node.name != cls.type: continue
                obj = cls.from_node(node)
                objects.append(obj)
        return objects

    @classmethod
    def Patch(cls, name, mod, spec='', insert=False):
        p = cls()
        node = '%' if insert else '@'
        node += ('%s[%s]:FOR[%s]%s' % (cls.type, name, mod, spec))
        p.type = node
        return p

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
        def getter(self): return T(self.GetValue(name))
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
