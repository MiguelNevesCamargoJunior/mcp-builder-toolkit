"""mcp-builder validate command."""

from __future__ import annotations

from pathlib import Path

import typer

from mcp_builder import __version__
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.cli.output import render_text_result, write_json
from mcp_builder.domain.diagnostics import (
    CommandResult,
    CommandStatus,
    Diagnostic,
    DiagnosticSummary,
    status_from_diagnostics,
)
from mcp_builder.manifest.loader import load_manifest_path
from mcp_builder.manifest.normalize import normalize
from mcp_builder.service import DEFAULT_MANIFEST


def register(app: typer.Typer) -> None:
    @app.command("validate")
    def validate_cmd(
        file: Path = typer.Option(
            Path(DEFAULT_MANIFEST),
            "--file",
            "-f",
            help="Path to the project manifest.",
            resolve_path=True,
        ),
        format: str = typer.Option("text", "--format", help="Output format: text or json."),
        strict: bool = typer.Option(
            False,
            "--strict",
            help="Promote strict-compatible warnings to errors.",
        ),
    ) -> None:
        """Validate syntax, schema, semantics, and compatibility."""
        result = run_validate(file=file, strict=strict)
        if format == "json":
            write_json(result)
        else:
            render_text_result(result)

        if result.status is CommandStatus.ERROR:
            raise typer.Exit(code=int(ExitCode.USAGE_OR_VALIDATION))


def run_validate(*, file: Path, strict: bool = False) -> CommandResult:
    diagnostics: list[Diagnostic] = []
    loaded = load_manifest_path(file)
    diagnostics.extend(loaded.diagnostics)

    if loaded.manifest is not None:
        _, norm_diags = normalize(loaded.manifest)
        diagnostics.extend(norm_diags)

    if strict:
        # Future: promote marked warnings; no-op for now beyond recompute
        pass

    return CommandResult(
        command="validate",
        status=status_from_diagnostics(diagnostics),
        builderVersion=__version__,
        diagnostics=diagnostics,
        summary=DiagnosticSummary.from_diagnostics(diagnostics),
    )
