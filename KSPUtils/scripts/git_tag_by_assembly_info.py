import sys
from pathlib import Path
from typing import List

import click

from KSPUtils.git_utils import get_repo, latest_tag
from KSPUtils.project_info import (
    get_assembly_version,
    get_changelog_version,
    get_git_tag_version,
)
from .execution_context import ExecutionContext
from .utils import get_search_paths


def on_error(message: str, exit_code: int) -> None:
    click.echo(message, err=True)
    sys.exit(exit_code)


@click.command(
    "git_tag_by_assembly_info",
)
@click.option(
    "--require-branch",
    default="master",
    show_default=True,
    help="Require this branch to be checked out to create the tag",
)
@click.option(
    "--change-log",
    default="ChangeLog.md",
    type=click.Path(),
    show_default=True,
    help="The name of the changelog file to search for the version",
)
@click.option(
    "--add-search-path",
    multiple=True,
    default=[],
    help="Additional paths to search for project sources and change log",
)
def cmd(change_log: str, require_branch: str, add_search_path: List[str]) -> None:
    """
    Creates lightweight git tag named after AssemblyVersion from AssemblyInfo.cs
    The version is prefixed with "v", e.g. "v1.2.3".

    Some conditions are checked before the tag is created:

    \b
        - repository should be on the --required-branch
        - a changelog file should exist, containing the same version as AssemblyInfo.cs
          E.g. if [assembly: AssemblyVersion("3.8.0")] is found in AssemblyInfo.cs,
          The sub-string "v3.8.0" should be present in the changelog file before other
          version-like sub-strings.
        - a git tag with this version should not exist
        - the latest existing git tag with a version should not be on HEAD commit
    """
    cwd = Path.cwd()
    search_paths = get_search_paths(cwd, *add_search_path)
    context = ExecutionContext(on_error, ValueError)
    with context("Git", 1):
        repo = get_repo(cwd)
        if repo is None or repo.bare:
            context.error(f"Need non-bare git repo at {cwd}")
        elif repo.is_dirty():
            context.error(f"Repo is dirty at {cwd}")
        if repo.active_branch.name != require_branch:
            context.error(f"Not on the '{require_branch}' branch")
    # acquire versions from git, changelog and AssemblyVersion
    with context("Git tag", 2):
        tag = latest_tag(repo)
        git_tag_version = None
        if tag is not None:
            try:
                git_tag_version = get_git_tag_version(tag)
            except ValueError:
                click.echo(
                    f"WARNING: Unable to parse latest git tag: {tag.name}", err=True
                )
            else:
                if tag.commit == repo.head.commit:
                    context.error(f"The latest git tag {tag.name} is on the HEAD")
    with context("AssemblyInfo", 3):
        assembly_version = get_assembly_version(*search_paths)
    with context("ChangeLog", 4):
        change_log_version = get_changelog_version(change_log, *search_paths)
    # check if the versions satisfy pre-release conditions
    with context("Assembly vs ChangeLog", 4):
        if assembly_version > change_log_version:
            context.error(
                f"Assembly version {assembly_version} is greater than the ChangeLog version {change_log_version}\n"
                f"Fill in the changelog entry for {assembly_version}",
            )
    with context("Git tag version", 5):
        if git_tag_version:
            if git_tag_version > assembly_version:
                context.error(
                    f"Assembly version {assembly_version} is less than the git tag version {git_tag_version}.\n"
                    f"Did you forget to update AssemblyInfo and ChangeLog?",
                )
            if git_tag_version == assembly_version:
                context.error(
                    f"Assembly version {assembly_version} is equal to the latest git tag version.\n"
                    "You have to investigate and remove the tag manually.",
                )
    if not context.failed:
        click.echo(
            f"Creating new lightweight tag at the HEAD of the '{require_branch}' branch:\n"
            f"{assembly_version!r} on {repo.head.commit.hexsha[:7]} <- HEAD"
        )
        if git_tag_version:
            click.echo(f'{git_tag_version!r}')
        with context("New git tag", 6):
            new_tag = repo.create_tag(f'{assembly_version}')
            new_tag_version = get_git_tag_version(new_tag)
            click.echo(f"Created new tag: {new_tag_version!r}")
    click.echo()
    sys.exit(context.exit_code)
