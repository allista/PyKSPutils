import sys
from functools import wraps
from pathlib import Path
from typing import Any, Callable, NoReturn, Optional, TypeVar, cast

import click

from KSPUtils.project_info.csharp_project import CSharpProject
from KSPUtils.scripts.exit_code_context import ExitCodeContext, OnErrorHandler


def on_error_exit(_message: str, exit_code: int) -> NoReturn:
    sys.exit(exit_code)


def get_project(ctx: click.Context) -> CSharpProject:
    return cast(CSharpProject, ctx.obj)


F = TypeVar("F", bound=Callable[..., Any])
D = Callable[[F], F]


def pass_project(load=True, on_error: Optional[OnErrorHandler] = None) -> D:
    def deco(f: F) -> F:
        @click.pass_context
        @wraps(f)
        def project_context_wrapper(ctx: click.Context, *args, **kwargs):
            project = get_project(ctx)
            if load:
                project.load(on_error=on_error)
            elif on_error:
                project.context.on_error = on_error
            return f(project, *args, **kwargs)

        return cast(F, project_context_wrapper)

    return deco


def sys_exit(project: CSharpProject) -> NoReturn:
    sys.exit(project.context.exit_code)


def create_project_cmd(on_error: Optional[OnErrorHandler] = None) -> click.Group:
    @click.group()
    @click.pass_context
    def cmd(ctx: click.Context):
        ctx.obj = CSharpProject(
            Path.cwd(),
            errors_context=ExitCodeContext(FileNotFoundError, on_error=on_error),
        )

    return cmd
