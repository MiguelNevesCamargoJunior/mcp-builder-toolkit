"""mcp-builder generate command."""

from __future__ import annotations

from pathlib import Path

import typer

from mcp_builder import __version__
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.cli.output import OutputFormat, render_text_result, write_json
from mcp_builder.domain.diagnostics import (
    Codes,
    CommandResult,
    CommandStatus,
    Diagnostic,
    DiagnosticSummary,
    Severity,
    status_from_diagnostics,
)
from mcp_builder.generation.lock import GenerationLock, GenerationLockError
from mcp_builder.generation.transaction import apply_plan
from mcp_builder.manifest.loader import load_manifest_path
from mcp_builder.manifest.normalize import normalize
from mcp_builder.service import DEFAULT_MANIFEST, build_planner


def register(app: typer.Typer) -> None:
    @app.command("generate")
    def generate_cmd(
        file: Path = typer.Option(
            Path(DEFAULT_MANIFEST),
            "--file",
            "-f",
            help="Path to the project manifest.",
            resolve_path=True,
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Project root (defaults to manifest directory).",
            resolve_path=True,
            file_okay=False,
        ),
        dry_run: bool = typer.Option(False, "--dry-run", help="Show plan without writing."),
        format: OutputFormat = typer.Option(
            OutputFormat.TEXT, "--format", help="Output format: text or json."
        ),
        force_managed: list[Path] = typer.Option(
            None,
            "--force-managed",
            help="Overwrite a named managed path that conflicts.",
        ),
    ) -> None:
        """Validate, plan, and generate project files."""
        result, exit_code = run_generate(
            file=file,
            output=output,
            dry_run=dry_run,
            force_managed={str(p) for p in (force_managed or [])},
        )
        if format is OutputFormat.JSON:
            write_json(result)
        else:
            render_text_result(result)

        if exit_code != ExitCode.SUCCESS:
            raise typer.Exit(code=int(exit_code))


def run_generate(
    *,
    file: Path,
    output: Path | None,
    dry_run: bool,
    force_managed: set[str],
) -> tuple[CommandResult, ExitCode]:
    diagnostics: list[Diagnostic] = []
    file = file.resolve()
    loaded = load_manifest_path(file)
    diagnostics.extend(loaded.diagnostics)

    if loaded.manifest is None:
        result = CommandResult(
            command="generate",
            status=status_from_diagnostics(diagnostics),
            builderVersion=__version__,
            diagnostics=diagnostics,
            summary=DiagnosticSummary.from_diagnostics(diagnostics),
        )
        return result, ExitCode.USAGE_OR_VALIDATION

    project, norm_diags = normalize(loaded.manifest)
    diagnostics.extend(norm_diags)
    if project is None:
        result = CommandResult(
            command="generate",
            status=status_from_diagnostics(diagnostics),
            builderVersion=__version__,
            diagnostics=diagnostics,
            summary=DiagnosticSummary.from_diagnostics(diagnostics),
        )
        return result, ExitCode.USAGE_OR_VALIDATION

    project_root = (output or file.parent).resolve()
    planner = build_planner()
    plan = planner.plan(project, project_root)
    diagnostics.extend(plan.diagnostics)

    if any(d.severity is Severity.ERROR for d in diagnostics):
        # Still classify for dry-run visibility when plan is empty due to errors
        apply = apply_plan(
            plan,
            project_root,
            dry_run=True,
            force_managed=force_managed,
        )
        all_diags = _dedup(diagnostics + apply.diagnostics)
        result = CommandResult(
            command="generate",
            status=CommandStatus.ERROR,
            builderVersion=__version__,
            diagnostics=all_diags,
            summary=DiagnosticSummary.from_diagnostics(all_diags),
            changes=apply.changes or None,
        )
        if any(d.code == Codes.GEN_CONFLICT for d in all_diags):
            return result, ExitCode.GENERATION_CONFLICT
        return result, ExitCode.USAGE_OR_VALIDATION

    # Dry-run does not need the exclusive lock; apply does.
    if dry_run:
        apply = apply_plan(
            plan,
            project_root,
            dry_run=True,
            force_managed=force_managed,
        )
    else:
        try:
            with GenerationLock(project_root):
                apply = apply_plan(
                    plan,
                    project_root,
                    dry_run=False,
                    force_managed=force_managed,
                )
        except GenerationLockError as exc:
            all_diags = _dedup([*diagnostics, exc.diagnostic])
            result = CommandResult(
                command="generate",
                status=CommandStatus.ERROR,
                builderVersion=__version__,
                diagnostics=all_diags,
                summary=DiagnosticSummary.from_diagnostics(all_diags),
            )
            return result, ExitCode.FILESYSTEM_FAILURE

    all_diags = _dedup(diagnostics + apply.diagnostics)
    result = CommandResult(
        command="generate",
        status=status_from_diagnostics(all_diags),
        builderVersion=__version__,
        diagnostics=all_diags,
        summary=DiagnosticSummary.from_diagnostics(all_diags),
        changes=apply.changes,
    )

    if any(d.severity is Severity.ERROR for d in all_diags):
        if any(d.code == Codes.GEN_CONFLICT for d in all_diags):
            return result, ExitCode.GENERATION_CONFLICT
        if any(d.code in {Codes.GEN_IO, Codes.GEN_LOCK} for d in all_diags):
            return result, ExitCode.FILESYSTEM_FAILURE
        return result, ExitCode.USAGE_OR_VALIDATION

    return result, ExitCode.SUCCESS


def _dedup(diags: list[Diagnostic]) -> list[Diagnostic]:
    seen: set[tuple[str, str | None, str]] = set()
    out: list[Diagnostic] = []
    for d in diags:
        key = (d.code, d.path, d.message)
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out
