import sys
from typing import Optional

import click
import github.GithubException
from github.GitReleaseAsset import GitReleaseAsset
from github.Tag import Tag

from KSPUtils import spacedock
from KSPUtils.github_utils import GITHUB_AUTH_FILE, GithubError, set_github_token
from KSPUtils.gpg_utils import GPG_ID_FILE
from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import (
    create_project_cmd,
    on_error_exit,
    pass_project,
    sys_exit,
)
from KSPUtils.spacedock import SPACEDOCK_AUTH_FILE, SpacedockError

cmd = create_project_cmd()

GPG_FILE_HELP = (
    f"Requires the {GPG_ID_FILE} file to be in this folder or in any of its parents."
)


@cmd.group("github")
def github_grp():
    pass


@github_grp.command(
    "set-token",
    help=f"""
    Saves GPG-encrypted auth token for GitHub to the {GITHUB_AUTH_FILE} file.

    {GPG_FILE_HELP}
    """,
)
@click.option("--token", prompt="GitHub token", help="GitHub OAuth token.")
@pass_project()
def set_token(project: CSharpProject, token) -> None:
    with project.context(project.BLOCK_GITHUB, GithubError):
        set_github_token(token, ".")
        project.update_github()
    sys_exit(project)


@github_grp.command(
    "upload",
    help=f"""
    Creates a new release on GitHub with the current mod version,
    using corresponding changelog entry and archive file.

    Requires the {GITHUB_AUTH_FILE} file with GPG-encrypted GitHub token
    to be in this folder or in any of its parents.

    {GPG_FILE_HELP}
    """,
)
@click.option(
    "--update",
    help="Update the release, if it exists.",
    is_flag=True,
)
@pass_project(on_error=on_error_exit)
def upload_to_github(project: CSharpProject, update) -> None:
    if not project.mod_config.github_url or not project.mod_config.archive_path:
        sys.exit(0)
    project.update_github()
    with project.context(project.BLOCK_GITHUB, github.GithubException):
        # see if locally everything matches
        if not project.versions_match():
            project.error(f"Versions do not match\n{project.versions_info()}")
        repo = project.github.get_repo(project.mod_config.github_url)
        # check if the tag for the release exists on the remote
        published_tag: Optional[Tag] = None
        git_tag_name = f"{project.git_tag_version}"
        for tag in repo.get_tags():
            if tag.name == git_tag_name:
                if tag.commit.sha != project.git_tag_version.commit_sha:
                    project.error(
                        "Remote tag is on the wrong commit:\n"
                        f"Tag:    {git_tag_name}"
                        f"Local:  {project.git_tag_version.commit_sha}\n"
                        f"Remote: {tag.commit.sha}"
                    )
                else:
                    published_tag = tag
                    break
        if not published_tag:
            project.error(f"Git tag is not published: {project.git_tag_version!r}")
        # check if we already have the release for this tag
        try:
            release = repo.get_release(published_tag.name)
            if release and not update:
                project.error(
                    f"Release already exists: {release.title} at {release.html_url}"
                )
        except github.UnknownObjectException:
            pass
        # get the change log entry for the release body
        change_log = project.change_log[project.assembly_version]
        if not change_log:
            project.error(
                f"Unable to get change log entry for: {project.assembly_version}"
            )
        # create or update the release
        if not release:
            click.echo(f"Creating new release: {tag.name}")
            release = repo.create_git_release(tag.name, tag.name, change_log)
        else:
            click.echo(f"Updating the release: {release.title}")
            if release.body != change_log:
                click.echo(f"Updating the change log for: {project.assembly_version}")
                release.update_release(release.title, change_log)
        # check if the asset already exists
        existing_assert: Optional[GitReleaseAsset] = None
        for asset in release.get_assets():
            if asset.name == project.archive_version.filename:
                existing_assert = asset
        if existing_assert:
            if not update:
                project.error(
                    f"Asset already exists: {existing_assert.browser_download_url}"
                )
            click.echo(f"Removing existing asset: {existing_assert.name}")
            existing_assert.delete_asset()
        click.echo(f"Uploading asset: {project.archive_version.filepath}")
        release.upload_asset(f"{project.archive_version.filepath}")
        click.echo(
            f"Successfully published release {release.title}: {release.html_url}"
        )
    sys_exit(project)


@cmd.group("spacedock")
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
    if (
        not project.mod_config.spacedock_mod_id
        or not project.mod_config.archive_path
        or project.mod_config.spacedock_mod_id is None
    ):
        sys.exit(0)
    with project.context(project.BLOCK_SPACEDOCK, SpacedockError):
        # see if locally everything matches
        if not project.versions_match():
            project.error(f"Versions do not match\n{project.versions_info()}")
        if not project.assembly_info.max_ksp_version:
            project.error("No MAX KSP Version found in AssemblyInfo")
        # get mod info from spacedock
        user = spacedock.login(".")
        mod_id = project.mod_config.spacedock_mod_id
        mod = user.get_mod(mod_id, reload=True)
        if not mod:
            project.error(f"Mod {mod_id} does not belong to {user.username}")
        # check if we already have the release for this version
        published_version = mod.get_version(project.assembly_version)
        if published_version:
            project.error(
                f"Release already exists: {published_version.friendly_version} "
                f"at {published_version.download_url}"
            )
        # get the change log entry for the release body
        change_log = project.change_log[project.assembly_version]
        if not change_log:
            project.error(
                f"Unable to get change log entry for: {project.assembly_version}"
            )
        # update the mod and reload its info
        mod.update(
            project.assembly_version.as_str_without_prefix,
            change_log,
            project.assembly_info.max_ksp_version.as_str_without_prefix,
            project.archive_version.filepath,
        )
        try:
            mod = mod.reload()
            new_version = mod.get_version(project.assembly_version)
            click.echo(
                f"Successfully published release: {new_version.friendly_version} at {new_version.download_url}"
            )
        except SpacedockError as e:
            click.echo(
                f"Successfully published release {project.assembly_version} but could not reload mod info: {e}"
            )
    sys_exit(project)
