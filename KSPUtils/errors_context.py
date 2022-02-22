import sys
from collections import defaultdict
from typing import List, NamedTuple, Optional, Tuple, Type


class ErrorsContextError(Exception):
    """Bad usage of ErrorsContextError"""


class Block(NamedTuple):
    name: str
    exceptions: Tuple[Type[BaseException]]


class ErrorsContext:
    """
    Utility context that keeps registry of errors occurred within it,
    keyed by block name.

    It can also handle exceptions.
    """

    message_template = "[{block.name}] {message}"

    def __init__(
        self,
        *handle_exceptions: Type[BaseException],
    ):
        self._common_exceptions = handle_exceptions
        self._block: Optional[Block] = None
        self._blocks_stack: List[Block] = []
        self._errors: defaultdict[str, List[str]] = defaultdict(list)

    def __call__(
        self, block: str, *handle_exceptions: Type[BaseException]
    ) -> "ErrorsContext":
        """
        Sets active block name

        :param block: human-readable block name
        :param handle_exceptions: additional Exception classes to handle in this block
        :return: self
        """
        self._block = Block(block, handle_exceptions)
        return self

    def __enter__(self) -> "ErrorsContext":
        if self._block is None:
            raise ErrorsContextError(
                "Active block is not set, cannot enter the context"
            )
        self._blocks_stack.append(self._block)
        self._block = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_val is not None and any(
                isinstance(exc_val, handled)
                for handled in (
                    self._common_exceptions + self._blocks_stack[-1].exceptions
                )
            ):
                self.error(f"{exc_val}")
                return True
        finally:
            self._blocks_stack.pop()

    def error(self, message) -> None:
        if not self._blocks_stack:
            raise ErrorsContextError("Cannot add error outside of block context")
        if self._block is not None:
            raise ErrorsContextError(
                "Block conflict: did you forget to enter the context after calling it?"
            )
        block = self._blocks_stack[-1]
        error_message = self.message_template.format(block=block, message=message)
        self._errors[block.name].append(error_message)
        self._on_error(error_message)

    def _on_error(self, message: str) -> None:
        print(message, file=sys.stderr)

    @property
    def blocks(self) -> List[str]:
        return list(self._errors.keys())

    @property
    def failed(self) -> bool:
        return bool(self._errors)

    @property
    def exit_code(self) -> int:
        return 1 if self.failed else 0

    def __int__(self):
        return self.exit_code
