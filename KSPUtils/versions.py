"""
Provides several classes to parse and handle semantic versions
from various sources like git tags, changelogs and AssemblyInfo.cs files
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union

_T = TypeVar("_T", bound="VersionBase")

_VersionArgs = Dict[str, Optional[Union[int, str, datetime]]]


@dataclass(frozen=True, repr=False, eq=False)
class VersionBase:
    """Base class for semantic versions"""

    major: int
    minor: int
    build: Optional[int] = None
    revision: Optional[int] = None
    date: Optional[datetime] = None

    def __str__(self) -> str:
        short = f"v{self.major}.{self.minor}.{self.build or 0}"
        if self.revision is not None:
            return f"{short}.{self.revision}"
        return short

    def __repr__(self):
        if not self.date:
            return self.__str__()
        return f"{self!s} at {self.date:%Y-%m-%d %H:%M:%S %z}"

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
        self_build = self.build or 0
        other_build = other.build or 0
        return (
            self.major >= other.major
            and self.minor >= other.minor
            and self_build >= other_build
            and (self.revision or 0) >= (other.revision or 0)
        )

    def __gt__(self, other):
        return self >= other and self != other

    @classmethod
    def _parse(cls, text: str) -> _VersionArgs:
        raise NotImplementedError()

    @classmethod
    def from_str(
        cls: Type[_T], text: str, date: Optional[datetime] = None, **kwargs: Any
    ) -> _T:
        """Creates Version from string"""
        args = cls._parse(text)
        if date is not None:
            args["date"] = date
        args.update(kwargs)
        return cls(**args)

    @classmethod
    def from_file(cls: Type[_T], filename: Union[str, Path]) -> _T:
        """
        Creates Version from a file
        """
        filepath = Path(filename).resolve()
        mod_time = datetime.fromtimestamp(
            filepath.stat().st_mtime, timezone.utc
        ).astimezone()
        return cls.from_str(filepath.read_text("utf8"), mod_time)


@dataclass(frozen=True, repr=False, eq=False)
class RegexVersionBase(VersionBase):
    """
    Version info found in text using regex
    """

    _re = re.compile("")

    @classmethod
    def _parse(cls, text: str) -> _VersionArgs:
        """
        Create Version from text using regex
        """
        ver = next(cls._re.finditer(text), None)
        if ver is None:
            raise ValueError("Unable to find Version in the text")
        rev = ver.group("revision")
        return {
            "major": int(ver.group("major")),
            "minor": int(ver.group("minor")),
            "build": int(ver.group("build") or 0),
            "revision": int(rev) if rev else None,
        }


@dataclass(frozen=True, repr=False, eq=False)
class AssemblyVersion(RegexVersionBase):
    """
    Representation of AssemblyVersion info
    """

    title: Optional[str] = None

    _re = re.compile(
        r'\[assembly: +AssemblyVersion\("'
        r"(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<build>\d+)(\.(?P<revision>\d+))?)?"
        r'"\)]'
    )

    _title_re = re.compile(r"\[assembly: +AssemblyTitle\(\"(?P<title>.*)\"\)]")

    def __repr__(self):
        res = super().__repr__()
        if self.title:
            return f"{res} [{self.title}]"
        return res

    @classmethod
    def _parse(cls, text: str) -> _VersionArgs:
        args = super()._parse(text)
        match = next(cls._title_re.finditer(text), None)
        args["title"] = match.group("title") if match else None
        return args


@dataclass(frozen=True, repr=False, eq=False)
class TagVersion(RegexVersionBase):
    """
    Representation of a version from git tag
    """

    commit_sha: str = ""

    _re = re.compile(
        r"v(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<build>\d+)(\.(?P<revision>\d+))?)?"
    )

    def __repr__(self):
        res = super().__repr__()
        if self.commit_sha:
            return f"{res} on {self.commit_sha[:7]}"
        return res


@dataclass(frozen=True, repr=False, eq=False)
class KSPAssemblyVersion(AssemblyVersion):
    """
    Representation of KSPAssembly version info
    """

    _re = re.compile(
        r'\[assembly: +KSPAssembly\("\w+", +(?P<major>\d+), +(?P<minor>\d+)\)]'
    )

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}"


@dataclass(frozen=True, repr=False, eq=False)
class MinKSPVersion(RegexVersionBase):
    """
    Representation of a MinKSPVersion from AssemblyInfo.cs
    """

    _KSPVersion = r"KSPVersion *= *new Version\( *(?P<major>\d+) *, *(?P<minor>\d+) *(, *(?P<build>\d)+ *)?\) *;"

    _re = re.compile(r"\s*Min" + _KSPVersion)


@dataclass(frozen=True, repr=False, eq=False)
class MaxKSPVersion(MinKSPVersion):
    """
    Representation of a MaxKSPVersion from AssemblyInfo.cs
    """

    _re = re.compile(r"\s*Max" + MinKSPVersion._KSPVersion)


@dataclass(frozen=True, repr=False, eq=False)
class FilenameVersion(AssemblyVersion):
    """
    Representation of a version from file name
    """

    filename: str = ""

    _re = re.compile(
        r"v?(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<build>\d+)(\.(?P<revision>\d+))?)?"
    )

    _title_re = re.compile(r"^(?P<title>.*)-.*")

    @classmethod
    def from_file(cls: Type[_T], filename: Union[str, Path]) -> _T:
        """
        Creates Version from file name
        """
        filepath = Path(filename).resolve()
        mod_time = datetime.fromtimestamp(
            filepath.stat().st_mtime, timezone.utc
        ).astimezone()
        return cls.from_str(filepath.name, mod_time, filename=filepath.name)
