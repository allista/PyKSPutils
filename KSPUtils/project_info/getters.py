from pathlib import Path
from typing import Collection, Type

from git import Tag

from KSPUtils.info_extractors.assembly_info import AssemblyInfo
from KSPUtils.info_extractors.file_extractor import FileExtractorType, StrPath
from KSPUtils.info_extractors.versions import ExifVersion, TagVersion

_properties = Path("Properties")
_assembly_info = Path("AssemblyInfo.cs")


def _version_from_paths(
    cls: Type[FileExtractorType], names: Collection[StrPath], paths: Collection[StrPath]
) -> FileExtractorType:
    for p in paths:
        for name in names:
            path = Path(p) / name
            if path.is_file():
                return cls.from_file(path)
    names_combined = " or ".join(f"{n}" for n in names)
    paths_combined = "\n".join(f"{p}" for p in paths)
    raise ValueError(f"Unable to find\n{names_combined}\nwithin:\n{paths_combined}")


def get_assembly_info(*paths: StrPath) -> AssemblyInfo:
    """
    Returns AssemblyVersion from AssemblyInfo.cs file

    :param paths: paths to look for AssemblyInfo.cs file in
    :return: AssemblyVersion object
    :raise ValueError: if AssemblyInfo.cs file is not found
    """
    return _version_from_paths(
        AssemblyInfo, [_assembly_info, _properties / _assembly_info], paths
    )


def get_changelog_version(name: str, *paths: StrPath) -> TagVersion:
    """
    Reads a text file from path and returns the first TagVersion encountered
    inside.

    :param name: filename of the changelog
    :param paths: paths where to search for the changelog file
    :return: The first version encountered in the text of the changelog file
    :raise ValueError: in case the file does not exist
    """
    return _version_from_paths(TagVersion, [name], paths)


def get_git_tag_version(tag: Tag) -> TagVersion:
    """
    Creates TagVersion from a git Tag
    """
    return TagVersion.from_str(
        tag.name, date=tag.commit.authored_datetime, commit_sha=tag.commit.hexsha
    )
