import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import pass_project, sys_exit


@click.command("for-release")
@click.option(
    "--require-branch",
    default="master",
    show_default=True,
    help="Require this branch to be checked out",
)
@pass_project()
def check_for_release(project: CSharpProject, require_branch: str) -> None:
    """Checks project before building the release archive"""
    with project.context(project.BLOCK_GIT):
        if project.repo:
            if project.repo.active_branch.name != require_branch:
                project.error(f"Not on the '{require_branch}' branch")
        if project.latest_tag is None:
            project.error(f"No tags in the repo at {project.path}")
        elif project.repo:
            if project.latest_tag.commit != project.repo.head.commit:
                project.error(
                    f"Latest tag {project.latest_tag.name} is not on the HEAD commit"
                )
            if project.git_tag_version is None:
                project.error(f"Unable to parse git tag: {project.latest_tag.name}")
    with project.context(project.BLOCK_VERSIONS):
        if not project.versions_match(archive=False):
            project.error(
                f"Versions do not match\n{project.versions_info(archive=False)}"
            )
        else:
            click.echo(f"All versions match\n{project.versions_info(archive=False)}")
    sys_exit(project)
