import re
from dataclasses import dataclass
from re import Match
from typing import Any, ClassVar, Dict, Optional, Pattern, Type, TypeVar, Union

from KSPUtils.info_extractors.file_extractor import FileExtractor, StrPath

RegexExtractorType = TypeVar("RegexExtractorType", bound="RegexExtractor")
GroupType = Union[str, int]


@dataclass(frozen=True)
class RegexExtractor(FileExtractor):
    _re: ClassVar[Pattern] = re.compile("")

    @classmethod
    def pattern(cls):
        return cls._re.pattern

    @classmethod
    def _find_first(cls, regex: Pattern, text: str) -> Optional[Match]:
        return next(regex.finditer(text), None)

    @classmethod
    def _find_info(cls, text: str) -> Optional[Match]:
        return cls._find_first(cls._re, text)

    @classmethod
    def _extract(cls: Type[RegexExtractorType], match: Match) -> Dict[str, Any]:
        """Extract init kwargs for the Extractor instance from a Match"""
        raise NotImplementedError()

    @classmethod
    def replace(cls, text: str, replacement: str, group: GroupType = 0) -> str:
        match = cls._find_info(text)
        if not match:
            return text
        orig = match.group(group)
        if not orig:
            return text
        return text.replace(orig, replacement)

    @classmethod
    def from_str(
        cls: Type[RegexExtractorType], text: str, **kwargs: Any
    ) -> Optional[RegexExtractorType]:
        match = cls._find_info(text)
        if not match:
            return None
        data = cls._extract(match)
        data.update(kwargs)
        # noinspection PyArgumentList
        # the _extract method is supposed to return the kwargs for its cls
        return cls(**data)

    @classmethod
    def from_file(
        cls: Type[RegexExtractorType], filename: StrPath, **kwargs: Any
    ) -> Optional[RegexExtractorType]:
        """
        Creates RegexExtractor from a text file
        """
        text, mod_time = cls._read_path(filename)
        return cls.from_str(text, date=mod_time, **kwargs)

    @classmethod
    def from_file_lines(
        cls: Type[RegexExtractorType], filename: StrPath, **kwargs: Any
    ) -> Optional[RegexExtractorType]:
        """
        Creates RegexExtractor from a text file,
        reading line by line until the match is found.

        Useful for large files, or for files with incorrectly encoded data.
        """
        filepath, mod_time = cls._resolve_path(filename)
        with filepath.open("rb") as inp:
            for line in inp:
                try:
                    res = cls.from_str(line.decode("utf8"), date=mod_time, **kwargs)
                    if res:
                        return res
                except UnicodeDecodeError:
                    continue
        return None
