import re
from collections import Counter

from KSPUtils.config_node_utils.search.abstract_term import AbstractTerm
from KSPUtils.config_node_utils.search.search_group import SearchGroup
from KSPUtils.config_node_utils.search.search_term import SearchTerm


class SearchQuery(AbstractTerm):
    class _Or(AbstractTerm):
        def __init__(self, term1, term2):
            AbstractTerm.__init__(self)
            self.term1 = term1
            self.term2 = term2

        def _match_object(self, obj):
            return self.term1.match(obj) or self.term2.match(obj)

        def __str__(self):
            return AbstractTerm.__str__(self) + f"{self.term1} OR {self.term2}"

    def __init__(self, term=None):
        AbstractTerm.__init__(self)
        self.root = SearchGroup(term) if term else SearchGroup()
        self.last = self.root

    def And(self, term):
        self.last.append(SearchTerm.Convert(term))
        return self

    def Or(self, term):
        self.last = SearchGroup(SearchTerm.Convert(term))
        self.root = SearchGroup(self._Or(self.root, self.last))
        return self

    def Brackets(self):
        self.last = self.root
        return self

    def _match_object(self, obj):
        return self.root.match(obj)

    def __str__(self):
        return AbstractTerm.__str__(self) + str(self.root)

    def __repr__(self):
        return str(self)

    AND = "&&"
    OR = "||"
    OPS = (AND, OR)
    op_re = re.compile(r"(\|\||&&)")

    class _Tree(list):
        def __init__(self, parent=None):
            super().__init__()
            self.parent = parent

        def subtree(self):
            tree = self.__class__(self)
            self.append(tree)
            return tree

        def __str__(self):
            return "{\n%s\n}" % "\n".join(
                f"    {line}" for token in self for line in str(token).splitlines()
            )

    @classmethod
    def _expand2tree(cls, string):
        tree = cls._Tree()
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
        while len(tree) == 1 and isinstance(tree[0], SearchQuery._Tree):
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
                    term = SearchTerm.Convert(term)
                    if term[0].node.match(root_node) is None:
                        term.insert(0, SearchTerm.Node(root_node))
                query.And(term)
            else:
                query.Or(term)

        for leaf in tree:
            if leaf in cls.OPS:
                last_op = leaf
            elif isinstance(leaf, SearchQuery._Tree):
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
