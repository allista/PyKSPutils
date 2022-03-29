import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Type, TypeVar

logger = logging.getLogger(__name__)


class ErrorsContextError(Exception):
    """Bad usage of ErrorsContext"""


@dataclass
class Block:
    name: str
    exceptions: Tuple[Type[BaseException]]
    optional: bool = False


ErrorsContextType = TypeVar("ErrorsContextType", bound="ErrorsContext")

OnErrorHandler = Callable[[str, int], None]


class ErrorsContext:
    """
    Utility context that keeps registry of errors occurred within it,
    keyed by block name.

    It can also handle exceptions.
    """

    message_template = "[{block.name}] {message}"
    logger = logger

    def __init__(
        self,
        *handle_exceptions: Type[BaseException],
        on_error: Optional[OnErrorHandler] = None
    ):
        self._common_exceptions = handle_exceptions
        self._block: Optional[Block] = None
        self._blocks_stack: List[Block] = []
        self._errors: defaultdict[str, List[str]] = defaultdict(list)
        self.on_error: Optional[OnErrorHandler] = on_error

    def __call__(
        self, block: str, *handle_exceptions: Type[BaseException]
    ) -> ErrorsContextType:
        """
        Sets active block name

        :param block: human-readable block name
        :param handle_exceptions: additional Exception classes to handle in this block
        :return: self
        """
        self._block = Block(block, handle_exceptions)
        return self

    def __enter__(self) -> ErrorsContextType:
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

    @property
    def optional(self) -> ErrorsContextType:
        if self._block is None:
            raise ErrorsContextError("Active block is not set")
        self._block.optional = True
        return self

    def error(self, message) -> None:
        if not self._blocks_stack:
            raise ErrorsContextError("Cannot add error outside of block context")
        if self._block is not None:
            raise ErrorsContextError(
                "Block conflict: did you forget to enter the context after calling it?"
            )
        block = self._blocks_stack[-1]
        error_message = self.message_template.format(block=block, message=message)
        if block.optional:
            self._on_warning(error_message)
        else:
            self._errors[block.name].append(error_message)
            self._on_error(error_message)

    def _on_error(self, message: str) -> None:
        self.logger.error(message)
        if self.on_error is not None:
            self.on_error(message, self.exit_code)

    def _on_warning(self, message: str) -> None:
        self.logger.warning(message)

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
