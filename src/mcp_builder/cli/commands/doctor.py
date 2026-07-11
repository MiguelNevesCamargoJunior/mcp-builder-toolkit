"""mcp-builder doctor — project and environment health checks."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import typer

from mcp_builder import __version__
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.cli.output import render_text_result, write_json
from mcp_builder.domain.diagnostics import (
    Codes,
    CommandResult,
    CommandStatus,
    Diagnostic,
    DiagnosticSummary,
    Ownership,
    Severity,
    status_from_diagnostics,
)
from mcp_builder.domain.project import ProjectSpec
from mcp_builder.generation.renderer import content_hash
from mcp_builder.generation.state import state_path, try_load_state
from mcp_builder.manifest.loader import load_manifest_path
from mcp_builder.manifest.normalize import normalize
from mcp_builder.service import DEFAULT_MANIFEST, build_planner
from mcp_builder.targets.compatibility import CompatibilityRegistry

# Documentation anchors for remediation (stable relative links).
_DOCS = {
    Codes.MANIFEST_NOT_FOUND: "docs: run `mcp-builder init` or pass --file",
    Codes.MANIFEST_PARSE: "docs: fix YAML syntax; see contracts/manifest.schema.json",
    Codes.MANIFEST_SCHEMA: "docs: contracts/manifest.schema.json",
    Codes.MANIFEST_SEMANTIC: "docs: specs/001-core-builder/data-model.md",
    Codes.PROFILE_UNKNOWN: "docs: SUPPORT.md compatibility table",
    Codes.PROFILE_PYTHON: "docs: SUPPORT.md - use Python 3.12-3.13",
    Codes.PROFILE_PROTOCOL: "docs: SUPPORT.md protocol profile",
    Codes.GEN_CONFLICT: "docs: use generate --force-managed PATH after review",
    "MBT-DOCTOR-001": "docs: re-run `mcp-builder generate` to recreate expected files",
    "MBT-DOCTOR-002": "docs: managed file drift — restore or --force-managed",
    "MBT-DOCTOR-003": "docs: delete corrupt .mcp-builder/state.json and regenerate",
    "MBT-DOCTOR-010": "docs: install uv from https://docs.astral.sh/uv/",
    "MBT-DOCTOR-011": "docs: install Docker if you enabled docker/compose features",
}


def register(app: typer.Typer) -> None:
    @app.command("doctor")
    def doctor_cmd(
        directory: Path = typer.Argument(
            Path("."),
            help="Project directory.",
            file_okay=False,
            resolve_path=True,
        ),
        file: Path | None = typer.Option(
            None,
            "--file",
            "-f",
            help="Manifest path (defaults to <directory>/mcp-builder.yaml).",
            resolve_path=True,
        ),
        format: str = typer.Option("text", "--format", help="Output format: text or json."),
        strict: bool = typer.Option(False, "--strict"),
    ) -> None:
        """Check manifest, profile, state, drift, and local tools."""
        result = run_doctor(directory=directory, file=file, strict=strict)
        if format == "json":
            write_json(result)
        else:
            render_text_result(result)

        if result.status is CommandStatus.ERROR:
            raise typer.Exit(code=int(ExitCode.DOCTOR_UNHEALTHY))


def run_doctor(
    *,
    directory: Path,
    file: Path | None,
    strict: bool = False,
) -> CommandResult:
    diagnostics: list[Diagnostic] = []
    if file is not None:
        manifest_path = file.resolve()
        directory = manifest_path.parent
    else:
        directory = directory.resolve()
        manifest_path = directory / DEFAULT_MANIFEST

    loaded = load_manifest_path(manifest_path)
    diagnostics.extend(loaded.diagnostics)

    project: ProjectSpec | None = None
    if loaded.manifest is not None:
        project, norm_diags = normalize(loaded.manifest)
        diagnostics.extend(norm_diags)
        if project is not None:
            registry = CompatibilityRegistry.default()
            profile = registry.get(project.target.profile)
            if profile is None:
                diagnostics.append(
                    Diagnostic(
                        code=Codes.PROFILE_UNKNOWN,
                        severity=Severity.ERROR,
                        message=f"Unknown profile: {project.target.profile}",
                        path="spec.target.profile",
                        hint=_DOCS[Codes.PROFILE_UNKNOWN],
                    )
                )
            else:
                diagnostics.append(
                    Diagnostic(
                        code="MBT-COMPAT-011",
                        severity=Severity.INFO,
                        message=(
                            f"Profile {profile.id} ok "
                            f"(fastmcp {profile.fastmcp}, protocol {profile.protocol})"
                        ),
                    )
                )

    diagnostics.extend(_python_checks())
    diagnostics.extend(_state_checks(directory))
    if project is not None:
        diagnostics.extend(_expected_and_drift_checks(directory, project))
        diagnostics.extend(_tool_checks(project))

    if strict:
        # Promote warnings that are marked as strict-compatible (none yet beyond recompute).
        pass

    # Attach default hints for known codes missing hints
    for d in diagnostics:
        if d.hint is None and d.code in _DOCS:
            d.hint = _DOCS[d.code]

    return CommandResult(
        command="doctor",
        status=status_from_diagnostics(diagnostics),
        builderVersion=__version__,
        diagnostics=diagnostics,
        summary=DiagnosticSummary.from_diagnostics(diagnostics),
    )


def _python_checks() -> list[Diagnostic]:
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 12) or (major, minor) >= (3, 14):
        return [
            Diagnostic(
                code=Codes.PROFILE_PYTHON,
                severity=Severity.WARNING,
                message=f"Python {major}.{minor} is outside the supported range 3.12-3.13",
                hint=_DOCS[Codes.PROFILE_PYTHON],
            )
        ]
    return [
        Diagnostic(
            code="MBT-COMPAT-010",
            severity=Severity.INFO,
            message=f"Python {major}.{minor} is supported",
        )
    ]


def _state_checks(directory: Path) -> list[Diagnostic]:
    path = state_path(directory)
    if not path.exists():
        return [
            Diagnostic(
                code="MBT-GEN-020",
                severity=Severity.INFO,
                message="No build state found (project may not be generated yet)",
                path=str(path),
            )
        ]
    state, err = try_load_state(directory)
    if err is not None or state is None:
        return [
            Diagnostic(
                code="MBT-DOCTOR-003",
                severity=Severity.ERROR,
                message=f"Build state is corrupt or unreadable: {err or 'unknown'}",
                path=str(path),
                hint=_DOCS["MBT-DOCTOR-003"],
            )
        ]
    return [
        Diagnostic(
            code="MBT-GEN-021",
            severity=Severity.INFO,
            message=(
                f"Build state present (builder {state.builder_version}, profile {state.profile})"
            ),
            path=str(path),
        )
    ]


def _expected_and_drift_checks(directory: Path, project: ProjectSpec) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    plan = build_planner().plan(project, directory)
    state, _err = try_load_state(directory)

    for art in plan.artifacts:
        dest = directory / art.relative_path
        if not dest.is_file():
            # Missing scaffold-once after first generate is info; missing managed is warning/error
            severity = Severity.WARNING if art.ownership is Ownership.MANAGED else Severity.INFO
            diagnostics.append(
                Diagnostic(
                    code="MBT-DOCTOR-001",
                    severity=severity,
                    message=f"Expected generated file is missing: {art.relative_path}",
                    path=art.relative_path,
                    hint=_DOCS["MBT-DOCTOR-001"],
                    details={"ownership": art.ownership.value},
                )
            )
            continue

        if art.ownership is Ownership.SCAFFOLD_ONCE:
            # Never treat scaffold edits as drift
            continue

        if art.ownership is Ownership.MANAGED and state is not None:
            prev = state.artifacts.get(art.relative_path.replace("\\", "/"))
            current = content_hash(dest.read_text(encoding="utf-8"))
            drifted = (
                prev is not None and current != prev.generated_hash and current != art.content_hash
            )
            if drifted:
                diagnostics.append(
                    Diagnostic(
                        code="MBT-DOCTOR-002",
                        severity=Severity.WARNING,
                        message=f"Managed file has drifted from last generation: {art.relative_path}",
                        path=art.relative_path,
                        hint=_DOCS["MBT-DOCTOR-002"],
                    )
                )
    return diagnostics


def _tool_checks(project: ProjectSpec) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if shutil.which("uv") is None:
        diagnostics.append(
            Diagnostic(
                code="MBT-DOCTOR-010",
                severity=Severity.WARNING,
                message="uv executable not found on PATH",
                hint=_DOCS["MBT-DOCTOR-010"],
            )
        )
    else:
        diagnostics.append(
            Diagnostic(
                code="MBT-DOCTOR-012",
                severity=Severity.INFO,
                message="uv is available",
            )
        )

    if project.features.docker or project.features.compose:
        if shutil.which("docker") is None:
            diagnostics.append(
                Diagnostic(
                    code="MBT-DOCTOR-011",
                    severity=Severity.WARNING,
                    message="Docker executable not found (required by enabled docker/compose features)",
                    hint=_DOCS["MBT-DOCTOR-011"],
                )
            )
        else:
            diagnostics.append(
                Diagnostic(
                    code="MBT-DOCTOR-013",
                    severity=Severity.INFO,
                    message="docker is available",
                )
            )
    return diagnostics
