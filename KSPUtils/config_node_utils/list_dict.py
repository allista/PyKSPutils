from typing import Dict, Generic, Iterator, List, Optional, TypeVar, Union

ListDictKey = Union[str, int]
ValueType = TypeVar("ValueType")


class ListDict(Generic[ValueType]):
    def __init__(self):
        self._values: List[ValueType] = []
        self._index: Dict[str, List[int]] = {}

    def __bool__(self):
        return bool(self._values)

    def __iter__(self) -> Iterator[ValueType]:
        return self._values.__iter__()

    def __getitem__(self, key: ListDictKey) -> Optional[ValueType]:
        if isinstance(key, int):
            return self._values[key]
        if isinstance(key, str):
            return self._values[self._index[key][0]]
        return None

    def __setitem__(self, key: ListDictKey, value: ValueType) -> None:
        if isinstance(key, int):
            self._values[key] = value
        elif isinstance(key, str):
            idx = self._index.get(key, [])
            if idx:
                self._values[idx[0]] = value
            else:
                self.add(key, value)

    def __contains__(self, key: str) -> bool:
        return key in self._index

    def __len__(self) -> int:
        return len(self._values)

    def keys(self) -> List[str]:
        return list(self._index.keys())

    def add(self, key: str, value: ValueType) -> None:
        idx = len(self._values)
        self._values.append(value)
        lst = self._index.get(key, None)
        if lst:
            lst.append(idx)
        else:
            self._index[key] = [idx]

    _GetDefaultType = TypeVar("_GetDefaultType")

    def get(
        self, key: str, default: Optional[_GetDefaultType] = None, idx=0
    ) -> Union[ValueType, Optional[_GetDefaultType]]:
        try:
            return self._values[self._index[key][idx]]
        except (IndexError, KeyError):
            return default

    def get_all(self, key: str) -> List[ValueType]:
        idx = self._index.get(key, [])
        return [self._values[i] for i in idx]
