"""Typer application entry point."""

from __future__ import annotations

import sys
from typing import Any

import typer
from typer.core import TyperGroup

from mcp_builder import __version__
from mcp_builder.cli.commands import doctor, generate, init, validate
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.domain.diagnostics import Codes


class OrderedGroup(TyperGroup):
    def list_commands(self, ctx: Any) -> list[str]:
        return list(self.commands)


app = typer.Typer(
    name="mcp-builder",
    help=(
        "Manifest-driven CLI that generates readable, tested Python MCP server projects "
        "with safe regeneration and optional Docker/CI assets."
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
    cls=OrderedGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Global state flags
_STATE: dict[str, bool] = {"verbose": False, "quiet": False, "no_color": False}


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"mcp-builder {__version__}")
        raise typer.Exit(code=int(ExitCode.SUCCESS))


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Show verbose errors."),
    quiet: bool = typer.Option(False, "--quiet", help="Minimize output."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output."),
) -> None:
    """MCP Builder Toolkit CLI."""
    _STATE["verbose"] = verbose
    _STATE["quiet"] = quiet
    _STATE["no_color"] = no_color


init.register(app)
validate.register(app)
generate.register(app)
doctor.register(app)


def main() -> None:
    try:
        app()
    except typer.Exit:
        raise
    except Exception as exc:
        if _STATE.get("verbose"):
            raise
        sys.stderr.write(f"error {Codes.INTERNAL}: unexpected internal error: {exc}\n")
        raise SystemExit(int(ExitCode.INTERNAL_ERROR)) from exc


if __name__ == "__main__":
    main()
