from functools import reduce
from functools import reduce
from typing import Callable, Dict, List, Optional, Type

from KSPUtils.errors_context import ErrorsContext, ErrorsContextError

OnErrorHandler = Callable[[str, int], None]


class ExitCodeContextError(ErrorsContextError):
    """Bad usage of ExitCodeContextError"""


class ExitCodeContext(ErrorsContext):
    """
    Utility context that automatically creates meaningful exit code
    from errors occurring within it.

    Can also handle exceptions.
    """

    def __init__(
        self,
        *handle_exceptions: Type[BaseException],
        block_ids: Optional[Dict[str, int]] = None,
        on_error: Optional[OnErrorHandler] = None,
    ):
        super().__init__(*handle_exceptions, on_error=on_error)
        self._block_ids: Dict[str, int] = block_ids or {}

    def __call__(
        self,
        block: str,
        *handle_exceptions: Type[BaseException],
        block_id: Optional[int] = None,
    ) -> "ExitCodeContext":
        """
        Updates block name and ID

        :param block: human-readable block name
        :param block_id: integer block ID, should be in [0, 7] interval
        :return: ExecutionContext instance, self
        """
        existing_block_id = self._block_ids.get(
            block, len(self._block_ids) if block_id is None else block_id
        )
        if not (0 <= existing_block_id <= 7):
            raise ExitCodeContextError("ExitCodeContext: block id should be in [0, 7]")
        if block_id is not None and existing_block_id != block_id:
            raise ExitCodeContextError(
                f"ExitCodeContext: block id {block_id} differs from the existing block {block}[{existing_block_id}]"
            )
        self._block_ids[block] = existing_block_id
        super().__call__(block, *handle_exceptions)
        return self

    @property
    def exit_code(self) -> int:
        return reduce(lambda r, b: r | 1 << self._block_ids[b], self._errors, 0)

    @property
    def blocks(self) -> List[str]:
        return list(self._block_ids.keys())
