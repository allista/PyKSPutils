from pathlib import Path
from textwrap import indent
from typing import List, Optional, cast

from git import Repo, Tag
from github import Github

from KSPUtils.errors_context import ErrorsContext, OnErrorHandler
from KSPUtils.git_utils import get_repo, latest_tag
from KSPUtils.github_utils import GithubError, get_github
from KSPUtils.info_extractors.assembly_info import AssemblyInfo
from KSPUtils.info_extractors.changelog import ChangeLog
from KSPUtils.info_extractors.file_extractor import StrPath
from KSPUtils.info_extractors.versions import (
    ArchiveVersion,
    AssemblyVersion,
    ExifVersion,
    SimpleVersion,
    TagVersion,
)
from KSPUtils.path_utils import get_search_paths
from KSPUtils.project_info.getters import (
    get_archive_version,
    get_assembly_info,
    get_changelog,
    get_git_tag_version,
)
from KSPUtils.project_info.mod_config import ModConfig


class CSharpProjectError(Exception):
    """An error during c# project info gathering"""


class CSharpProject:
    BLOCK_MOD_CONFIG = "Mod config"
    BLOCK_ASSEMBLY_INFO = "AssemblyInfo"
    BLOCK_CHANE_LOG = "ChangeLog"
    BLOCK_GIT = "Git"
    BLOCK_GIT_TAG = "Git tag"
    BLOCK_ARCHIVE = "Archive"
    BLOCK_GITHUB = "GitHub"

    def __init__(
        self,
        path: StrPath,
        errors_context: Optional[ErrorsContext] = None,
    ) -> None:
        self.path = Path(path)
        self.search_paths = []
        self.context = errors_context or ErrorsContext(FileNotFoundError)
        self.mod_config: Optional[ModConfig] = None
        self.assembly_info: Optional[AssemblyInfo] = None
        self.change_log: Optional[ChangeLog] = None
        self.dll_version: Optional[ExifVersion] = None
        self.archive_version: Optional[ArchiveVersion] = None
        self.github: Optional[Github] = None
        self.repo: Optional[Repo] = None
        self.latest_tag: Optional[Tag] = None
        self.git_tag_version: Optional[TagVersion] = None
        self._loaded = False

    def load(self, force=False, on_error: Optional[OnErrorHandler] = None) -> None:
        if self._loaded and not force:
            return
        if on_error is not None:
            self.context.on_error = on_error
        self.update_mod_config()
        self.update_assembly_info()
        self.update_changelog()
        with self.context(self.BLOCK_GIT):
            self.repo = get_repo(self.path)
            if self.repo is None or self.repo.bare:
                self.error(f"Need non-bare git repo at {self.path}")
                self.repo = cast(Optional[Repo], None)
            elif self.repo.is_dirty():
                self.error(f"Repo is dirty at {self.path}")
        self.update_latest_tag()
        self.update_dll_version()
        self.update_archive_version()
        self._loaded = True

    def _secondary_versions(self, dll=True, archive=True) -> List[str]:
        versions = [
            f"ChangeLog: {self.change_log_version!r}",
            f"Git tag:   {self.git_tag_version!r}",
        ]
        if dll:
            versions.append(f"DLL:       {self.dll_version!r}")
        if archive:
            versions.append(f"Archive:   {self.archive_version!r}")
        return versions

    def __str__(self) -> str:
        return "\n".join(
            (
                f"Assembly Info:",
                indent(f"{self.assembly_info}", "  "),
                *self._secondary_versions(),
            )
        )

    def versions_info(self, *, dll=True, archive=True):
        return "\n".join(
            (
                f"Assembly:  {self.change_log_version!r}",
                *self._secondary_versions(dll, archive),
            )
        )

    @property
    def assembly_version(self) -> Optional[AssemblyVersion]:
        return self.assembly_info.assembly_version if self.assembly_info else None

    @property
    def assembly_title(self) -> Optional[str]:
        return (
            self.assembly_info.title.title
            if self.assembly_info and self.assembly_info.title
            else None
        )

    @property
    def change_log_name(self) -> str:
        return self.mod_config.change_log

    @property
    def change_log_version(self) -> Optional[SimpleVersion]:
        return self.change_log.latest_version if self.change_log else None

    def versions_match(
        self, *, change_log=True, git_tag=True, dll=True, archive=True
    ) -> bool:
        v = self.assembly_version
        return (
            v is not None
            and (not change_log or v == self.change_log_version)
            and (not git_tag or v == self.git_tag_version)
            and (not dll or v == self.dll_version)
            and (not archive or v == self.archive_version)
        )

    def update_mod_config(self):
        with self.context(self.BLOCK_MOD_CONFIG):
            self.mod_config = ModConfig.default(self.path)
            self.search_paths = get_search_paths(
                self.path, *self.mod_config.search_paths
            )

    def update_assembly_info(self) -> bool:
        with self.context(self.BLOCK_ASSEMBLY_INFO):
            self.assembly_info = get_assembly_info(*self.search_paths)
        return bool(self.assembly_info)

    def update_changelog(self) -> bool:
        with self.context(self.BLOCK_CHANE_LOG):
            self.change_log = get_changelog(self.change_log_name, *self.search_paths)
        return bool(self.change_log)

    def update_latest_tag(self):
        with self.context(self.BLOCK_GIT_TAG):
            if self.repo:
                self.latest_tag = latest_tag(self.repo)
                if self.latest_tag is not None:
                    try:
                        self.git_tag_version = get_git_tag_version(self.latest_tag)
                    except ValueError:
                        pass

    def update_dll_version(self) -> bool:
        if not self.mod_config.dll_path:
            return False
        with self.context(self.BLOCK_MOD_CONFIG).optional:
            self.dll_version = ExifVersion.from_file(self.mod_config.dll_path)
        return bool(self.dll_version)

    def update_archive_version(self) -> bool:
        if not self.assembly_title or not self.mod_config.archive_path:
            return False
        with self.context(self.BLOCK_ARCHIVE).optional:
            self.archive_version = get_archive_version(
                self.assembly_title, self.mod_config.archive_path
            )
        return bool(self.archive_version)

    def update_github(self) -> bool:
        with self.context(self.BLOCK_GITHUB, GithubError):
            self.github = get_github(".")
        return bool(self.github)

    def error(self, message: str) -> None:
        self.context.error(message)
