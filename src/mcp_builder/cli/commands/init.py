"""mcp-builder init command."""

from __future__ import annotations

import keyword
import re
from enum import StrEnum
from pathlib import Path

import typer
import yaml

from mcp_builder import __version__
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.cli.output import OutputFormat, output_is_quiet, render_text_result, write_json
from mcp_builder.domain.diagnostics import (
    Codes,
    CommandResult,
    CommandStatus,
    Diagnostic,
    DiagnosticSummary,
    Severity,
    status_from_diagnostics,
)
from mcp_builder.manifest.normalize import name_to_package
from mcp_builder.targets.compatibility import (
    DEFAULT_PROFILE_ID,
    CompatibilityRegistry,
)

DEFAULT_PROFILE = DEFAULT_PROFILE_ID
MANIFEST_NAME = "mcp-builder.yaml"


class TransportChoice(StrEnum):
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable-http"


def register(app: typer.Typer) -> None:
    @app.command("init")
    def init_cmd(
        directory: Path = typer.Argument(
            Path("."),
            help="Target directory for the new manifest.",
            file_okay=False,
            resolve_path=True,
        ),
        name: str | None = typer.Option(None, "--name", help="Project name (DNS-label style)."),
        transport: TransportChoice = typer.Option(
            TransportChoice.STDIO,
            "--transport",
            help="Transport: stdio or streamable-http.",
        ),
        profile: str = typer.Option(DEFAULT_PROFILE, "--profile", help="Compatibility profile."),
        no_interactive: bool = typer.Option(
            False,
            "--no-interactive",
            help="Do not prompt; use flags and defaults.",
        ),
        format: OutputFormat = typer.Option(
            OutputFormat.TEXT, "--format", help="Output format: text or json."
        ),
    ) -> None:
        """Create a minimal mcp-builder.yaml manifest."""
        result = run_init(
            directory=directory,
            name=name,
            transport=transport.value,
            profile=profile,
            no_interactive=no_interactive,
            force_empty=False,
        )
        if format is OutputFormat.JSON:
            write_json(result)
        else:
            render_text_result(result)
            if result.status is CommandStatus.OK and not output_is_quiet():
                typer.echo("Created mcp-builder.yaml")
                typer.echo("Next: mcp-builder validate && mcp-builder generate")

        if result.status is CommandStatus.ERROR:
            raise typer.Exit(code=int(ExitCode.USAGE_OR_VALIDATION))


def run_init(
    *,
    directory: Path,
    name: str | None,
    transport: str,
    profile: str,
    no_interactive: bool,
    force_empty: bool,
) -> CommandResult:
    diagnostics: list[Diagnostic] = []
    directory = directory.resolve()

    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)

    _ = force_empty  # retained for the internal alpha API; no public flag

    manifest_path = directory / MANIFEST_NAME
    if manifest_path.exists():
        diagnostics.append(
            Diagnostic(
                code=Codes.INIT_EXISTS,
                severity=Severity.ERROR,
                message=f"Manifest already exists: {manifest_path}",
                path=str(manifest_path),
                hint="Remove it or choose another directory.",
            )
        )
        return _result(diagnostics)

    project_name = name
    if project_name is None:
        if no_interactive:
            project_name = directory.name if directory.name not in {".", ""} else "my-mcp-server"
        else:
            project_name = typer.prompt("Project name", default=directory.name or "my-mcp-server")

    if transport not in {"stdio", "streamable-http"}:
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_SEMANTIC,
                severity=Severity.ERROR,
                message=f"Unsupported transport: {transport}",
                path="spec.transport.type",
                hint="Use 'stdio' or 'streamable-http'.",
            )
        )
        return _result(diagnostics)

    try:
        package = name_to_package(project_name)
    except ValueError as exc:
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_SEMANTIC,
                severity=Severity.ERROR,
                message=str(exc),
                path="metadata.name",
            )
        )
        return _result(diagnostics)

    if not re.match(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", project_name):
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_SEMANTIC,
                severity=Severity.ERROR,
                message=(
                    f"Project name must be a valid DNS label "
                    f"(lowercase alphanumeric + hyphens): {project_name!r}"
                ),
                path="metadata.name",
            )
        )
        return _result(diagnostics)

    if keyword.iskeyword(package):
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_SEMANTIC,
                severity=Severity.ERROR,
                message=f"Derived package name {package!r} is a Python keyword",
                path="project.packageName",
            )
        )
        return _result(diagnostics)

    registry = CompatibilityRegistry.default()
    if registry.get(profile) is None:
        diagnostics.append(
            Diagnostic(
                code=Codes.PROFILE_UNKNOWN,
                severity=Severity.ERROR,
                message=f"Unknown profile: {profile!r}",
                path="spec.target.profile",
                hint=f"Supported: {', '.join(registry.ids())}",
            )
        )
        return _result(diagnostics)

    data = _minimal_manifest(
        name=project_name,
        package=package,
        transport=transport,
        profile=profile,
    )
    text = yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
    try:
        manifest_path.write_text(text, encoding="utf-8")
    except OSError as exc:
        diagnostics.append(
            Diagnostic(
                code=Codes.GEN_IO,
                severity=Severity.ERROR,
                message=f"Failed to write manifest: {exc}",
                path=str(manifest_path),
            )
        )
        return _result(diagnostics)

    diagnostics.append(
        Diagnostic(
            code=Codes.INIT_SUCCESS,
            severity=Severity.INFO,
            message=f"Created {MANIFEST_NAME}",
            path=str(manifest_path),
        )
    )
    return _result(diagnostics)


def _minimal_manifest(
    *,
    name: str,
    package: str,
    transport: str,
    profile: str,
) -> dict[str, object]:
    compatibility = CompatibilityRegistry.default().require(profile)
    transport_block: dict[str, object]
    if transport == "streamable-http":
        transport_block = {
            "type": "streamable-http",
            "host": "127.0.0.1",
            "port": 8000,
            "path": "/mcp",
        }
    else:
        transport_block = {"type": "stdio"}

    return {
        "apiVersion": "mcpbuilder.dev/v1alpha1",
        "kind": "MCPServerProject",
        "metadata": {
            "name": name,
            "version": "0.1.0",
            "license": "Apache-2.0",
        },
        "spec": {
            "target": {
                "runtime": "fastmcp-python",
                "profile": profile,
                "protocolVersion": compatibility.protocol,
            },
            "project": {
                "python": compatibility.python,
                "packageName": package,
                "layout": "src",
                "dependencyManager": "uv",
            },
            "transport": transport_block,
            "features": {
                "tests": True,
                "lint": True,
                "typing": True,
                "docker": False,
                "compose": False,
                "githubActions": True,
                "structuredLogging": True,
            },
            "scaffolds": {
                "exampleTool": True,
            },
        },
    }


def _result(diagnostics: list[Diagnostic]) -> CommandResult:
    return CommandResult(
        command="init",
        status=status_from_diagnostics(diagnostics),
        builderVersion=__version__,
        diagnostics=diagnostics,
        summary=DiagnosticSummary.from_diagnostics(diagnostics),
    )
