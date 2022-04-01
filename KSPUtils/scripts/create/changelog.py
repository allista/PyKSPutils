import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import pass_project, sys_exit


@click.command("changelog")
@click.option(
    "--reformat",
    help="Re-format the change log file if it exists",
    is_flag=True,
)
@click.option("--dry-run", is_flag=True, help="Do not write anything to disk")
@pass_project()
def create_changelog(project: CSharpProject, reformat: bool, dry_run: bool) -> None:
    """
    Creates new changelog file if it does not exist.

    If the file exists and the --reformat flag is provided,
    the change log from the file is reformatted and saved back.
    """
    project.context.reset(project.BLOCK_GIT)
    if project.context.failed:
        sys_exit(project)
    rel_path = project.change_log.filepath.relative_to(project.path)
    with project.context(project.BLOCK_CHANE_LOG):
        if project.change_log.filepath.exists():
            if not reformat:
                click.echo(f"Change log already exists: {rel_path}")
                sys_exit(project)
            if not project.change_log.has_changed:
                click.echo(f"Change log has not changed: {rel_path}")
                sys_exit(project)
            click.echo(f"Reformatting existing change log from: {rel_path}")
        else:
            click.echo(f"Creating new change log from: {rel_path}")
        if dry_run:
            click.echo(project.change_log)
        else:
            project.change_log.save()
    sys_exit(project)
