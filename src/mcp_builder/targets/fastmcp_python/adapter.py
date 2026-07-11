"""FastMCP Python target adapter."""

from __future__ import annotations

from typing import Any

from mcp_builder.domain.artifacts import ArtifactSpec
from mcp_builder.domain.diagnostics import Diagnostic, Ownership, Severity
from mcp_builder.domain.project import ProjectSpec, StreamableHttpTransport
from mcp_builder.generation.renderer import content_hash, make_env, render_template
from mcp_builder.targets.compatibility import CompatibilityProfile, CompatibilityRegistry

TEMPLATE_PACKAGE = "mcp_builder.targets.fastmcp_python"
TEMPLATES_DIR = "templates"


class FastMCPPythonAdapter:
    id = "fastmcp-python"

    def __init__(self, registry: CompatibilityRegistry | None = None) -> None:
        self._registry = registry or CompatibilityRegistry.default()
        self._env = make_env(TEMPLATE_PACKAGE, TEMPLATES_DIR)

    def compatibility_profile(self, project: ProjectSpec) -> CompatibilityProfile:
        return self._registry.require(project.target.profile)

    def validate(self, project: ProjectSpec) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        if project.target.runtime != "fastmcp-python":
            diagnostics.append(
                Diagnostic(
                    code="MBT-COMPAT-001",
                    severity=Severity.ERROR,
                    message=f"Adapter {self.id} cannot handle runtime {project.target.runtime}",
                    path="spec.target.runtime",
                )
            )
        if self._registry.get(project.target.profile) is None:
            diagnostics.append(
                Diagnostic(
                    code="MBT-COMPAT-001",
                    severity=Severity.ERROR,
                    message=f"Unknown profile: {project.target.profile}",
                    path="spec.target.profile",
                )
            )
        if isinstance(project.transport, StreamableHttpTransport):
            host = project.transport.host
            if host in {"0.0.0.0", "::", "[::]"}:
                diagnostics.append(
                    Diagnostic(
                        code="MBT-MANIFEST-004",
                        severity=Severity.WARNING,
                        message=(
                            f"HTTP host {host!r} binds broadly; "
                            "prefer 127.0.0.1 for local development"
                        ),
                        path="spec.transport.host",
                        hint=(
                            "Use 127.0.0.1 unless you intentionally expose the server "
                            "behind authentication and TLS."
                        ),
                    )
                )
            if not project.transport.path.startswith("/"):
                diagnostics.append(
                    Diagnostic(
                        code="MBT-MANIFEST-004",
                        severity=Severity.ERROR,
                        message="HTTP path must start with '/'",
                        path="spec.transport.path",
                    )
                )
        return diagnostics

    def plan(self, project: ProjectSpec) -> list[ArtifactSpec]:
        profile = self.compatibility_profile(project)
        ctx = self._context(project, profile)
        package = project.project.package_name
        artifacts: list[ArtifactSpec] = []

        managed_templates = [
            ("pyproject.toml.j2", "pyproject.toml"),
            ("gitignore.j2", ".gitignore"),
            ("env.example.j2", ".env.example"),
            ("README.md.j2", "README.md"),
        ]
        for template_name, dest in managed_templates:
            content = render_template(self._env, template_name, ctx)
            artifacts.append(
                ArtifactSpec(
                    relative_path=dest,
                    content=content,
                    content_hash=content_hash(content),
                    ownership=Ownership.MANAGED,
                    origin=f"target.fastmcp-python/{template_name}",
                )
            )

        scaffold_templates: list[tuple[str, str]] = [
            ("package/__init__.py.j2", f"src/{package}/__init__.py"),
            ("package/server.py.j2", f"src/{package}/server.py"),
            ("package/tools/__init__.py.j2", f"src/{package}/tools/__init__.py"),
        ]
        if project.scaffolds.example_tool:
            scaffold_templates.append(
                ("package/tools/example.py.j2", f"src/{package}/tools/example.py")
            )

        if project.features.tests:
            if project.scaffolds.example_tool:
                scaffold_templates.append(
                    ("tests/test_example_tool.py.j2", "tests/test_example_tool.py")
                )
            scaffold_templates.append(
                ("tests/test_server_smoke.py.j2", "tests/test_server_smoke.py")
            )

        for template_name, dest in scaffold_templates:
            content = render_template(self._env, template_name, ctx)
            artifacts.append(
                ArtifactSpec(
                    relative_path=dest,
                    content=content,
                    content_hash=content_hash(content),
                    ownership=Ownership.SCAFFOLD_ONCE,
                    origin=f"target.fastmcp-python/{template_name}",
                )
            )

        return artifacts

    def _context(self, project: ProjectSpec, profile: CompatibilityProfile) -> dict[str, Any]:
        is_http = isinstance(project.transport, StreamableHttpTransport)
        transport: dict[str, Any]
        if is_http:
            assert isinstance(project.transport, StreamableHttpTransport)
            transport = {
                "type": "streamable-http",
                "host": project.transport.host,
                "port": project.transport.port,
                "path": project.transport.path,
            }
        else:
            transport = {"type": "stdio"}

        return {
            "project": project,
            "metadata": project.metadata,
            "package_name": project.project.package_name,
            "python": project.project.python,
            "fastmcp_constraint": profile.fastmcp,
            "protocol_version": profile.protocol,
            "profile_id": profile.id,
            "transport": transport,
            "is_http": is_http,
            "features": project.features,
            "scaffolds": project.scaffolds,
            "display_name": project.metadata.display_name or project.metadata.name,
            "description": project.metadata.description
            or f"MCP server for {project.metadata.name}",
            "license": project.metadata.license or "Apache-2.0",
            "version": project.metadata.version,
        }
