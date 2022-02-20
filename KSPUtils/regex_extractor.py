import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from re import Match
from typing import Any, Dict, Optional, Pattern, Tuple, Type, TypeVar, Union

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


RegexExtractorType = TypeVar("RegexExtractorType", bound="RegexExtractor")


@dataclass(frozen=True)
class RegexExtractor(FileExtractor):
    _re = re.compile("")

    @classmethod
    def _find_first(cls, regex: Pattern, text: str) -> Optional[Match]:
        return next(regex.finditer(text), None)

    @classmethod
    def _find_info(cls, text: str) -> Optional[Match]:
        return cls._find_first(cls._re, text)

    @classmethod
    def _extract(cls, match: Match) -> Dict[str, Any]:
        """Extract init kwargs for the Extractor instance from a Match"""
        raise NotImplementedError()

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
        cls: Type[RegexExtractorType], filename: Union[str, Path], **kwargs: Any
    ) -> Optional[RegexExtractorType]:
        """
        Creates RegexExtractor from a text file
        """
        text, mod_time = cls._read_path(filename)
        return cls.from_str(text, date=mod_time, **kwargs)
