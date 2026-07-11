"""Normalize validated manifests into immutable ProjectSpec."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from mcp_builder.domain.diagnostics import Codes, Diagnostic, Severity
from mcp_builder.domain.project import (
    FeatureSelection,
    ProjectMetadata,
    ProjectSpec,
    PythonProjectSpec,
    ScaffoldSelection,
    StdioTransport,
    StreamableHttpTransport,
    TargetSpec,
)
from mcp_builder.manifest.models import (
    ManifestModel,
    StdioTransportModel,
    StreamableHttpTransportModel,
)
from mcp_builder.targets.compatibility import CompatibilityRegistry

_PYTHON_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def name_to_package(name: str) -> str:
    """Derive a Python package identifier from a DNS-label project name."""
    package = name.replace("-", "_")
    if package[0].isdigit():
        package = f"pkg_{package}"
    if not _PYTHON_IDENTIFIER.match(package):
        raise ValueError(f"cannot derive package name from {name!r}")
    return package


def normalize(manifest: ManifestModel) -> tuple[ProjectSpec | None, list[Diagnostic]]:
    """Convert a validated manifest into ProjectSpec with semantic checks."""
    diagnostics: list[Diagnostic] = []
    registry = CompatibilityRegistry.default()

    profile = registry.get(manifest.spec.target.profile)
    if profile is None:
        diagnostics.append(
            Diagnostic(
                code=Codes.PROFILE_UNKNOWN,
                severity=Severity.ERROR,
                message=f"Unknown compatibility profile: {manifest.spec.target.profile}",
                path="spec.target.profile",
                hint=f"Supported profiles: {', '.join(registry.ids())}",
            )
        )
    else:
        if manifest.spec.target.protocol_version != profile.protocol:
            diagnostics.append(
                Diagnostic(
                    code=Codes.PROFILE_PROTOCOL,
                    severity=Severity.ERROR,
                    message=(
                        f"Protocol version {manifest.spec.target.protocol_version} "
                        f"does not match profile {profile.id} "
                        f"(expected {profile.protocol})"
                    ),
                    path="spec.target.protocolVersion",
                )
            )
        if manifest.spec.project.python != profile.python:
            diagnostics.append(
                Diagnostic(
                    code=Codes.PROFILE_PYTHON,
                    severity=Severity.ERROR,
                    message=(
                        f"Python constraint {manifest.spec.project.python!r} "
                        f"does not match profile {profile.id} "
                        f"(expected {profile.python!r})"
                    ),
                    path="spec.project.python",
                    hint=f"Use python: {profile.python!r}",
                )
            )

    # Feature dependency already enforced in FeaturesModel; restate as diagnostic if needed
    if manifest.spec.features.compose and not manifest.spec.features.docker:
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_SEMANTIC,
                severity=Severity.ERROR,
                message="features.compose requires features.docker",
                path="spec.features.compose",
            )
        )

    if diagnostics:
        return None, diagnostics

    transport_model = manifest.spec.transport
    if isinstance(transport_model, StdioTransportModel):
        transport: StdioTransport | StreamableHttpTransport = StdioTransport()
    elif isinstance(transport_model, StreamableHttpTransportModel):
        transport = StreamableHttpTransport(
            host=transport_model.host,
            port=transport_model.port,
            path=transport_model.path,
        )
    else:  # pragma: no cover — pydantic discriminator
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_SEMANTIC,
                severity=Severity.ERROR,
                message="Unsupported transport type",
                path="spec.transport.type",
                hint="Use 'stdio' or 'streamable-http'.",
            )
        )
        return None, diagnostics

    spec = ProjectSpec(
        api_version=manifest.api_version,
        kind=manifest.kind,
        metadata=ProjectMetadata(
            name=manifest.metadata.name,
            version=manifest.metadata.version,
            display_name=manifest.metadata.display_name,
            description=manifest.metadata.description,
            license=manifest.metadata.license,
        ),
        target=TargetSpec(
            runtime=manifest.spec.target.runtime,
            profile=manifest.spec.target.profile,
            protocol_version=manifest.spec.target.protocol_version,
        ),
        project=PythonProjectSpec(
            python=manifest.spec.project.python,
            package_name=manifest.spec.project.package_name,
            layout=manifest.spec.project.layout,
            dependency_manager=manifest.spec.project.dependency_manager,
        ),
        transport=transport,
        features=FeatureSelection(
            tests=manifest.spec.features.tests,
            lint=manifest.spec.features.lint,
            typing=manifest.spec.features.typing,
            docker=manifest.spec.features.docker,
            compose=manifest.spec.features.compose,
            github_actions=manifest.spec.features.github_actions,
            structured_logging=manifest.spec.features.structured_logging,
        ),
        scaffolds=ScaffoldSelection(
            example_tool=manifest.spec.scaffolds.example_tool,
        ),
    )
    return spec, diagnostics


def project_spec_to_canonical_dict(spec: ProjectSpec) -> dict[str, Any]:
    """Deterministic dict for hashing (sorted keys, stable shape)."""
    transport: dict[str, Any]
    if isinstance(spec.transport, StreamableHttpTransport):
        transport = {
            "type": "streamable-http",
            "host": spec.transport.host,
            "port": spec.transport.port,
            "path": spec.transport.path,
        }
    else:
        transport = {"type": "stdio"}

    return {
        "apiVersion": spec.api_version,
        "kind": spec.kind,
        "metadata": {
            "name": spec.metadata.name,
            "displayName": spec.metadata.display_name,
            "description": spec.metadata.description,
            "version": spec.metadata.version,
            "license": spec.metadata.license,
        },
        "spec": {
            "target": {
                "runtime": spec.target.runtime,
                "profile": spec.target.profile,
                "protocolVersion": spec.target.protocol_version,
            },
            "project": {
                "python": spec.project.python,
                "packageName": spec.project.package_name,
                "layout": spec.project.layout,
                "dependencyManager": spec.project.dependency_manager,
            },
            "transport": transport,
            "features": {
                "tests": spec.features.tests,
                "lint": spec.features.lint,
                "typing": spec.features.typing,
                "docker": spec.features.docker,
                "compose": spec.features.compose,
                "githubActions": spec.features.github_actions,
                "structuredLogging": spec.features.structured_logging,
            },
            "scaffolds": {
                "exampleTool": spec.scaffolds.example_tool,
            },
        },
    }


def manifest_hash(spec: ProjectSpec) -> str:
    """SHA-256 of canonical JSON serialization."""
    payload = json.dumps(
        project_spec_to_canonical_dict(spec),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
