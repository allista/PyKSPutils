import sys

import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import create_project_cmd, pass_project, sys_exit

cmd = create_project_cmd()

BLOCK_VERSIONS = "Version check"


@cmd.command("show-versions")
@pass_project()
def show_versions(project: CSharpProject) -> None:
    click.echo(f"{project}")


@cmd.command("for-merge")
@click.option(
    "--require-branch",
    default="development",
    show_default=True,
    help="Require this branch to be checked out",
)
@pass_project()
def for_merge(project: CSharpProject, require_branch: str) -> None:
    """Checks project before merging of the development branch into stable branch"""
    with project.context(project.BLOCK_GIT):
        if project.repo:
            if project.repo.active_branch.name != require_branch:
                project.error(f"Not on the '{require_branch}' branch")
    with project.context(project.BLOCK_GIT_TAG):
        if project.latest_tag and not project.git_tag_version:
            click.echo(f"WARNING: Unable to parse git tag: {project.latest_tag.name}")
    with project.context(BLOCK_VERSIONS):
        if (
            not project.assembly_version
            or project.assembly_version != project.change_log_version
        ):
            project.error(
                f"Assembly version should match the latest ChangeLog entry"
                f"\nAssembly:  {project.assembly_version!r}"
                f"\nChangeLog: {project.change_log_version!r}"
            )
        elif (
            project.assembly_version
            and project.git_tag_version
            and project.git_tag_version >= project.assembly_version
        ):
            project.error(
                f"Git tag version should be be older than Assembly version"
                f"\nAssembly:  {project.assembly_version!r}"
                f"\nGit tag:   {project.git_tag_version!r}"
            )
    if not project.context.failed:
        click.echo(
            f"You can merge the '{require_branch}' into your stable branch\n"
            f"in {project.path}\n"
            f"Upcoming release:\n"
            f"{project.assembly_info!r}"
        )
        if project.git_tag_version is not None:
            click.echo(f"Previous release:\n{project.git_tag_version!r}")
    sys_exit(project)


@cmd.command("for-release")
@click.option(
    "--require-branch",
    default="master",
    show_default=True,
    help="Require this branch to be checked out",
)
@pass_project()
def for_release(project: CSharpProject, require_branch: str) -> None:
    """Checks project before building the release archive"""
    with project.context(project.BLOCK_GIT):
        if project.repo:
            if project.repo.active_branch.name != require_branch:
                project.error(f"Not on the '{require_branch}' branch")
    with project.context(project.BLOCK_GIT_TAG):
        if project.latest_tag is None:
            project.error(f"No tags in the repo at {project.path}")
        else:
            if project.latest_tag.commit != project.repo.head.commit:
                project.error(
                    f"Latest tag {project.latest_tag.name} is not on the HEAD commit"
                )
            if project.git_tag_version is None:
                project.error(f"Unable to parse git tag: {project.latest_tag.name}")
    with project.context(BLOCK_VERSIONS):
        if not project.versions_match(archive=False):
            project.error(
                f"Versions do not match\n{project.versions_info(archive=False)}"
            )
        else:
            click.echo(f"All versions match\n{project.versions_info(archive=False)}")
    sys_exit(project)


@cmd.command("check-archive")
@pass_project()
def check_archive(project: CSharpProject) -> None:
    """
    Checks for existence and version of a release archive
    corresponding to Assembly version
    """
    if not project.mod_config.archive_path:
        sys.exit(0)
    with project.context(project.BLOCK_ARCHIVE):
        if not project.archive_version:
            project.error(
                f"No archive for {project.assembly_info.title} is found within {project.mod_config.archive_path}"
            )
        elif project.archive_version != project.assembly_version:
            project.error(
                "Latest archive version does not match the Assembly version:\n"
                f"Assembly: {project.assembly_version!r}\n"
                f"Archive:  {project.archive_version!r}"
            )
        else:
            click.echo(
                f"Found archive {project.archive_version.filename}\n{project.archive_version!r}"
            )
    sys_exit(project)
