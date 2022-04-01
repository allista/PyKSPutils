import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import on_error_exit, pass_project, sys_exit


@click.command("tag-by-version")
@pass_project(on_error_exit)
def remove_tag_by_version(project: CSharpProject) -> None:
    """
    Removes git tag named after AssemblyVersion from AssemblyInfo.cs

    Some conditions are checked before the tag is removed:

    \b
        - the git tag with this version should be the latest tag
    """
    if not project.repo:
        return
    with project.context(project.BLOCK_GIT):
        if not project.latest_tag:
            project.error("No tag found")
            return
        if not project.git_tag_version:
            project.error(
                f"Unable to parse latest git tag: {project.latest_tag.name}",
            )
            return
    with project.context(project.BLOCK_VERSIONS):
        if project.assembly_version != project.git_tag_version:
            project.error(
                "Assembly version does not match the latest git tag:\n"
                f"Assembly: {project.assembly_version!r}\n"
                f"Git tag:  {project.git_tag_version!r}"
            )
            return
    if not project.context.failed:
        with project.context("Remove git tag"):
            click.echo(f"Removing the tag: {project.git_tag_version!r}")
            project.repo.delete_tag(project.latest_tag)
            project.update_latest_tag()
            click.echo(f"Latest tag now: {project.git_tag_version!r}")
    sys_exit(project)
