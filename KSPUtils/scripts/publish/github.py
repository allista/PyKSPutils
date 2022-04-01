import sys
from typing import Optional

import click
import github
from github.GitReleaseAsset import GitReleaseAsset
from github.Tag import Tag

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import on_error_exit, pass_project, sys_exit
from KSPUtils.scripts.publish.common import GPG_FILE_HELP
from KSPUtils.utils.github import GITHUB_AUTH_FILE, GithubError, set_github_token


@click.group("github")
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
    if not project.github:
        return
    with project.context(project.BLOCK_VERSIONS):
        # see if locally everything matches
        if not project.versions_match() or not project.git_tag_version:
            project.error(f"Versions do not match\n{project.versions_info()}")
            return
    with project.context(project.BLOCK_GITHUB, github.GithubException):
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
                    return
                published_tag = tag
                break
        if not published_tag:
            project.error(f"Git tag is not published: {project.git_tag_version!r}")
            return
        # check if we already have the release for this tag
        try:
            release = repo.get_release(published_tag.name)
            if release and not update:
                project.error(
                    f"Release already exists: {release.title} at {release.html_url}"
                )
                return
        except github.UnknownObjectException:
            pass
        # get the change log entry for the release body
        change_log = project.change_log[project.assembly_version]
        if not change_log:
            project.error(
                f"Unable to get change log entry for: {project.assembly_version}"
            )
            return
        # create or update the release
        if not release:
            click.echo(f"Creating new release: {published_tag.name}")
            release = repo.create_git_release(
                published_tag.name, published_tag.name, change_log
            )
        else:
            click.echo(f"Updating the release: {release.title}")
            if release.body != change_log:
                click.echo(f"Updating the change log for: {project.assembly_version}")
                release.update_release(release.title, change_log)
        # check if the asset already exists
        existing_assert: Optional[GitReleaseAsset] = None
        if not project.archive_version:
            return
        for asset in release.get_assets():
            if asset.name == project.archive_version.filename:
                existing_assert = asset
        if existing_assert:
            if not update:
                project.error(
                    f"Asset already exists: {existing_assert.browser_download_url}"
                )
                return
            click.echo(f"Removing existing asset: {existing_assert.name}")
            existing_assert.delete_asset()
        click.echo(f"Uploading asset: {project.archive_version.filepath}")
        release.upload_asset(f"{project.archive_version.filepath}")
        click.echo(
            f"Successfully published release {release.title}: {release.html_url}"
        )
    sys_exit(project)
