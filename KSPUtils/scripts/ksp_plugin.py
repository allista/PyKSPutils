import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.check.archive import check_archive
from KSPUtils.scripts.check.for_merge import check_for_merge
from KSPUtils.scripts.check.for_release import check_for_release
from KSPUtils.scripts.create.archive import create_archive
from KSPUtils.scripts.create.tag_by_version import create_tag_by_version
from KSPUtils.scripts.project_cmd import create_project_cmd, pass_project
from KSPUtils.scripts.publish.github import github_grp
from KSPUtils.scripts.publish.spacedock import spacedock_grp
from KSPUtils.scripts.remove.tag_by_version import remove_tag_by_version

cmd = create_project_cmd()

cmd.add_command(github_grp)
cmd.add_command(spacedock_grp)


@cmd.group("check")
def check_grp() -> None:
    pass


check_grp.add_command(check_archive)
check_grp.add_command(check_for_merge)
check_grp.add_command(check_for_release)


@cmd.group("create")
def create_grp() -> None:
    pass


create_grp.add_command(create_archive)
create_grp.add_command(create_tag_by_version)


@cmd.group("remove")
def remove_grp() -> None:
    pass


remove_grp.add_command(remove_tag_by_version)


@cmd.command("info")
@click.option(
    "--print-changelog",
    help="Print out the latest changelog entry",
    is_flag=True,
)
@pass_project()
def show_info(project: CSharpProject, print_changelog) -> None:
    """Print summary information about KSP plugin project in the current folder"""
    click.echo(project)
    if print_changelog and project.change_log:
        change_log = project.change_log.latest_entry
        if change_log:
            click.echo(
                f"\nLatest change log entry: {project.change_log.latest_version}"
            )
            click.echo(change_log)
