import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.project_info.getters import get_git_tag_version
from KSPUtils.scripts.project_cmd import on_error_exit, pass_project, sys_exit


@click.command("tag-by-version")
@click.option(
    "--require-branch",
    default="master",
    show_default=True,
    help="Require this branch to be checked out to create the tag",
)
@pass_project(on_error_exit)
def create_tag_by_version(project: CSharpProject, require_branch: str) -> None:
    """
    Creates lightweight git tag named after AssemblyVersion from AssemblyInfo.cs
    The version is prefixed with "v", e.g. "v1.2.3".

    Some conditions are checked before the tag is created:

    \b
        - repository should be on the --required-branch and sould not be dirty
        - a changelog file should exist, containing the same version as AssemblyInfo.cs
          E.g. if [assembly: AssemblyVersion("3.8.0")] is found in AssemblyInfo.cs,
          The sub-string "v3.8.0" should be present in the changelog file before other
          version-like sub-strings.
        - a git tag with this version should not exist, or be the latest tag and on the HEAD commit
    """
    with project.context(project.BLOCK_GIT):
        if not project.repo:
            sys_exit(project)
        if project.repo.active_branch.name != require_branch:
            project.error(f"Not on the '{require_branch}' branch")
            sys_exit(project)
    with project.context(project.BLOCK_CHANE_LOG):
        if (
            project.assembly_version
            and project.assembly_version > project.change_log_version
        ):
            project.error(
                f"Assembly version {project.assembly_version} is greater "
                f"than the ChangeLog version {project.change_log_version}\n"
                f"Fill in the changelog entry for {project.assembly_version}",
            )
            sys_exit(project)
    with project.context(project.BLOCK_GIT):
        if project.latest_tag:
            if not project.git_tag_version:
                click.echo(
                    f"WARNING: Unable to parse latest git tag: {project.latest_tag.name}",
                    err=True,
                )
            else:
                if project.git_tag_version > project.assembly_version:
                    project.error(
                        f"Assembly version {project.assembly_version} is less "
                        f"than the git tag version {project.git_tag_version}.\n"
                        f"Did you forget to update AssemblyInfo and ChangeLog?",
                    )
                    sys_exit(project)
                if project.git_tag_version == project.assembly_version:
                    if project.latest_tag.commit == project.repo.head.commit:
                        click.echo(
                            f"Tag already exists on the HEAD:\n{project.git_tag_version!r}"
                        )
                        sys_exit()
                    project.error(
                        f"Assembly version {project.assembly_version} "
                        "is equal to the latest git tag version, which is not on HEAD commit.\n"
                        "You have to investigate and remove the tag manually.",
                    )
                    sys_exit(project)
    if not project.context.failed:
        click.echo(
            f"Creating new lightweight tag at the HEAD of the '{require_branch}' branch:\n"
            f"{project.assembly_version!r} on {project.repo.head.commit.hexsha[:7]} <- HEAD"
        )
        if project.git_tag_version:
            click.echo(f"{project.git_tag_version!r}")
        with project.context(project.BLOCK_GIT):
            new_tag = project.repo.create_tag(f"{project.assembly_version}")
            new_tag_version = get_git_tag_version(new_tag)
            click.echo(f"Created new tag: {new_tag_version!r}")
    sys_exit(project)
