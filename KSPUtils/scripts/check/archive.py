import sys

import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import pass_project, sys_exit


@click.command("archive")
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
                f"No archive for {project.assembly_title} "
                f"is found within {project.mod_config.archive_path}"
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
