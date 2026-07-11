"""Artifact planning types shared by adapters and the filesystem layer."""

from __future__ import annotations

from dataclasses import dataclass, field

from mcp_builder.domain.diagnostics import Diagnostic, Ownership


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    """A single desired generated file."""

    relative_path: str
    content: str
    content_hash: str
    ownership: Ownership
    origin: str
    mode: int | None = None


@dataclass(slots=True)
class ArtifactPlan:
    """Complete proposed filesystem change set before apply."""

    project_root: str
    manifest_hash: str
    builder_version: str
    profile: str
    artifacts: list[ArtifactSpec] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
