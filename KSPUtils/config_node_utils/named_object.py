import os
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from KSPUtils.config_node_utils import ConfigNode, ValueCollection
from KSPUtils.config_node_utils.list_dict import ListDict


class NamedDescriptor:
    def __init__(self) -> None:
        self._name = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name


_T = TypeVar("_T")


class ValueProperty(NamedDescriptor, Generic[_T]):
    def __init__(self, converter: Callable[[Any], _T]) -> None:
        super().__init__()
        self._convert = converter

    def __get__(
        self, instance: ValueCollection, owner: Type[ValueCollection]
    ) -> Optional[_T]:
        try:
            raw_value = instance.GetValue(self._name)
            return self._convert(raw_value)
        except (AttributeError, ValueError, TypeError):
            return None

    def __set__(self, instance: ValueCollection, value: Any) -> None:
        instance.SetValue(self._name, self._convert(value))


NamedObjectType = TypeVar("NamedObjectType", bound="NamedObject")


class ChildrenDict(NamedDescriptor, Generic[NamedObjectType]):
    def __init__(self, child_type: Type[NamedObjectType]) -> None:
        super().__init__()
        self._type = child_type

    def _iter_children(
        self, instance: "NamedObject"
    ) -> Generator[Tuple[str, NamedObjectType], None, None]:
        for child in instance.children.get_all(self._type.type):
            if not isinstance(child, self._type):
                continue
            name = child.name
            if name is None:
                continue
            yield name, child

    def __get__(
        self, instance: "NamedObject", owner: Type["NamedObject"]
    ) -> Dict[str, NamedObjectType]:
        return dict(self._iter_children(instance))


# noinspection PyPep8Naming
class NamedObject(ValueCollection):
    _db: Dict[str, Type["NamedObject"]] = {}
    type = "None"

    name = ValueProperty(str)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._db[cls.type] = cls

    def __init__(self):
        ValueCollection.__init__(self)
        self.children: ListDict[NamedObject] = ListDict()

    def __str__(self):
        node = ConfigNode(self.type)
        self.save(node)
        return str(node)

    def AddChild(self, obj: "NamedObject") -> None:
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

    @classmethod
    def LoadFromFile(
        cls: Type[NamedObjectType], path: str
    ) -> Generator["NamedObject", None, None]:
        for obj in cls.LoadFromNode(ConfigNode.Load(path)):
            yield obj

    @classmethod
    def LoadFromPath(
        cls: Type[NamedObjectType], path: str, ext=".cfg", followlinks=True
    ) -> Generator[Optional["NamedObject"], None, None]:
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
    ) -> Generator["NamedObject", None, None]:
        if node.name == cls.type:
            yield cls.from_node(node)
        elif node.subnodes:
            for subnode in node.subnodes:
                for obj in cls.LoadFromNode(subnode):
                    yield obj

    @classmethod
    def Patch(
        cls: Type[NamedObjectType], operator: str, name: str, spec=""
    ) -> NamedObjectType:
        p = cls()
        node = f"{operator}{cls.type}[{name}]"
        if spec:
            node += spec
        p.type = node
        return p

    @classmethod
    def PatchValue(
        cls: Type[NamedObjectType], operator: str, name: str, value: Any
    ) -> ValueCollection.Value:
        return ValueCollection.Value(f"{operator}{name}", value)

    @classmethod
    def _create(
        cls: Type[NamedObjectType], typename
    ) -> Union[NamedObjectType, "NamedObject"]:
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
