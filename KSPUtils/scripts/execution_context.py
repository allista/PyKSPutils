import sys
from functools import reduce
from typing import Callable, Optional, Set, Type

OnErrorHandler = Callable[[str, int], None]


class ExecutionContextError(Exception):
    """Bad usage of ExecutionContext"""


class ExecutionContext:
    """
    Utility context that automatically creates meaningful exit code
    from errors occurring within it.

    Can also handle exceptions.
    """

    message_template = "[{block}] {message}"

    def __init__(
        self,
        on_error: Optional[OnErrorHandler] = None,
        *handle_exceptions: Type[BaseException],
    ):
        self._handle_exceptions = handle_exceptions
        self._on_error = on_error
        self._block_id = 0
        self._block: Optional[str] = None
        self._errors: Set[int] = set()

    def __int__(self):
        return self.exit_code

    def __call__(self, block: str, block_id: int) -> "ExecutionContext":
        """
        Updates block name and ID

        :param block: human-readable block name
        :param block_id: integer block ID, should be in [0, 7] interval
        :return: ExecutionContext instance, self
        """
        if not (0 <= block_id < 8):
            raise ValueError("ExecutionContext: block id should be in [0, 7]")
        self._block = block
        self._block_id = block_id
        return self

    def __enter__(self) -> "ExecutionContext":
        if self._block is None:
            raise ExecutionContextError(
                "Current block is not set, cannot enter the context"
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_val is not None and any(
                isinstance(exc_val, handled) for handled in self._handle_exceptions
            ):
                self.error(f"{exc_val}")
                return True
        finally:
            self._block = None
            self._block_id = 0

    def error(self, message) -> None:
        if self._block is None:
            raise ExecutionContextError("Cannot set error outside of execution block")
        self._errors.add(self._block_id)
        error_message = self.message_template.format(block=self._block, message=message)
        if self._on_error:
            self._on_error(error_message, self.exit_code)
        else:
            print(error_message, file=sys.stderr)

    @property
    def exit_code(self) -> int:
        return reduce(lambda r, b: r | 1 << b, self._errors, 0)

    @property
    def failed(self) -> bool:
        return bool(self._errors)
