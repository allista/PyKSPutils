from pathlib import Path
from typing import Any


class FileSaverMixin:
    def __init__(self, filepath: Path, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.filepath = filepath
        self._dirty = False

    @property
    def is_dirty(self):
        return self._dirty

    def save(self):
        with self.filepath.open("wt", encoding="utf8") as out:
            out.write(str(self))
        self._dirty = False
