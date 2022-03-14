import sys
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.exit_code_context import ExitCodeContext, OnErrorHandler


def on_error_echo(message: str, _exit_code: int) -> None:
    click.echo(message, err=True)


def get_project(ctx: click.Context) -> CSharpProject:
    return cast(CSharpProject, ctx.obj)


F = TypeVar("F", bound=Callable[..., Any])


def pass_project(f: F) -> F:
    @click.pass_context
    @wraps(f)
    def project_context_wrapper(ctx: click.Context, *args, **kwargs):
        return f(get_project(ctx), *args, **kwargs)

    return cast(F, project_context_wrapper)


def sys_exit(project: CSharpProject) -> None:
    sys.exit(project.context.exit_code)


def create_project_cmd(on_error: OnErrorHandler = on_error_echo) -> click.Group:
    @click.group()
    @click.pass_context
    def cmd(ctx: click.Context):
        ctx.obj = CSharpProject(
            Path.cwd(),
            errors_context=ExitCodeContext(on_error, FileNotFoundError),
        )

    return cmd
