from copy import deepcopy
from typing import List, Optional, Union

from KSPUtils.config_node_utils.list_dict import ListDict
from KSPUtils.config_node_utils.value_collection import ValueCollection


class ConfigNode(ValueCollection):
    """
    Simple KSP ConfigNode reader/writer
    """

    def __init__(self, name=""):
        ValueCollection.__init__(self)
        self.subnodes: ListDict[ConfigNode] = ListDict()
        self.name = name

    def Clone(self, other: "ConfigNode") -> None:
        ValueCollection.Clone(self, other)
        self.subnodes = deepcopy(other.subnodes)
        self.name = other.name

    def __bool__(self):
        return bool(self.values) or bool(self.subnodes)

    def AddNode(self, node: Union["ConfigNode", str]) -> "ConfigNode":
        if isinstance(node, str):
            new_node = ConfigNode(node)
        elif isinstance(node, ConfigNode):
            new_node = node
        else:
            raise ValueError("node should be either a string or ConfigNode object")
        self.subnodes.add(new_node.name, new_node)
        return new_node

    def GetNode(self, name: str, idx=0) -> Optional["ConfigNode"]:
        return self.subnodes.get(name, idx)

    def GetNodes(self, name: str) -> List["ConfigNode"]:
        return self.subnodes.get_all(name)

    def HasNode(self, name: str) -> bool:
        return name in self.subnodes

    def Parse(self, text: str) -> None:
        self.values = ListDict()
        self.subnodes = ListDict()
        lines = self._preformat(text.splitlines())
        self._parse(lines, self)
        if len(self.values) == 0 and len(self.subnodes) == 1:
            node = self.subnodes[0]
            if node is not None:
                self.Clone(node)

    @classmethod
    def FromText(cls, text: str) -> "ConfigNode":
        node = cls()
        node.Parse(text)
        return node

    @classmethod
    def Load(cls, filename: str) -> "ConfigNode":
        node = cls()
        try:
            with open(filename, encoding="utf8") as inp:
                node.Parse(inp.read())
        except Exception as exc:
            print(f"Unable to parse {filename}: {exc!s}")
        return node

    def Save(self, filename: str) -> None:
        with open(filename, "w", encoding="utf8") as out:
            out.write(str(self).strip("\n\r"))

    @classmethod
    def _parse(cls, lines: List[List[str]], node: "ConfigNode", index=0) -> int:
        nlines = len(lines)
        while index < nlines:
            line = lines[index]
            if len(line) == 2:
                node.AddValue(*line)
                index += 1
            elif line[0] == "{":
                subnode = node.AddNode("")
                index = cls._parse(lines, subnode, index + 1)
            else:
                if line[0] == "}":
                    return index + 1
                if index < nlines - 1 and lines[index + 1][0] == "{":
                    subnode = node.AddNode(line[0].strip(" \t\xef\xbb\xbf\ufeff"))
                    index = cls._parse(lines, subnode, index + 2)
                else:
                    index += 1
        return index

    @staticmethod
    def _split_by(sym: str, line_num: int, lines: List[str]) -> int:
        line = lines[line_num]
        try:
            idx = line.index(sym)
            if idx == 0 and len(line) == 1:
                return line_num
            if idx > 0:
                lines.insert(line_num, line[:idx])
                line = line[idx:]
                line_num += 1
                idx = 0
                lines[line_num] = line
            if idx < len(line) - 1:
                lines.insert(line_num + 1, line[1:])
                lines[line_num] = sym
                line_num = min(len(lines) - 1, line_num + 2)
        except ValueError:
            pass
        return line_num

    def _preformat(self, lines: List[str]) -> List[List[str]]:
        num_lines = len(lines)
        while num_lines > 0:
            num_lines -= 1
            line = lines[num_lines].strip()
            try:
                idx = line.index("//")
                if idx == 0:
                    del lines[num_lines]
                    continue
                if idx > 0:
                    line = line[:idx]
            except ValueError:
                pass
            line = line.strip()
            if not line:
                del lines[num_lines]
                continue
            lines[num_lines] = line
            num_lines = self._split_by("}", num_lines, lines)
            num_lines = self._split_by("{", num_lines, lines)
        return [[w.strip() for w in line.split("=")] for line in lines]

    def __str__(self):
        name = f"{self.name}\n{{\n"
        values = "\n".join(f"    {value}" for value in self.values)
        nodes = "\n".join(
            f"    {line}" for node in self.subnodes for line in str(node).splitlines()
        )
        if values and nodes:
            values += "\n"
        return "".join((name, values, nodes, "\n}"))
