import os
from typing import Any, Callable, Dict, Generator, Optional, Type, TypeVar

from KSPUtils.config_node_utils import ConfigNode, ValueCollection
from KSPUtils.config_node_utils.list_dict import ListDict

NamedObjectType = TypeVar("NamedObjectType", bound="NamedObject")


class NamedObject(ValueCollection):
    _db: Dict[str, Type["NamedObject"]] = {}
    type = "None"

    @classmethod
    def LoadFromFile(
        cls: Type[NamedObjectType], path: str
    ) -> Generator[NamedObjectType, None, None]:
        for obj in cls.LoadFromNode(ConfigNode.Load(path)):
            yield obj

    @classmethod
    def LoadFromPath(
        cls: Type[NamedObjectType], path: str, ext=".cfg", followlinks=True
    ) -> Generator[Optional[NamedObjectType], None, None]:
        if os.path.isfile(path):
            for obj in cls.LoadFromFile(path):
                yield obj
            return
        if not os.path.isdir(path):
            yield None
            return
        for dirpath, _dirnames, filenames in os.walk(path, followlinks=followlinks):
            for filename in filenames:
                if not filename.endswith(ext):
                    continue
                for obj in cls.LoadFromFile(os.path.join(dirpath, filename)):
                    yield obj

    @classmethod
    def LoadFromNode(
        cls: Type[NamedObjectType], node: ConfigNode
    ) -> Generator[NamedObjectType, None, None]:
        if node.name == cls.type:
            yield cls.from_node(node)
        elif node.subnodes:
            for subnode in node.subnodes:
                for obj in cls.LoadFromNode(subnode):
                    yield obj

    @classmethod
    def Patch(cls: Type[NamedObjectType], operator, name, spec=""):
        p = cls()
        node = f"{operator}{cls.type}[{name}]"
        if spec:
            node += spec
        p.type = node
        return p

    @classmethod
    def PatchValue(cls: Type[NamedObjectType], operator, name, value):
        return ValueCollection.Value(f"{operator}{name}", value)

    @classmethod
    def register(cls: Type[NamedObjectType], typename: str) -> None:
        NamedObject._db[typename] = cls
        cls.type = typename

    @classmethod
    def _create(cls: Type[NamedObjectType], typename):
        klass = cls._db.get(typename, NamedObject)
        o = klass()
        o.type = typename
        return o

    @classmethod
    def from_node(cls: Type[NamedObjectType], node: ConfigNode) -> NamedObjectType:
        obj: NamedObjectType = cls()
        obj.type = node.name
        obj.load(node)
        return obj

    _T = TypeVar("_T")
    ConverterType = Callable[[Any], _T]

    @classmethod
    def mirror_value(cls, name: str, convert: ConverterType = str) -> None:
        def getter(self: NamedObject) -> Optional[NamedObject._T]:
            try:
                return convert(self.GetValue(name))
            except Exception:
                return None

        def setter(self: NamedObject, val: Any) -> None:
            self.SetValue(name, val)

        setattr(cls, name, property(getter, setter))

    @classmethod
    def setup_children_dict(cls, name, typename):
        def children(self):
            return dict((c.name, c) for c in self.children.get_all(typename))

        def has_children(self, *names):
            d = getattr(self, name)
            return all(n in d for n in names) if d else False

        setattr(cls, name, property(children))
        setattr(cls, "has_" + name, has_children)

    def __init__(self):
        ValueCollection.__init__(self)
        self.children: ListDict[NamedObject] = ListDict()

    def AddChild(self: NamedObjectType, obj: NamedObjectType) -> None:
        self.children.add(obj.type, obj)

    def load(self, node: ConfigNode) -> None:
        self.values = ListDict()
        for value in node.values:
            self.AddValueItem(value)
        for n in node.subnodes:
            c = self._create(n.name)
            self.children.add(c.type, c)
            c.load(n)

    def save(self, node):
        for value in node.values:
            self.AddValueItem(value)
        for c in self.children:
            c.save(node.AddNode(c.type))

    def __str__(self):
        node = ConfigNode(self.type)
        self.save(node)
        return str(node)
