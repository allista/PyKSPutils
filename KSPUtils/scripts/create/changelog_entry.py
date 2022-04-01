from typing import Generator, List, Optional

import click
from git import Repo, Tag
from git.objects.commit import Commit

from KSPUtils.info_extractors.versions import ChangeLogVersion
from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import pass_project, sys_exit


def iter_commits_until(repo: Repo, tag: Optional[Tag]) -> Generator[Commit, None, None]:
    stop_at = tag.commit if tag else None
    for commit in repo.iter_commits(rev=repo.head):
        if commit == stop_at:
            break
        yield commit


def format_commit_message(commit: Commit) -> str:
    lines: List[str] = [
        str(line)
        for line in (_line.strip() for _line in commit.message.splitlines())
        if line
    ]
    if not lines:
        return ""
    if len(lines) == 1:
        return f"* {lines[0]}"
    formatted: List[str] = [f"* {lines[0]}"]
    entry: List[str] = []
    for line in lines[1:]:
        if (
            not entry
            or line.startswith("*")
            or len(line) < 2
            or line[0].isupper()
            and line[1].islower()
        ):
            if entry:
                formatted.append(" ".join(entry))
            entry = [f"    * {line.lstrip('* ')}"]
        else:
            entry.append(line)
    if entry:
        formatted.append(" ".join(entry))
    return "\n".join(formatted)


@click.command("changelog-entry")
@click.option(
    "--update",
    help="Update the version, if it exists.",
    is_flag=True,
)
@click.option("--dry-run", is_flag=True, help="Do not write anything to disk")
@pass_project()
def create_changelog_entry(project: CSharpProject, update: bool, dry_run: bool) -> None:
    """
    Creates new change log entry for the current AssemblyVersion.

    If the entry already exists and the --update flag is provided,
    the entry is replaced with the newly generated one.
    """
    if not project.assembly_version or not project.repo:
        sys_exit(project)
    with project.context(project.BLOCK_GIT):
        if project.assembly_version <= project.git_tag_version:
            project.error(
                "Assembly version is not greater than the latest git tag.\n"
                "Did you forget to update the AssemblyVersion?"
            )
            sys_exit(project)
        if project.latest_tag and project.latest_tag.commit == project.repo.head.commit:
            project.error(
                "Latest git tag is on HEAD. Nothing to write into the change log."
            )
            sys_exit(project)
    project.context.reset()
    with project.context(project.BLOCK_CHANE_LOG):
        entry = project.change_log[project.assembly_version]
        if entry and not update:
            project.error(
                f"Change log entry already exists for: {project.assembly_version}"
            )
            sys_exit(project)
        new_entry = "\n".join(
            format_commit_message(commit)
            for commit in iter_commits_until(project.repo, project.latest_tag)
        ).strip()
        if new_entry != entry:
            changelog_version = ChangeLogVersion.clone(
                project.assembly_version,
                title=f"/ {project.assembly_version.date:%Y-%m-%d}",
            )
            project.change_log[changelog_version] = new_entry
        if project.change_log.is_dirty:
            click.echo(
                f"Adding new change log entry for: {project.assembly_version}\n"
                f"------------------------\n{new_entry}\n------------------------"
            )
            if not dry_run:
                project.change_log.save()
    sys_exit(project)
