import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, cast

import click
from git import Repo, Tag

from KSPUtils.git_utils import get_repo, latest_tag
from KSPUtils.project_info import (
    get_assembly_version,
    get_changelog_version,
    get_git_tag_version,
)
from KSPUtils.versions import AssemblyVersion, FilenameVersion, TagVersion
from .execution_context import ExecutionContext
from .utils import get_search_paths


def on_error(message: str, _exit_code: int) -> None:
    click.echo(message, err=True)


@dataclass
class VersionContext:
    cwd: Path
    context: ExecutionContext
    search_paths: List[Path]
    repo: Optional[Repo] = None
    tag: Optional[Tag] = None
    assembly_version: Optional[AssemblyVersion] = None
    change_log_version: Optional[TagVersion] = None
    git_tag_version: Optional[TagVersion] = None


@click.group()
@click.option(
    "--change-log",
    default="ChangeLog.md",
    type=click.Path(),
    show_default=True,
    help="Path to the changelog file where to search for the version",
)
@click.option(
    "--add-search-path",
    multiple=True,
    default=[],
    help="Additional paths to search for project sources",
)
@click.pass_context
def cmd(ctx: click.Context, change_log: str, add_search_path: List[str]):
    cwd = Path.cwd()
    context = ExecutionContext(on_error, ValueError)
    search_paths = get_search_paths(cwd, *add_search_path)
    # noinspection PyUnusedLocal
    # because context can handle exceptions
    assembly_version: Optional[AssemblyVersion] = None
    with context("AssemblyInfo", 1):
        assembly_version = get_assembly_version(*search_paths)
    # noinspection PyUnusedLocal
    # because context can handle exceptions
    change_log_version: Optional[TagVersion] = None
    with context("ChangeLog", 2):
        change_log_version = get_changelog_version(change_log, *search_paths)
    git_tag_version: Optional[TagVersion] = None
    with context("Git", 3):
        repo = get_repo(cwd)
        tag: Optional[Tag] = None
        if repo is None or repo.bare:
            context.error(f"Need non-bare git repo at {cwd}")
            repo = None
        else:
            if repo.is_dirty():
                context.error(f"Repo is dirty at {cwd}")
            context("Git tag", 4)
            tag = latest_tag(repo)
            if tag is not None:
                try:
                    git_tag_version = get_git_tag_version(tag)
                except ValueError:
                    pass
    ctx.obj = VersionContext(
        cwd,
        context,
        search_paths,
        repo,
        tag,
        assembly_version,
        change_log_version,
        git_tag_version,
    )


@cmd.command("show-versions")
@click.pass_context
def show_versions(ctx: click.Context) -> None:
    v_ctx = cast(VersionContext, ctx.obj)
    click.echo(
        f"Assembly:  {v_ctx.assembly_version!r}\n"
        f"ChangeLog: {v_ctx.change_log_version!r}\n"
        f"Git tag:   {v_ctx.git_tag_version!r}\n",
    )


@cmd.command("for-merge")
@click.option(
    "--require-branch",
    default="development",
    show_default=True,
    help="Require this branch to be checked out",
)
@click.pass_context
def for_merge(ctx: click.Context, require_branch: str) -> None:
    """Checks project before merging of the development branch into stable branch"""
    v_ctx = cast(VersionContext, ctx.obj)
    cwd = v_ctx.cwd
    context = v_ctx.context
    repo = v_ctx.repo
    tag = v_ctx.tag
    git_tag_version = v_ctx.git_tag_version
    if repo:
        with context("Git", 3):
            if repo.active_branch.name != require_branch:
                context.error(f"Not on the '{require_branch}' branch")
            if tag and not git_tag_version:
                click.echo(f"WARNING: Unable to parse git tag: {tag.name}")
    with context("Version check", 5):
        assembly_version = v_ctx.assembly_version
        change_log_version = v_ctx.change_log_version
        if (
            not assembly_version
            or not change_log_version
            or assembly_version != change_log_version
        ):
            context.error(
                f"Assembly version should match the latest ChangeLog entry"
                f"\nAssembly:  {assembly_version!r}"
                f"\nChangeLog: {change_log_version!r}"
            )
        elif (
            assembly_version and git_tag_version and git_tag_version >= assembly_version
        ):
            context.error(
                f"Git tag version should be be older than Assembly version"
                f"\nAssembly:  {assembly_version!r}"
                f"\nGit tag:   {git_tag_version!r}"
            )
    if not context.failed:
        click.echo(
            f"You can merge the '{require_branch}' into your stable branch\n"
            f"in {cwd}\n"
            f"Upcoming release:\n"
            f"{assembly_version!r}"
        )
        if git_tag_version is not None:
            click.echo(f"Previous release:\n{git_tag_version!r}")
    sys.exit(context.exit_code)


