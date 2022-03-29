import re
from collections import Counter
from itertools import chain

from .Objects import NamedObject


class _AbstractTerm:
    def __init__(self):
        self.negative = False

    # pylint: disable=no-self-use
    def _match_object(self, _obj: NamedObject) -> bool:
        """
        Returns True if the object matches the term positively, False otherwise.
        :type obj: NamedObject
        :rtype: bool
        """
        return True

    def match(self, obj):
        """
        Returns True if the object matches the term, False otherwise.
        :type obj: NamedObject
        :rtype: bool
        """
        m = self._match_object(obj)
        return not m if self.negative else m

    def __str__(self):
        return "^" if self.negative else ""

    def __repr__(self):
        return str(self)


class Term(list, _AbstractTerm):
    class Node:
        def __init__(self, nodestring):
            self._nonzero = bool(nodestring)
            node_name = nodestring.split(":")
            if len(node_name) > 2:
                raise ValueError("Incorrect node term format. Should be Node[:name].")
            self.node = re.compile(node_name[0])
            self.name = None if len(node_name) < 2 else re.compile(node_name[1])

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

        def match(self, obj):
            """
            Returns True if the object matches the NodeTerm, False otherwise.
            :type obj: NamedObject
            :rtype: bool
            """
            if not self:
                return True
            return self.node.match(obj.type) and (
                self.name is None or self.name.match(obj.name)
            )

        def match_as_value(self, obj):
            """
            Returns True if one of the object's value matches the NodeTerm, False otherwise.
            :type obj: NamedObject
            :rtype: bool
            """
            if not self:
                return True
            return (
                any(self.node.match(v.name) for v in obj.values)
                if self.name is None
                else any(
                    self.name.match(v.value)
                    for v in obj.values
                    if self.node.match(v.name)
                )
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

    def __init__(self, string):
        """
        :param string str: NODE:name1/SUBNODE:name2/SUBSUBNODE:name3/ValueName:value
        """
        _AbstractTerm.__init__(self)
        self.negative = string.startswith("^")
        list.__init__(self, (self.Node(t) for t in string.strip("^").split("/")))

    def __str__(self):
        return _AbstractTerm.__str__(self) + "/".join(str(n) for n in self)

    def __repr__(self):
        return str(self)

    @classmethod
    def _match_path(cls, obj, path):
        """
        Returns True if the object matches the path, False otherwise.
        :type obj: NamedObject
        :type path: list
        :rtype: bool
        """
        if len(path) == 1:
            return path[0].match_as_value(obj)
        if not path[0].match(obj):
            return False
        subpath = path[1:]
        if len(subpath) == 1:
            return cls._match_path(obj, subpath)
        return any(cls._match_path(child, subpath) for child in obj.children)

    @classmethod
    def _select_by_path(cls, obj, path):
        """
        Returns objects that match the path, None otherwise.
        :type obj: NamedObject
        :type path: list
        :rtype: list of NamedObjects
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

    def _match_object(self, obj):
        return self._match_path(obj, self)

    def select(self, obj):
        return self._select_by_path(obj, self)

    @classmethod
    def Convert(cls, term):
        return cls(term) if isinstance(term, str) else term


class Group(list, _AbstractTerm):
    def __init__(self, *terms):
        _AbstractTerm.__init__(self)
        list.__init__(self, (Term.Convert(t) for t in terms))

    def _match_object(self, obj):
        return all(t.match(obj) for t in self)

    def __str__(self):
        return f"{{{_AbstractTerm.__str__(self)}{' AND '.join(str(t) for t in self)}}}"

    def __repr__(self):
        return str(self)


class Query(_AbstractTerm):
    class _Or(_AbstractTerm):
        def __init__(self, term1, term2):
            _AbstractTerm.__init__(self)
            self.term1 = term1
            self.term2 = term2

        def _match_object(self, obj):
            return self.term1.match(obj) or self.term2.match(obj)

        def __str__(self):
            return _AbstractTerm.__str__(self) + f"{self.term1} OR {self.term2}"

    def __init__(self, term=None):
        _AbstractTerm.__init__(self)
        self.root = Group(term) if term else Group()
        self.last = self.root

    def And(self, term):
        self.last.append(Term.Convert(term))
        return self

    def Or(self, term):
        self.last = Group(Term.Convert(term))
        self.root = Group(self._Or(self.root, self.last))
        return self

    def Brackets(self):
        self.last = self.root
        return self

    def _match_object(self, obj):
        return self.root.match(obj)

    def __str__(self):
        return _AbstractTerm.__str__(self) + str(self.root)

    def __repr__(self):
        return str(self)

    AND = "&&"
    OR = "||"
    OPS = (AND, OR)
    op_re = re.compile(r"(\|\||&&)")

    class _tree(list):
        def __init__(self, parent=None):
            super().__init__()
            self.parent = parent

        def subtree(self):
            tree = Query._tree(self)
            self.append(tree)
            return tree

        def __str__(self):
            return "{\n%s\n}" % "\n".join(
                f"    {line}" for token in self for line in str(token).splitlines()
            )

    @classmethod
    def _expand2tree(cls, string):
        tree = cls._tree()
        cur = tree
        buf = []

        def flush(buffer):
            if buffer:
                cur.extend(
                    atom
                    for atom in (
                        a.strip() for a in cls.op_re.split("".join(buffer).strip())
                    )
                    if atom
                )
            return []

        for letter in string:
            if letter == "{":
                buf = flush(buf)
                cur = cur.subtree()
            elif letter == "}":
                buf = flush(buf)
                cur = cur.parent
            else:
                buf.append(letter)
        flush(buf)
        while len(tree) == 1 and isinstance(tree[0], Query._tree):
            tree = tree[0]
            tree.parent = None
        return tree

    @classmethod
    def _tree2query(cls, tree, root_node):
        query = cls()
        last_op = None

        def add(term):
            if last_op is None or last_op == cls.AND:
                if root_node:
                    term = Term.Convert(term)
                    if term[0].node.match(root_node) is None:
                        term.insert(0, Term.Node(root_node))
                query.And(term)
            else:
                query.Or(term)

        for leaf in tree:
            if leaf in cls.OPS:
                last_op = leaf
            elif isinstance(leaf, Query._tree):
                add(cls._tree2query(leaf, root_node).root)
                last_op = None
            else:
                add(leaf)
        return query

    @classmethod
    def Parse(cls, string, root_node=None):
        # join multiline
        string = " ".join(string.split("\n\r"))
        # remove white spaces
        string = string.strip()
        # perform bracket count
        c = Counter(string)
        if ("{" in c or "}" in c) and c["{"] != c["}"]:
            raise ValueError("Malformed query string: unbalanced brackets.")
        # expand all internal groups into a tree
        tree = cls._expand2tree(string)
        # construct a query from the resulted tree
        query = cls._tree2query(tree, root_node=root_node)
        return query


if __name__ == "__main__":
    print(
        Query.Parse(
            "sdf && "
            "{wetqew ||  asdljf} && "
            "{saldkjf ||   {asdl || kjf} && wet } || lask djg"
        )
    )
