import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import pass_project, sys_exit


@click.command("for-merge")
@click.option(
    "--require-branch",
    default="development",
    show_default=True,
    help="Require this branch to be checked out",
)
@pass_project()
def check_for_merge(project: CSharpProject, require_branch: str) -> None:
    """Checks project before merging of the development branch into stable branch"""
    with project.context(project.BLOCK_GIT):
        if project.repo:
            if project.repo.active_branch.name != require_branch:
                project.error(f"Not on the '{require_branch}' branch")
        if project.latest_tag and not project.git_tag_version:
            click.echo(f"WARNING: Unable to parse git tag: {project.latest_tag.name}")
    with project.context(project.BLOCK_VERSIONS):
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
                f"Git tag version should less than Assembly version"
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
