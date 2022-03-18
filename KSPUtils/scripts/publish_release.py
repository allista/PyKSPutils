import sys
from typing import Optional

import click
import github.GithubException
from github.Tag import Tag

from KSPUtils.github_utils import GITHUB_AUTH_FILE, GithubError, set_github_token
from KSPUtils.gpg_utils import GPG_ID_FILE
from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import (
    create_project_cmd,
    on_error_exit,
    pass_project,
    sys_exit,
)

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
@pass_project(on_error=on_error_exit)
def upload_to_github(
    project: CSharpProject,
) -> None:
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
            published_release = repo.get_release(published_tag.name)
            if published_release:
                project.error(
                    f"Release already exists: {published_release.title} at {published_release.html_url}"
                )
        except github.UnknownObjectException:
            pass
        # get the change log entry for the release body
        change_log = project.change_log[project.assembly_version]
        if not change_log:
            project.error(
                f"Unable to get change log entry for: {project.assembly_version}"
            )
        # create the release
        new_release = repo.create_git_release(tag.name, tag.name, change_log)
        new_release.upload_asset(f"{project.archive_version.filepath}")
        click.echo(
            f"Successfully published release {new_release.title}: {new_release.html_url}"
        )
    sys_exit(project)

