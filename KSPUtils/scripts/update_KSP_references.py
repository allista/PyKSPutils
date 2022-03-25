import os.path
import re
import sys
from io import StringIO
from pathlib import Path
from typing import Optional, Pattern

import click

assembly_re = re.compile(r"\s*<HintPath>(.*)\\KSP_Data\\Managed\\.*\.dll</HintPath>")


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


@click.command("update_KSP_references")
@click.argument(
    "ksp-path",
    type=click.Path(dir_okay=True, file_okay=False, exists=True, path_type=Path),
)
@click.option("--exclude", help="Exclude paths that include this regex")
@click.option("--dry-run", is_flag=True, help="Do not write anything to disk")
def cmd(ksp_path: Path, exclude: Optional[str], dry_run: bool) -> None:
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
    # process files and folders
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
