import sys

import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.project_info.getters import get_git_tag_version
from KSPUtils.scripts.project_cmd import create_project_cmd, pass_project, sys_exit


def on_error(message: str, exit_code: int) -> None:
    click.echo(message, err=True)
    sys.exit(exit_code)


cmd = create_project_cmd(on_error)


@cmd.command("create")
@click.option(
    "--require-branch",
    default="master",
    show_default=True,
    help="Require this branch to be checked out to create the tag",
)
@pass_project
def create_tag(project: CSharpProject, require_branch: str) -> None:
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
    if project.context.failed:
        sys_exit(project)
    with project.context(project.BLOCK_GIT):
        if project.repo.active_branch.name != require_branch:
            project.error(f"Not on the '{require_branch}' branch")
    with project.context(project.BLOCK_GIT_TAG):
        if project.latest_tag:
            if not project.git_tag_version:
                click.echo(
                    f"WARNING: Unable to parse latest git tag: {project.latest_tag.name}",
                    err=True,
                )
            else:
                if project.latest_tag.commit == project.repo.head.commit:
                    project.error(
                        f"The latest git tag {project.latest_tag.name} is on the HEAD"
                    )
    with project.context("Assembly vs ChangeLog"):
        if project.assembly_version > project.change_log_version:
            project.error(
                f"Assembly version {project.assembly_version} is greater "
                f"than the ChangeLog version {project.change_log_version}\n"
                f"Fill in the changelog entry for {project.assembly_version}",
            )
    with project.context("Git tag version"):
        if project.git_tag_version:
            if project.git_tag_version > project.assembly_version:
                project.error(
                    f"Assembly version {project.assembly_version} is less "
                    f"than the git tag version {project.git_tag_version}.\n"
                    f"Did you forget to update AssemblyInfo and ChangeLog?",
                )
            if project.git_tag_version == project.assembly_version:
                project.error(
                    f"Assembly version {project.assembly_version} is equal to the latest git tag version.\n"
                    "You have to investigate and remove the tag manually.",
                )
    if not project.context.failed:
        click.echo(
            f"Creating new lightweight tag at the HEAD of the '{require_branch}' branch:\n"
            f"{project.assembly_version!r} on {project.repo.head.commit.hexsha[:7]} <- HEAD"
        )
        if project.git_tag_version:
            click.echo(f"{project.git_tag_version!r}")
        with project.context("New git tag"):
            new_tag = project.repo.create_tag(f"{project.assembly_version}")
            new_tag_version = get_git_tag_version(new_tag)
            click.echo(f"Created new tag: {new_tag_version!r}")
    sys_exit(project)


@cmd.command("remove")
@pass_project
def remove_tag(project: CSharpProject) -> None:
    """
    Removes git tag named after AssemblyVersion from AssemblyInfo.cs

    Some conditions are checked before the tag is removed:

    \b
        - the git tag with this version should be the latest tag
    """
    if project.context.failed:
        sys_exit(project)
    with project.context(project.BLOCK_GIT_TAG):
        if not project.latest_tag:
            project.error("No tag found")
        if not project.git_tag_version:
            project.error(
                f"Unable to parse latest git tag: {project.latest_tag.name}",
            )
    with project.context("Assembly vs Git tag"):
        if project.assembly_version != project.git_tag_version:
            project.error(
                "Assembly version does not match the latest git tag:\n"
                f"Assembly: {project.assembly_version!r}\n"
                f"Git tag:  {project.git_tag_version!r}"
            )

    if not project.context.failed:
        with project.context("Remove git tag"):
            click.echo(f"Removing the tag: {project.git_tag_version!r}")
            project.repo.delete_tag(project.latest_tag)
            project.update_latest_tag()
            click.echo(f"Latest tag now: {project.git_tag_version!r}")
    sys_exit(project)
