"""Text and JSON rendering for command results."""

from __future__ import annotations

import sys
from enum import StrEnum
from typing import TextIO

from rich.console import Console
from rich.table import Table

from mcp_builder.domain.diagnostics import (
    CommandResult,
    CommandStatus,
    Diagnostic,
    PlannedChange,
    Severity,
)

_OUTPUT_OPTIONS = {"no_color": False, "quiet": False}


class OutputFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


def configure_output(*, no_color: bool, quiet: bool) -> None:
    _OUTPUT_OPTIONS["no_color"] = no_color
    _OUTPUT_OPTIONS["quiet"] = quiet


def output_is_quiet() -> bool:
    return _OUTPUT_OPTIONS["quiet"]


def make_console(*, no_color: bool = False, quiet: bool = False) -> Console:
    no_color = no_color or _OUTPUT_OPTIONS["no_color"]
    quiet = quiet or _OUTPUT_OPTIONS["quiet"]
    return Console(
        stderr=False,
        force_terminal=None if not no_color else False,
        no_color=no_color,
        quiet=quiet,
    )


def make_error_console(*, no_color: bool = False) -> Console:
    no_color = no_color or _OUTPUT_OPTIONS["no_color"]
    return Console(stderr=True, no_color=no_color)


def render_text_result(
    result: CommandResult,
    *,
    console: Console | None = None,
    err_console: Console | None = None,
) -> None:
    out = console or make_console()
    err = err_console or make_error_console()

    if result.changes is not None:
        _render_changes(result.changes, out)

    for diag in result.diagnostics:
        stream = err if diag.severity is Severity.ERROR else out
        _render_diagnostic(diag, stream)

    if result.status is CommandStatus.OK and not result.diagnostics:
        out.print(f"[green]{result.command}: ok[/green]")
    elif result.status is CommandStatus.OK:
        out.print(
            f"[green]{result.command}: ok[/green] "
            f"({result.summary.errors} errors, {result.summary.warnings} warnings)"
        )
    elif result.status is CommandStatus.WARNING:
        out.print(
            f"[yellow]{result.command}: warning[/yellow] "
            f"({result.summary.errors} errors, {result.summary.warnings} warnings)"
        )
    else:
        err.print(
            f"[red]{result.command}: error[/red] "
            f"({result.summary.errors} errors, {result.summary.warnings} warnings)"
        )


def _render_diagnostic(diag: Diagnostic, console: Console) -> None:
    color = {
        Severity.INFO: "blue",
        Severity.WARNING: "yellow",
        Severity.ERROR: "red",
    }[diag.severity]
    loc = f" ({diag.path})" if diag.path else ""
    console.print(f"[{color}]{diag.severity.value}[/{color}] {diag.code}{loc}: {diag.message}")
    if diag.hint:
        console.print(f"  hint: {diag.hint}")


def _render_changes(changes: list[PlannedChange], console: Console) -> None:
    if not changes:
        console.print("No planned file changes.")
        return
    table = Table(title="Planned changes")
    table.add_column("Action")
    table.add_column("Ownership")
    table.add_column("Path")
    for change in sorted(changes, key=lambda c: c.path):
        table.add_row(change.action.value, change.ownership.value, change.path)
    console.print(table)


def write_json(result: CommandResult, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    target.write(result.model_dump_json_envelope())
    target.write("\n")
