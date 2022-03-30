from copy import deepcopy
from typing import Any, List, Optional, TypeVar

from KSPUtils.config_node_utils.list_dict import ListDict

ValueCollectionType = TypeVar("ValueCollectionType", bound="ValueCollection")


class ValueCollection:
    class Value:
        def __init__(self, name: str, value: Any, comment="") -> None:
            self.name = name
            self.value = value
            self.comment = comment

        def __str__(self):
            s = f"{self.name} = {self.value}"
            if self.comment:
                s += f" //{self.comment}"
            return s

    def __init__(self):
        self.values: ListDict[ValueCollection.Value] = ListDict()

    def Clone(self: ValueCollectionType, other: ValueCollectionType) -> None:
        self.values = deepcopy(other.values)

    def __getitem__(self, key: str) -> Optional[Value]:
        return self.values[key]

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return bool(self.values)

    def AddValue(self, name: str, value: Any) -> None:
        self.values.add(name, self.Value(name, value))

    def AddValueItem(self, value: Value) -> None:
        self.values.add(value.name, value)

    def GetValue(self, name: str, idx=0) -> Optional[Any]:
        val = self.values.get(name, None, idx)
        return val.value if val is not None else None

    def GetValues(self, name: str) -> List[Value]:
        return self.values.get_all(name)

    def SetValue(self, name: str, value: Any, idx=0) -> None:
        val = self.values.get(name, None, idx)
        if val is not None:
            val.value = value
        else:
            self.values[name] = self.Value(name, value)

    def SetComment(self, name: str, comment: str, idx=0):
        val = self.values.get(name, None, idx)
        if val is not None:
            val.comment = comment

    def HasValue(self, name: str) -> bool:
        return name in self.values
