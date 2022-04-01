import re
from dataclasses import dataclass
from typing import Any, Dict, Match, Optional, Type

from KSPUtils.info_extractors.file_extractor import StrPath
from KSPUtils.info_extractors.regex_extractor import RegexExtractor, RegexExtractorType


@dataclass(frozen=True, repr=False)
class TitleExtractorBase(RegexExtractor):
    """Base class for extracting titles from various sources"""

    title: Optional[str] = None

    _re = re.compile(r"^(?P<title>.*)$")

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.__str__()

    def __bool__(self):
        return bool(self.title)

    @classmethod
    def _extract(cls, match: Match) -> Dict[str, Any]:
        return {"title": match.group("title")}

    @classmethod
    def _as_str(cls, instance: Optional["TitleExtractorBase"]) -> Optional[str]:
        return instance.title if instance else None

    @classmethod
    def from_str_as_str(cls, text: str) -> Optional[str]:
        return cls._as_str(cls.from_str(text))

    @classmethod
    def from_file_as_str(cls, filename: StrPath) -> Optional[str]:
        return cls._as_str(cls.from_file(filename))


@dataclass(frozen=True, repr=False)
class AssemblyTitle(TitleExtractorBase):
    """Title of the Assembly as defined in the AssemblyInfo.cs text"""

    _re = re.compile(r"\[assembly: +AssemblyTitle\(\"(?P<title>.*)\"\)]")


@dataclass(frozen=True, repr=False)
class FilenameTitle(TitleExtractorBase):
    """Just a file name without the last extension"""

    _re = re.compile(r"^(?P<title>.*)\..*")

    @classmethod
    def from_file(
        cls: Type[RegexExtractorType], filename: StrPath, **kwargs: Any
    ) -> Optional[RegexExtractorType]:
        filepath, _ = cls._resolve_path(filename)
        return cls.from_str(filepath.name, **kwargs)


@dataclass(frozen=True, repr=False)
class ArchiveTitle(FilenameTitle):
    """The name of a file before the last dash"""

    _re = re.compile(r"^(?P<title>.*)-.*")
