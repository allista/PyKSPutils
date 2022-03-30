from KSPUtils.config_node_utils import NamedObject


class AbstractTerm:
    def __init__(self):
        self.negative = False

    # pylint: disable=no-self-use
    def _match_object(self, _obj: NamedObject) -> bool:
        """
        Returns True if the object matches the term positively, False otherwise.
        """
        return True

    def match(self, obj: NamedObject) -> bool:
        """
        Returns True if the object matches the term, False otherwise.
        """
        m = self._match_object(obj)
        return not m if self.negative else m

    def __str__(self):
        return "^" if self.negative else ""

    def __repr__(self):
        return str(self)