@cmd.command("for-release")
@click.option(
    "--require-branch",
    default="master",
    show_default=True,
    help="Require this branch to be checked out",
)
@click.pass_context
def for_release(ctx: click.Context, require_branch: str) -> None:
    """Checks project before building the release archive"""
    v_ctx = cast(VersionContext, ctx.obj)
    cwd = v_ctx.cwd
    context = v_ctx.context
    repo = v_ctx.repo
    tag = v_ctx.tag
    git_tag_version = v_ctx.git_tag_version
    if repo:
        with context("Git", 3):
            if repo.active_branch.name != require_branch:
                context.error(f"Not on the '{require_branch}' branch")
            context("Git tag", 4)
            if tag is None:
                context.error(f"No tags in the repo at {cwd}")
            else:
                if tag.commit != repo.head.commit:
                    context.error(f"Latest tag {tag.name} is not on the HEAD commit")
                if git_tag_version is None:
                    context.error(f"Unable to parse git tag: {tag.name}")
    with context("Version check", 5):
        assembly_version = v_ctx.assembly_version
        change_log_version = v_ctx.change_log_version
        if (
            not assembly_version
            or not change_log_version
            or not git_tag_version
            or assembly_version != git_tag_version
            or assembly_version != change_log_version
            or git_tag_version != change_log_version
        ):
            context.error(
                f"Versions do not match"
                f"\nAssembly:  {assembly_version!r}"
                f"\nChangeLog: {change_log_version!r}"
                f"\nGit tag:   {git_tag_version!r}",
            )
        else:
            click.echo(
                f"All versions match"
                f"\nAssembly:  {assembly_version!r}"
                f"\nChangeLog: {change_log_version!r}"
                f"\nGit tag:   {git_tag_version!r}",
            )
    sys.exit(context.exit_code)


@cmd.command("check-archive")
@click.argument(
    "archives_path",
    type=click.Path(file_okay=False, dir_okay=True, exists=True),
)
@click.option(
    "--only-if-exists",
    default="",
    show_default=True,
    help="Check for the existence of this file first",
    type=click.Path(),
)
@click.pass_context
def check_archive(ctx: click.Context, archives_path: str, only_if_exists: str) -> None:
    """
    Checks for existence and version of a release archive
    corresponding to Assembly version
    """
    v_ctx = cast(VersionContext, ctx.obj)
    if only_if_exists and not Path(only_if_exists).exists():
        click.echo(f"No {only_if_exists} found.\nSkipping {v_ctx.cwd}")
        sys.exit(0)
    context = v_ctx.context
    assembly_version = v_ctx.assembly_version
    if assembly_version:
        with context("Version check", 5):
            archives = Path(archives_path)
            archive_version: Optional[FilenameVersion] = None
            for filepath in archives.iterdir():
                try:
                    file_version = FilenameVersion.from_file(filepath)
                except ValueError:
                    continue
                if file_version and file_version.title == assembly_version.title:
                    archive_version = file_version
                    if archive_version != assembly_version:
                        context.error(
                            "Archive version does not match the Assembly version:\n"
                            f"Assembly: {assembly_version!r}\n"
                            f"Archive:  {archive_version!r}"
                        )
                    else:
                        click.echo(f"Found archive {filepath.name}\n{archive_version!r}")
                    break
            if not archive_version:
                context.error(
                    f"No archive for {assembly_version.title} is found within\n{archives}"
                )
    sys.exit(context.exit_code)
