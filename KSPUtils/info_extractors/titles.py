import re
from dataclasses import dataclass
from typing import Any, Dict, Match, Optional

from KSPUtils.info_extractors.regex_extractor import RegexExtractor


@dataclass(frozen=True, repr=False)
class TitleExtractorBase(RegexExtractor):
    """Base class for extracting titles from various sources"""

    title: Optional[str] = None

    _re = re.compile(r"^(?P<title>.*)$")

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.__str__()

    @classmethod
    def _extract(cls, match: Match) -> Dict[str, Any]:
        return {"title": match.group("title")}


@dataclass(frozen=True, repr=False)
class AssemblyTitle(TitleExtractorBase):
    """Title of the Assembly as defined in the AssemblyInfo.cs text"""

    _re = re.compile(r"\[assembly: +AssemblyTitle\(\"(?P<title>.*)\"\)]")


@dataclass(frozen=True)
class FilenameTitle(TitleExtractorBase):
    _re = re.compile(r"^(?P<title>.*)-.*")
