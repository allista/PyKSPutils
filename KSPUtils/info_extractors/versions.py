"""
Provides several classes to parse and handle semantic versions
from various sources like git tags, changelogs and AssemblyInfo.cs files
"""

import re
from dataclasses import dataclass
from datetime import datetime
from subprocess import CalledProcessError, check_output
from typing import Any, Dict, Match, Optional, Type, TypeVar

from KSPUtils.info_extractors.file_extractor import StrPath
from KSPUtils.info_extractors.regex_extractor import RegexExtractor, RegexExtractorType
from KSPUtils.info_extractors.titles import ArchiveTitle, FilenameTitle


VersionBaseType = TypeVar("VersionBaseType", bound="VersionBase")


@dataclass(frozen=True, repr=False, eq=False)
class VersionBase:
    """Base class for semantic versions"""

    major: int
    minor: int
    build: Optional[int] = None
    revision: Optional[int] = None
    date: Optional[datetime] = None

    @classmethod
    def clone(
        cls: Type[VersionBaseType], other: "VersionBase", **kwargs: Any
    ) -> VersionBaseType:
        args = other.__dict__.copy()
        args.update(kwargs)
        return cls(**args)

    @property
    def as_str_without_prefix(self):
        short = f"{self.major}.{self.minor}.{self.build or 0}"
        if self.revision is not None:
            return f"{short}.{self.revision}"
        return short

    def __str__(self) -> str:
        return f"v{self.as_str_without_prefix}"

    def __repr__(self):
        if not self.date:
            return self.__str__()
        return f"{self!s} at {self.date:%Y-%m-%d %H:%M:%S %z}"

    def __hash__(self):
        return hash((self.major, self.minor, self.build or 0, self.revision or 0))

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, VersionBase)
            and self.major == other.major
            and self.minor == other.minor
            and (self.build or 0) == (other.build or 0)
            and (self.revision or 0) == (other.revision or 0)
        )

    def __ge__(self, other):
        if not isinstance(other, VersionBase):
            return False
        if self.major > other.major:
            return True
        if self.major == other.major:
            if self.minor > other.minor:
                return True
            if self.minor == other.minor:
                self_build = self.build or 0
                other_build = other.build or 0
                if self_build > other_build:
                    return True
                if self_build == other_build:
                    self_revision = self.revision or 0
                    other_revision = other.revision or 0
                    if self_revision > other_revision:
                        return True
                    if self_revision == other_revision:
                        return True
        return False

    def __gt__(self, other):
        return self >= other and self != other

    def __lt__(self, other):
        if not isinstance(other, VersionBase):
            return False
        return not self >= other

    def __le__(self, other):
        return self < other or self == other


@dataclass(frozen=True, repr=False, eq=False)
class RegexVersionBase(VersionBase, RegexExtractor):
    """
    Version info found in text using regex
    """

    _re = re.compile(
        r"(?P<version>(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<build>\d+)(\.(?P<revision>\d+))?)?)"
    )

    @classmethod
    def _extract(cls: Type[RegexExtractorType], match: Match) -> Dict[str, Any]:
        rev = match.group("revision")
        return {
            "major": int(match.group("major")),
            "minor": int(match.group("minor")),
            "build": int(match.group("build") or 0),
            "revision": int(rev) if rev else None,
        }


@dataclass(frozen=True, repr=False, eq=False)
class AssemblyVersion(RegexVersionBase):
    """
    Representation of AssemblyVersion info
    """

    _re = re.compile(
        r'\[assembly: +AssemblyVersion\("' + RegexVersionBase._re.pattern + r'"\)]'
    )


@dataclass(frozen=True, repr=False, eq=False)
class SimpleVersion(RegexVersionBase):
    """
    Representation of a simple version
    """

    _re = re.compile(f"v?{RegexVersionBase._re.pattern}")


@dataclass(frozen=True, repr=False, eq=False)
class ChangeLogVersion(RegexVersionBase):
    """
    Representation a version from a change log file
    """

    title: str = ""

    _re = re.compile(
        r"^[#*]*\s*"
        + f"[_*]*v{RegexVersionBase._re.pattern}[_*]*"
        + r"\s*(?P<title>.+)?$"
    )

    def __str__(self):
        short = super().__str__()
        if self.title:
            return f"{short} {self.title}"
        return short

    @classmethod
    def _extract(cls: Type[RegexExtractorType], match: Match) -> Dict[str, Any]:
        kwargs = super()._extract(match)  # type: ignore[misc]
        title = match.group("title")
        if title:
            kwargs["title"] = title
        return kwargs


