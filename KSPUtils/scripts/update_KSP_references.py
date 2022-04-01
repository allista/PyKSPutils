import logging
import os.path
import re
import sys
from io import StringIO
from pathlib import Path
from typing import Optional, Pattern

import click

from KSPUtils.errors_context import ErrorsContext
from KSPUtils.info_extractors.versions import KspReadmeVersion
from KSPUtils.project_info.csharp_project import CSharpProject

assembly_re = re.compile(r"\s*<HintPath>(.*)\\KSP_Data\\Managed\\.*\.dll</HintPath>")

ErrorsContext.logger.setLevel(logging.CRITICAL)


def replace_references(
    cwd: Path, ksp_path: Path, csproj_path: Path, dry_run: bool
) -> None:
    replacement = (
        os.path.relpath(ksp_path, csproj_path.parent).rstrip("/\\").replace("/", "\\")
    )
    content = StringIO()
    changed = False
    with csproj_path.open("rt", encoding="utf8") as inp:
        for line in inp:
            match = assembly_re.match(line)
            if not match or replacement == match.group(1):
                content.write(line)
                continue
            print(line, match.group(1), replacement)
            print(line.replace(match.group(1), replacement))
            content.write(line.replace(match.group(1), replacement))
            changed = True
    if not changed:
        return
    click.echo(
        f"Changing references in: {csproj_path.relative_to(cwd)}"
        + (" [DRY RUN]" if dry_run else "")
    )
    if dry_run:
        return
    content.seek(0)
    with csproj_path.open("wt", encoding="utf8") as out:
        out.write(content.read())


def replace_ksp_avc_versions(
    cwd: Path, ksp_version: KspReadmeVersion, project_path: Path, dry_run: bool
) -> None:
    project = CSharpProject(project_path)
    project.load()
    if not project.assembly_info:
        return
    version_replacement = (
        f"{ksp_version.major}, {ksp_version.minor}, {ksp_version.build}"
    )
    project.assembly_info.replace("min_ksp_version", version_replacement)
    project.assembly_info.replace("max_ksp_version", version_replacement)
    if not project.assembly_info.is_dirty:
        return
    click.echo(
        "Changing Min/Max KSP Versions in: "
        f"{project.assembly_info.filepath.absolute().relative_to(cwd)}"
        + (" [DRY RUN]" if dry_run else "")
    )
    if dry_run:
        return
    project.assembly_info.save()


@click.command("update_KSP_references")
@click.argument(
    "ksp-path",
    type=click.Path(dir_okay=True, file_okay=False, exists=True, path_type=Path),
)
@click.option("--exclude", help="Exclude paths that include this regex")
@click.option(
    "--update-ksp-avc",
    is_flag=True,
    help="Also update KSP AVC version in AssemblyInfo.cs "
    "based on the readme.txt in the KSP installation folder",
)
@click.option("--dry-run", is_flag=True, help="Do not write anything to disk")
def cmd(
    ksp_path: Path, exclude: Optional[str], update_ksp_avc: bool, dry_run: bool
) -> None:
    """
    Changes references to KSP libraries in .csproj files recursively
    """
    cwd = Path.cwd()
    ksp_path = ksp_path.absolute()
    # construct and check the dlls path
    dlls_path = ksp_path / "KSP_Data" / "Managed"
    if not dlls_path.is_dir():
        click.echo(f"Directory does not exist: {dlls_path}")
        sys.exit(1)
    # handle the --exclude argument
    exclude_re: Optional[Pattern] = None
    if exclude:
        exclude_re = re.compile(exclude)
    # handle the --update-ksp-avc argument
    ksp_version: Optional[KspReadmeVersion] = None
    if update_ksp_avc:
        readme_file = ksp_path / "readme.txt"
        try:
            ksp_version = KspReadmeVersion.from_file_lines(readme_file)
        except FileNotFoundError:
            click.echo(f"No such file: {readme_file}", err=True)
    # process files and folders
    visited = set()
    path_stack = [cwd]
    while path_stack:
        cur_path = path_stack.pop()
        for sub_path in cur_path.iterdir():
            if exclude_re and exclude_re.search(str(sub_path)) is not None:
                click.echo(f"Skipping: {sub_path}")
                continue
            if sub_path.is_dir():
                path_stack.append(sub_path)
            elif sub_path.is_file() and sub_path.name.endswith(".csproj"):
                replace_references(cwd, ksp_path, sub_path, dry_run)
                project_path = sub_path.parent.absolute()
                if ksp_version and project_path not in visited:
                    visited.add(project_path)
                    replace_ksp_avc_versions(cwd, ksp_version, project_path, dry_run)
