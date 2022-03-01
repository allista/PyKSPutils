from pathlib import Path
from typing import Optional, cast

from git import Repo, Tag

from KSPUtils.errors_context import ErrorsContext
from KSPUtils.git_utils import get_repo, latest_tag
from KSPUtils.info_extractors.assembly_info import AssemblyInfo
from KSPUtils.info_extractors.file_extractor import StrPath
from KSPUtils.info_extractors.versions import AssemblyVersion, SimpleVersion, TagVersion
from KSPUtils.path_utils import get_search_paths
from KSPUtils.project_info.getters import (
    get_assembly_info,
    get_changelog_version,
    get_git_tag_version,
)


class CSharpProjectError(Exception):
    """An error during c# project info gathering"""


class CSharpProject:
    BLOCK_ASSEMBLY_INFO = "AssemblyInfo"
    BLOCK_CHANE_LOG = "ChangeLog"
    BLOCK_GIT = "Git"
    BLOCK_GIT_TAG = "Git tag"

    def __init__(
        self,
        path: StrPath,
        *search_paths: StrPath,
        change_log: str = "ChangeLog.md",
        errors_context: Optional[ErrorsContext] = None,
    ) -> None:
        self.path = Path(path)
        self.search_paths = get_search_paths(self.path, *search_paths)
        self.change_log_name = change_log
        self.context = errors_context or ErrorsContext(FileNotFoundError)
        self.assembly_info: Optional[AssemblyInfo] = None
        self.change_log_version: Optional[SimpleVersion] = None
        self.repo: Optional[Repo] = None
        self.latest_tag: Optional[Tag] = None
        self.git_tag_version: Optional[TagVersion] = None
        self.update_assembly_info()
        self.update_changelog_version()
        with self.context(self.BLOCK_GIT):
            self.repo = get_repo(self.path)
            if self.repo is None or self.repo.bare:
                self.error(f"Need non-bare git repo at {self.path}")
                self.repo = cast(Optional[Repo], None)
            elif self.repo.is_dirty():
                self.error(f"Repo is dirty at {self.path}")
        self.update_latest_tag()

    @property
    def assembly_version(self) -> Optional[AssemblyVersion]:
        return self.assembly_info.assembly_version if self.assembly_info else None

    def update_assembly_info(self) -> bool:
        with self.context(self.BLOCK_ASSEMBLY_INFO):
            self.assembly_info = get_assembly_info(*self.search_paths)
        return bool(self.assembly_info)

    def update_changelog_version(self) -> bool:
        with self.context(self.BLOCK_CHANE_LOG):
            self.change_log_version = get_changelog_version(
                self.change_log_name, *self.search_paths
            )
        return bool(self.change_log_version)

    def update_latest_tag(self):
        with self.context(self.BLOCK_GIT_TAG):
            if self.repo:
                self.latest_tag = latest_tag(self.repo)
                if self.latest_tag is not None:
                    try:
                        self.git_tag_version = get_git_tag_version(self.latest_tag)
                    except ValueError:
                        pass

    def error(self, message: str) -> None:
        self.context.error(message)
