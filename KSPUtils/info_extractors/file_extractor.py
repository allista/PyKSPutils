from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Tuple, Type, TypeVar, Union

StrPath = Union[str, Path]

FileExtractorType = TypeVar("FileExtractorType", bound="FileExtractor")


class FileExtractor:
    def __init__(self, **kwargs: Any) -> None:
        # pylint: disable=useless-super-delegation
        super().__init__(**kwargs)

    @classmethod
    def _resolve_path(cls, filename: StrPath) -> Tuple[Path, datetime]:
        filepath = Path(filename).resolve()
        mod_time = datetime.fromtimestamp(
            filepath.stat().st_mtime, timezone.utc
        ).astimezone()
        return filepath, mod_time

    @classmethod
    def _read_path(cls, filename: StrPath) -> Tuple[str, datetime]:
        filepath, mod_time = cls._resolve_path(filename)
        return filepath.read_text("utf8"), mod_time

    @classmethod
    def from_file(
        cls: Type[FileExtractorType], filename: StrPath, **kwargs: Any
    ) -> Optional[FileExtractorType]:
        raise NotImplementedError()
