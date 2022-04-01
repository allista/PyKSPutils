from requests import Response

from KSPUtils.exception_chain import ExceptionChain


class SpacedockError(ExceptionChain):
    """Generic spacedock exception"""

    def __str__(self):
        res = super().__str__()
        if self.cause:
            response = getattr(self.cause, "response", None)
            if isinstance(response, Response):
                return f"{res}\n{response.content}"
        return res
