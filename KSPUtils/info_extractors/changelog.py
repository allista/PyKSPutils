from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Type

from KSPUtils.file_saver_mixin import FileSaverMixin
from KSPUtils.info_extractors.file_extractor import (
    FileExtractor,
    FileExtractorType,
    StrPath,
)
from KSPUtils.info_extractors.versions import (
    ChangeLogVersion,
    VersionBase,
)

ChangeLogEntries = Dict[VersionBase, str]


def _combine_entry(entry: List[str]) -> str:
    return dedent("".join(entry)).strip("\n\r\t ")


class ChangeLog(FileSaverMixin, FileExtractor):
    """
    Extracts change log records and stores them
    in order and keyed by version
    """

    def __init__(
        self,
        filepath: Path,
        header: str = "",
        entries: Optional[ChangeLogEntries] = None,
    ):
        super().__init__(filepath)
        self.header = header
        self._entries = entries or {}
        self._order: List[VersionBase] = sorted(self._entries, reverse=True)

    def __str__(self):
        res = [self.header] if self.header else []
        for version in self._order:
            res.append(f"## {version}")
            entry = self._entries[version]
            if entry:
                res.append(entry)
        return "\n\n".join(res)

    def __getitem__(self, v: Optional[VersionBase]) -> Optional[str]:
        return self._entries.get(v) if v is not None else None

    def __setitem__(self, v: VersionBase, entry) -> None:
        if v not in self._entries:
            self._order.append(v)
            self._order.sort(reverse=True)
        self._entries[v] = entry
        self._dirty = True

    @property
    def latest_version(self) -> Optional[VersionBase]:
        return next(iter(self._order), None)

    @property
    def latest_entry(self) -> Optional[str]:
        return self[self.latest_version]

    @property
    def has_changed(self):
        return str(self) != self.get_original_text()

    def get_original_text(self) -> Optional[str]:
        if self.filepath.is_file():
            return self.filepath.read_text(encoding="utf8")
        return None

    @classmethod
    def from_file(
        cls: Type[FileExtractorType], filename: StrPath, **kwargs: Any
    ) -> Optional[FileExtractorType]:
        filepath, mod_time = cls._resolve_path(filename)
        header = ""
        entries: ChangeLogEntries = {}
        with filepath.open("rt", encoding="utf8") as inp:
            version: Optional[ChangeLogVersion] = None
            entry: List[str] = []
            for i, line in enumerate(inp):
                v = ChangeLogVersion.from_str(line, date=mod_time)
                if v:
                    if version:
                        if version in entries:
                            raise ValueError(
                                f"Duplicate entry: '{version}' in {filepath}:{i+1}"
                            )
                        entries[version] = _combine_entry(entry)
                    else:
                        header = _combine_entry(entry)
                    version = v
                    entry = []
                else:
                    entry.append(line)
            if version:
                if version not in entries:
                    entries[version] = _combine_entry(entry)
            elif not header and entry:
                header = _combine_entry(entry)
        return cls(filepath=filepath, header=header, entries=entries)
