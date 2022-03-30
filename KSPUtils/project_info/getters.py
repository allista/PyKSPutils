from pathlib import Path
from typing import Collection, Optional, Type

from git import Tag

from KSPUtils.info_extractors.assembly_info import AssemblyInfo
from KSPUtils.info_extractors.changelog import ChangeLog
from KSPUtils.info_extractors.file_extractor import FileExtractorType, StrPath
from KSPUtils.info_extractors.versions import ArchiveVersion, ExifVersion, TagVersion

_properties = Path("Properties")
_assembly_info = Path("AssemblyInfo.cs")


def _parse_from_paths(
    cls: Type[FileExtractorType], names: Collection[StrPath], paths: Collection[StrPath]
) -> Optional[FileExtractorType]:
    for p in paths:
        for name in names:
            path = Path(p) / name
            if path.is_file():
                return cls.from_file(path)
    names_combined = " or ".join(f"{n}" for n in names)
    paths_combined = "\n".join(f"{p}" for p in paths)
    raise FileNotFoundError(
        f"Unable to find\n{names_combined}\nwithin:\n{paths_combined}"
    )


def get_assembly_info(*paths: StrPath) -> Optional[AssemblyInfo]:
    """
    Returns AssemblyVersion from AssemblyInfo.cs file

    :param paths: paths to look for AssemblyInfo.cs file in
    :return: AssemblyVersion object
    :raise FileNotFoundError: if AssemblyInfo.cs file is not found
    """
    return _parse_from_paths(
        AssemblyInfo, [_assembly_info, _properties / _assembly_info], paths
    )


def get_changelog(name: str, *paths: StrPath) -> Optional[ChangeLog]:
    """
    Reads a text file from path and parses it as a ChangeLog

    :param name: filename of the changelog
    :param paths: paths where to search for the changelog file
    :return: The ChangeLog parsed from the file
    :raise FileNotFoundError: in case the file does not exist
    """
    return _parse_from_paths(ChangeLog, [name], paths)


def get_git_tag_version(tag: Tag) -> Optional[TagVersion]:
    """
    Creates TagVersion from a git Tag
    """
    return TagVersion.from_str(
        tag.name, date=tag.commit.authored_datetime, commit_sha=tag.commit.hexsha
    )


def get_dll_version(name: str, *paths: StrPath) -> Optional[ExifVersion]:
    """
    Creates ExifVersion from an assembly .dll

    :param name: filename of the changelog
    :param paths: paths where to search for the changelog file
    :return: The version extracted from .dll
    :raise FileNotFoundError: in case the file does not exist
    """
    return _parse_from_paths(ExifVersion, [name], paths)


def get_archive_version(
    name: str, path: StrPath, extension: str = ".zip"
) -> Optional[ArchiveVersion]:
    """
    Searches for a file with specified extension and filename
    that matches the archive naming scheme as defined by the :class:`ArchiveVersion`,
    with title equal to the provided name.

    :param name: The "name" part of the archive filename.
    :param path: The path to search for the archive in.
    :param extension: The ending of a file name to filter files by.
    :return: The ArchiveVersion of the found archive.
    :raises FileNotFoundError: If the archive was not found.
    """
    archive_version: Optional[ArchiveVersion] = None
    for filepath in Path(path).iterdir():
        if not filepath.name.endswith(extension):
            continue
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
