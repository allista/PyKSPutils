import sys

import click

from KSPUtils import spacedock
from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import on_error_exit, pass_project, sys_exit
from KSPUtils.scripts.publish.common import GPG_FILE_HELP
from KSPUtils.spacedock import SPACEDOCK_AUTH_FILE, SpacedockError
from KSPUtils.utils.gpg import GPG_ID_FILE


@click.group("spacedock")
def spacedock_grp() -> None:
    pass


@spacedock_grp.command(
    "set-auth",
    help=f"""
    Saves GPG-encrypted username and password for Spacedock to the {SPACEDOCK_AUTH_FILE} file.

    Requires the {GPG_ID_FILE} file to be in this folder or in any of its parents.
    """,
)
@click.option("--username", prompt="Spacedock login", help="Spacedock username")
@click.password_option("--password", prompt="password", help="Spacedock password")
@pass_project()
def set_auth(project: CSharpProject, username, password) -> None:
    with project.context(project.BLOCK_SPACEDOCK, SpacedockError):
        spacedock.set_auth(username, password, ".")
    sys_exit(project)


@spacedock_grp.command(
    "upload",
    help=f"""
    Updates the mod on Spacedock with the current mod version,
    using corresponding changelog entry and archive file.

    Requires the {SPACEDOCK_AUTH_FILE} file with GPG-encrypted credentials
    to be in this folder or in any of its parents.

    {GPG_FILE_HELP}
    """,
)
@pass_project(on_error=on_error_exit)
def upload_to_spacedock(
    project: CSharpProject,
) -> None:
    if not project.mod_config.spacedock_mod_id or not project.mod_config.archive_path:
        sys.exit(0)
    with project.context(project.BLOCK_VERSIONS):
        # see if locally everything matches
        if not project.versions_match():
            project.error(f"Versions do not match\n{project.versions_info()}")
            return
    with project.context(project.BLOCK_SPACEDOCK, SpacedockError):
        if (
            not project.assembly_info
            or not project.assembly_version
            or not project.archive_version
        ):
            return
        if not project.assembly_info.max_ksp_version:
            project.error("No MAX KSP Version found in AssemblyInfo")
            return
        # get mod info from spacedock
        user = spacedock.login(".")
        mod_id = project.mod_config.spacedock_mod_id
        mod = user.get_mod(mod_id, reload=True)
        if not mod:
            project.error(f"Mod {mod_id} does not belong to {user.username}")
            return
        # check if we already have the release for this version
        published_version = mod.get_version(project.assembly_version)
        if published_version:
            project.error(
                f"Release already exists: {published_version.friendly_version} "
                f"at {published_version.download_url}"
            )
            return
        # get the change log entry for the release body
        change_log = project.change_log[project.assembly_version]
        if not change_log:
            project.error(
                f"Unable to get change log entry for: {project.assembly_version}"
            )
            return
        # update the mod and reload its info
        mod.update(
            project.assembly_version.as_str_without_prefix,
            change_log,
            project.assembly_info.max_ksp_version.as_str_without_prefix,
            project.archive_version.filepath,
        )
        click.echo(f"Successfully published release {project.assembly_version}")
        try:
            mod = mod.reload()
            new_version = mod.get_version(project.assembly_version)
            if new_version:
                click.echo(f"Download URL: {new_version.download_url}")
            else:
                click.echo("WARNING: new version not found!", err=True)
        except SpacedockError as e:
            click.echo(f"But could not reload mod info: {e}", err=True)
    sys_exit(project)