@dataclass(frozen=True, repr=False, eq=False)
class TagVersion(RegexVersionBase):
    """
    Representation of a version from git tag
    """

    _re = re.compile(f"^v{RegexVersionBase._re.pattern}$")

    commit_sha: str = ""

    def __repr__(self):
        res = super().__repr__()
        if self.commit_sha:
            return f"{res} on {self.commit_sha[:7]}"
        return res


@dataclass(frozen=True, repr=False, eq=False)
class KSPAssemblyVersion(RegexVersionBase):
    """
    Representation of KSPAssembly version info
    """

    _re = re.compile(
        r'\[assembly: +KSPAssembly\("\w+", +(?P<version>(?P<major>\d+), +(?P<minor>\d+))\)]'
    )

    @classmethod
    def _extract(cls, match: Match) -> Dict[str, Any]:
        return {
            "major": int(match.group("major")),
            "minor": int(match.group("minor")),
        }

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}"


@dataclass(frozen=True, repr=False, eq=False)
class MinKSPVersion(RegexVersionBase):
    """
    Representation of a MinKSPVersion from AssemblyInfo.cs
    """

    _KSPVersion_pattern = (
        r"KSPVersion *= *new Version\( *"
        r"(?P<version>(?P<major>\d+) *, *(?P<minor>\d+) *(, *(?P<build>\d)+ *)?)"
        r"\) *;"
    )

    _re = re.compile(r"\s*Min" + _KSPVersion_pattern)

    @classmethod
    def _extract(cls, match: Match) -> Dict[str, Any]:
        return {
            "major": int(match.group("major")),
            "minor": int(match.group("minor")),
            "build": int(match.group("build") or 0),
        }


@dataclass(frozen=True, repr=False, eq=False)
class MaxKSPVersion(MinKSPVersion):
    """
    Representation of a MaxKSPVersion from AssemblyInfo.cs
    """

    _re = re.compile(r"\s*Max" + MinKSPVersion._KSPVersion_pattern)


@dataclass(frozen=True, repr=False, eq=False)
class FilenameVersion(SimpleVersion):
    """
    Representation of a version from file name
    """

    title: str = ""
    filename: str = ""
    filepath: StrPath = ""

    def __repr__(self):
        return f"{super().__repr__()} [{self.title}] {self.filename}"

    @classmethod
    def from_file(
        cls: Type[RegexExtractorType],
        filename: StrPath,
        **kwargs: Any,
    ) -> Optional[RegexExtractorType]:
        """
        Creates Version from file name
        """
        filepath, mod_time = cls._resolve_path(filename)
        kwargs.setdefault("title", filepath.name)
        return cls.from_str(
            filepath.name,
            date=mod_time,
            filename=filepath.name,
            filepath=filepath,
            **kwargs,
        )


@dataclass(frozen=True, repr=False, eq=False)
class ArchiveVersion(FilenameVersion):
    """
    Representation of a version from a mod archive
    """

    @classmethod
    def from_file(
        cls: Type[RegexExtractorType],
        filename: StrPath,
        **kwargs: Any,
    ) -> RegexExtractorType:
        return super().from_file(  # type: ignore[misc]
            filename, title=ArchiveTitle.from_file_as_str(filename)
        )


@dataclass(frozen=True, repr=False, eq=False)
class ExifVersion(FilenameVersion):
    """
    Representation of a version from exiftool output
    """

    _re = re.compile(r"Product Version\s+: " + RegexVersionBase.pattern())

    @classmethod
    def from_file(
        cls: Type[RegexExtractorType], filename: StrPath, **kwargs: Any
    ) -> Optional[RegexExtractorType]:
        filepath, mod_time = cls._resolve_path(filename)
        try:
            output = check_output(f"exiftool {filepath}", shell=True).decode("utf8")
        except CalledProcessError as e:
            print(f"{e}")
            return None
        return cls.from_str(
            output,
            title=FilenameTitle.from_str_as_str(filepath.name),
            filename=filepath.name,
            filepath=filepath,
            date=mod_time,
            **kwargs,
        )


@dataclass(frozen=True, repr=False, eq=False)
class KspReadmeVersion(RegexVersionBase):
    """KSP version from readme.txt file"""

    _re = re.compile(f"^Version {RegexVersionBase._re.pattern}$")
