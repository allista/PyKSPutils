from pathlib import Path
from typing import Union

from git import Tag

from KSPUtils.assembly_info import AssemblyInfo
from KSPUtils.versions import TagVersion

_properties = Path("Properties")
_assembly_info = Path("AssemblyInfo.cs")


def get_assembly_info(*paths: Union[str, Path]) -> AssemblyInfo:
    """
    Returns AssemblyVersion from AssemblyInfo.cs file

    :param paths: paths to look for AssemblyInfo.cs file in
    :return: AssemblyVersion object
    :raise ValueError: if AssemblyInfo.cs file is not found
    """
    for path in paths:
        base_path = Path(path)
        file_path = base_path / _assembly_info
        if not file_path.is_file():
            file_path = base_path / _properties / _assembly_info
        if not file_path.is_file():
            continue
        return AssemblyInfo.from_file(file_path)
    paths_combined = "\n".join(f"{p}" for p in paths)
    raise ValueError(f"Unable to find {_assembly_info} within:\n{paths_combined}")


def get_changelog_version(name: str, *paths: Union[str, Path]) -> TagVersion:
    """
    Reads a text file from path and returns the first TagVersion encountered
    inside.

    :param name: filename of the changelog
    :param paths: paths where to search for the changelog file
    :return: The first version encountered in the text of the changelog file
    :raise ValueError: in case the file does not exist
    """
    for p in paths:
        path = Path(p) / name
        if path.is_file():
            return TagVersion.from_file(path)
    paths_combined = "\n".join(f"{p}" for p in paths)
    raise ValueError(f"Unable to find {name} within:\n{paths_combined}")


def get_git_tag_version(tag: Tag) -> TagVersion:
    """
    Creates TagVersion from a git Tag
    """
    return TagVersion.from_str(
        tag.name, date=tag.commit.authored_datetime, commit_sha=tag.commit.hexsha
    )
