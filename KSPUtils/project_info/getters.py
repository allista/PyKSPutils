from pathlib import Path
from typing import Collection, Optional, Type

from git import Tag

from KSPUtils.info_extractors.assembly_info import AssemblyInfo
from KSPUtils.info_extractors.file_extractor import FileExtractorType, StrPath
from KSPUtils.info_extractors.versions import ArchiveVersion, SimpleVersion, ExifVersion, TagVersion

_properties = Path("Properties")
_assembly_info = Path("AssemblyInfo.cs")


def _parse_from_paths(
    cls: Type[FileExtractorType], names: Collection[StrPath], paths: Collection[StrPath]
) -> FileExtractorType:
    for p in paths:
        for name in names:
            path = Path(p) / name
            if path.is_file():
                return cls.from_file(path)
    names_combined = " or ".join(f"{n}" for n in names)
    paths_combined = "\n".join(f"{p}" for p in paths)
    raise FileNotFoundError(f"Unable to find\n{names_combined}\nwithin:\n{paths_combined}")


def get_assembly_info(*paths: StrPath) -> AssemblyInfo:
    """
    Returns AssemblyVersion from AssemblyInfo.cs file

    :param paths: paths to look for AssemblyInfo.cs file in
    :return: AssemblyVersion object
    :raise FileNotFoundError: if AssemblyInfo.cs file is not found
    """
    return _parse_from_paths(
        AssemblyInfo, [_assembly_info, _properties / _assembly_info], paths
    )


def get_changelog_version(name: str, *paths: StrPath) -> SimpleVersion:
    """
    Reads a text file from path and returns the first TagVersion encountered
    inside.

    :param name: filename of the changelog
    :param paths: paths where to search for the changelog file
    :return: The first version encountered in the text of the changelog file
    :raise FileNotFoundError: in case the file does not exist
    """
    return _parse_from_paths(SimpleVersion, [name], paths)


def get_git_tag_version(tag: Tag) -> TagVersion:
    """
    Creates TagVersion from a git Tag
    """
    return TagVersion.from_str(
        tag.name, date=tag.commit.authored_datetime, commit_sha=tag.commit.hexsha
    )


def get_dll_version(name: str, *paths: StrPath) -> ExifVersion:
    """
    Creates ExifVersion from an assembly .dll

    :param name: filename of the changelog
    :param paths: paths where to search for the changelog file
    :return: The version extracted from .dll
    :raise FileNotFoundError: in case the file does not exist
    """
    return _parse_from_paths(ExifVersion, [name], paths)


def get_archive_version(name: str, path: StrPath) -> ArchiveVersion:
    archive_version: Optional[ArchiveVersion] = None
    for filepath in Path(path).iterdir():
        try:
            file_version = ArchiveVersion.from_file(filepath)
        except FileNotFoundError:
            continue
        if (
            file_version
            and file_version.title == name
            and (not archive_version or archive_version < file_version)
        ):
            archive_version = file_version
    if not archive_version:
        raise FileNotFoundError(f"Unable to find archive for {name} within {path}")
    return archive_version
