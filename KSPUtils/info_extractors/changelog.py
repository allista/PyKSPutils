from textwrap import dedent
from typing import Any, Dict, List, Optional, Type

from KSPUtils.info_extractors.file_extractor import (
    FileExtractor,
    FileExtractorType,
    StrPath,
)
from KSPUtils.info_extractors.versions import SimpleVersion

ChangeLogEntries = Dict[SimpleVersion, str]


class ChangeLog(FileExtractor):
    """
    Extracts change log records and stores them
    in order and keyed by version
    """

    def __init__(
        self,
        header: str = "",
        entries: Optional[ChangeLogEntries] = None,
    ):
        self.header = header
        self.entries: ChangeLogEntries = (
            {v: entries[v] for v in sorted(entries, reverse=True)} if entries else {}
        )

    def __str__(self):
        res = [self.header] if self.header else []
        for version in self.entries:
            res += [f"## {version}", self.entries[version]]
        return "\n\n".join(res)

    @classmethod
    def from_file(
        cls: Type[FileExtractorType], filename: StrPath, **kwargs: Any
    ) -> Optional[FileExtractorType]:
        filepath, mod_time = cls._resolve_path(filename)
        header = ""
        entries: ChangeLogEntries = {}
        with filepath.open("rt", encoding="utf8") as inp:
            version: Optional[SimpleVersion] = None
            entry: List[str] = []
            for line in inp:
                v = SimpleVersion.from_str(line, date=mod_time)
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
        return cls(header, entries)
