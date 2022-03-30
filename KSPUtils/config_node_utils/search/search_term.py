import re
from itertools import chain
from typing import List, Optional, Pattern, Union

from KSPUtils.config_node_utils import NamedObject
from KSPUtils.config_node_utils.search.abstract_term import AbstractTerm


class SearchTerm(list, AbstractTerm):
    class Node:
        def __init__(self, nodestring):
            self._nonzero = bool(nodestring)
            node_name = nodestring.split(":")
            if len(node_name) > 2:
                raise ValueError("Incorrect node term format. Should be Node[:name].")
            self.node = re.compile(node_name[0])
            self.name: Optional[Pattern] = (
                None if len(node_name) < 2 else re.compile(node_name[1])
            )

        def __bool__(self):
            return self._nonzero

        def __str__(self):
            if not self:
                return ""
            return (
                self.node.pattern
                if not self.name
                else f"{self.node.pattern}:{self.name.pattern}"
            )

        def __repr__(self):
            return str(self)

        def match(self, obj: NamedObject) -> bool:
            """
            Returns True if the object matches the NodeTerm, False otherwise.
            """
            if not self:
                return True
            return self.node.match(obj.type) is not None and (
                self.name is None
                or self.name.match(obj.name) is not None  # type: ignore[attr-defined]
            )

        def match_as_value(self, obj: NamedObject) -> bool:
            """
            Returns True if one of the object's value matches the NodeTerm, False otherwise.
            """
            if not self:
                return True
            if self.name is None:
                return any(self.node.match(v.name) for v in obj.values)
            return any(
                self.name.match(v.value) for v in obj.values if self.node.match(v.name)
            )

        def match_value(self, val):
            """
            Returns True if the given value matches the NodeTerm, False otherwise.
            :type val: ValueCollection.Value
            :rtype: bool
            """
            if not self:
                return True
            if self.name is None:
                return self.node.match(val.name)
            return self.node.match(val.name) and self.name.match(val.value)

    def __init__(self, string: str) -> None:
        """
        :param string: NODE:name1/SUBNODE:name2/SUBSUBNODE:name3/ValueName:value
        """
        AbstractTerm.__init__(self)
        self.negative = string.startswith("^")
        list.__init__(self, (self.Node(t) for t in string.strip("^").split("/")))

    def __str__(self):
        return AbstractTerm.__str__(self) + "/".join(str(n) for n in self)

    def __repr__(self):
        return str(self)

    @classmethod
    def _match_path(cls, obj: NamedObject, path: List[Node]) -> bool:
        """
        Returns True if the object matches the path, False otherwise.
        """
        if len(path) == 1:
            return path[0].match_as_value(obj)
        if not path[0].match(obj):
            return False
        subpath = path[1:]
        if len(subpath) == 1:
            return cls._match_path(obj, subpath)
        return any(cls._match_path(child, subpath) for child in obj.children)

    SelectResult = List[Union[NamedObject, NamedObject.Value]]

    @classmethod
    def _select_by_path(cls, obj: NamedObject, path: List[Node]) -> SelectResult:
        """
        Returns objects that match the path, None otherwise.
        """
        if len(path) == 1:
            node = path[0]
            if not node:
                return [obj]
            return [v for v in obj.values if node.match_value(v)]
        if not path[0].match(obj):
            return []
        subpath = path[1:]
        if len(subpath) == 1:
            return cls._select_by_path(obj, subpath)
        return list(
            chain.from_iterable(
                objects
                for objects in (
                    cls._select_by_path(child, subpath) for child in obj.children
                )
                if objects
            )
        )

    def _match_object(self, obj: NamedObject) -> bool:
        return self._match_path(obj, self)

    def select(self, obj: NamedObject) -> SelectResult:
        return self._select_by_path(obj, self)

    @classmethod
    def Convert(cls, term):
        return cls(term) if isinstance(term, str) else term
