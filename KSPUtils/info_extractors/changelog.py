from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Type

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


class ChangeLog(FileExtractor):
    """
    Extracts change log records and stores them
    in order and keyed by version
    """

    def __init__(
        self,
        filepath: Path,
        date: datetime = datetime.now(),
        header: str = "",
        entries: Optional[ChangeLogEntries] = None,
    ):
        super().__init__(filepath, date)
        self.header = header
        self._entries = entries or {}
        self._order: List[VersionBase] = sorted(entries, reverse=True)

    def __str__(self):
        res = [self.header] if self.header else []
        for version in self._entries:
            res += [f"## {version}", self._entries[version]]
        return "\n\n".join(res)

    def __getitem__(self, v: VersionBase) -> Optional[str]:
        return self._entries.get(v)

    def __setitem__(self, v: VersionBase, entry) -> None:
        if v not in self._entries:
            self._order.append(v)
            self._order.sort()
        self._entries[v] = entry

    @property
    def latest_version(self) -> Optional[ChangeLogVersion]:
        return next(iter(self._order), None)

    @property
    def latest_entry(self) -> Optional[str]:
        return self[self.latest_version]

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
            for line in inp:
                v = ChangeLogVersion.from_str(line, date=mod_time)
                if v:
                    entry_text = dedent("".join(entry)).rstrip("\n\r")
                    if version:
                        entries[version] = entry_text
                    else:
                        header = entry_text
                    version = v
                    entry = []
                else:
                    entry.append(line)
        return cls(filepath, mod_time, header, entries)
