from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, Union

StrPath = Union[str, Path]


class FileExtractor:
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
