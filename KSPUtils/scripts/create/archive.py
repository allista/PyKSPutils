import fnmatch
import os
from pathlib import Path
from typing import List, Optional
from zipfile import ZIP_DEFLATED, ZipFile

import click

from KSPUtils.info_extractors.file_extractor import StrPath
from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.project_cmd import pass_project, sys_exit

exclude_backups = ["*~"]


def zip_dir(
    zip_file: ZipFile,
    path: Path,
    exclude: Optional[List[str]] = None,
    prefix: StrPath = "",
):
    prefix = Path(prefix)
    path = path.absolute()
    cwd = Path.cwd()
    archive_path = path.parent
    if archive_path != path:
        os.chdir(archive_path)
    try:
        stack: List[Path] = [path]
        while stack:
            for sub_path in stack.pop().iterdir():
                if sub_path.is_dir():
                    stack.append(sub_path)
                    continue
                rel_path = str(sub_path.relative_to(archive_path))
                if exclude and [
                    pat for pat in exclude if fnmatch.fnmatch(rel_path, pat)
                ]:
                    continue
                path_in_archive = prefix / rel_path
                click.echo(f"Adding: {path_in_archive}")
                zip_file.write(rel_path, path_in_archive)
    finally:
        os.chdir(cwd)


@click.command("archive")
@pass_project()
def create_archive(project: CSharpProject) -> None:
    """Creates a KSP mod distribution archive"""
    if (
        not project.assembly_title
        or not project.game_data_path
        or not project.archives_path
    ):
        sys_exit()
    project.context.reset()
    exclude = exclude_backups + project.mod_config.exclude_patterns
    with project.context(project.BLOCK_VERSIONS):
        if not project.versions_match(archive=False) or not project.dll_version:
            project.error(f"Versions do not match\n{project.versions_info()}")
            sys_exit(project)
    with project.context(project.BLOCK_ARCHIVE):
        archive_filename = f"{project.assembly_title}-{project.dll_version}.zip"
        archive_path = project.archives_path / archive_filename
        click.echo(f"Creating: {archive_path.relative_to(project.path)}")
        with ZipFile(archive_path, "w", ZIP_DEFLATED) as zip_file:
            zip_dir(zip_file, project.game_data_path, exclude)
            for include_folder in project.mod_config.additional_data_paths:
                include_path = Path(include_folder)
                if not include_path.is_absolute():
                    include_path = project.path / include_path
                zip_dir(zip_file, include_path, exclude)
    sys_exit(project)
