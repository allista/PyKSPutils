from KSPUtils.config_node_utils.search.abstract_term import AbstractTerm
from KSPUtils.config_node_utils.search.search_term import SearchTerm


class SearchGroup(list, AbstractTerm):
    def __init__(self, *terms):
        AbstractTerm.__init__(self)
        list.__init__(self, (SearchTerm.Convert(t) for t in terms))

    def _match_object(self, obj):
        return all(t.match(obj) for t in self)

    def __str__(self):
        return f"{{{AbstractTerm.__str__(self)}{' AND '.join(str(t) for t in self)}}}"

    def __repr__(self):
        return str(self)
