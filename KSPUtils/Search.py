from __future__ import print_function

import re
from KSPUtils import NamedObject


class _AbstractTerm(object):
    def __init__(self):
        self.negative = False

    def _match_object(self, obj):
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
        return '^' if self.negative else ''


class Term(list, _AbstractTerm):
    class Node(object):
        def __init__(self, nodestring):
            self._nonzero = bool(nodestring)
            node_name = nodestring.split(':')
            if len(node_name) > 2:
                raise ValueError('Incorrect node term format. Should be Node[:name].')
            self.node = re.compile(node_name[0])
            self.name = None if len(node_name) < 2 else re.compile(node_name[1])

        def __nonzero__(self): return self._nonzero

        def __str__(self):
            if not self: return ''
            return (self.node.pattern if not self.name
                    else '%s:%s' % (self.node.pattern, self.name.pattern))

        def match(self, obj):
            """
            Returns True if the object matches the NodeTerm, False otherwise.
            :type obj: NamedObject
            :rtype: bool
            """
            if not self: return True
            return self.node.match(obj.type) and (self.name is None or self.name.match(obj.name))

        def match_as_value(self, obj):
            """
            Returns True if one of the object's value matches the NodeTerm, False otherwise.
            :type obj: NamedObject
            :rtype: bool
            """
            if not self: return True
            return (any(self.node.match(v.name) for v in obj.values) if self.name is None
                    else
                    any(self.name.match(v.value) for v in obj.values if self.node.match(v.name)))

    def __init__(self, string):
        """
        :param string str: NODE:name1/SUBNODE:name2/SUBSUBNODE:name3/ValueName:value
        """
        _AbstractTerm.__init__(self)
        self.negative = string.startswith('^')
        list.__init__(self, (self.Node(t) for t in string.strip('^').split('/')))

    def __str__(self):
        return _AbstractTerm.__str__(self) + '/'.join(str(n) for n in self)

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
        if not path[0].match(obj): return False
        subpath = path[1:]
        if len(subpath) == 1:
            return cls._match_path(obj, subpath)
        return any(cls._match_path(child, subpath)
                   for child in obj.children)

    def _match_object(self, obj):
        return self._match_path(obj, self)

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
        return '{%s%s}' % (_AbstractTerm.__str__(self), ' AND '.join(str(t) for t in self))


class Query(_AbstractTerm):
    class _Or(_AbstractTerm):
        def __init__(self, term1, term2):
            _AbstractTerm.__init__(self)
            self.term1 = term1
            self.term2 = term2

        def _match_object(self, obj):
            return (self.term1.match(obj)
                    or
                    self.term2.match(obj))

        def __str__(self):
            return _AbstractTerm.__str__(self) + ('%s OR %s ' % (self.term1, self.term2))

    def __init__(self, term):
        _AbstractTerm.__init__(self)
        self.root = Group(term)
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
