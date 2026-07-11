"""Internal adapter and feature generator protocols (v0.1, not stable)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mcp_builder.domain.artifacts import ArtifactSpec
from mcp_builder.domain.diagnostics import Diagnostic
from mcp_builder.domain.project import ProjectSpec
from mcp_builder.targets.compatibility import CompatibilityProfile


@runtime_checkable
class TargetAdapter(Protocol):
    id: str

    def validate(self, project: ProjectSpec) -> list[Diagnostic]: ...

    def plan(self, project: ProjectSpec) -> list[ArtifactSpec]: ...

    def compatibility_profile(self, project: ProjectSpec) -> CompatibilityProfile: ...


@runtime_checkable
class FeatureGenerator(Protocol):
    id: str

    def supports(self, project: ProjectSpec) -> bool: ...

    def validate(self, project: ProjectSpec) -> list[Diagnostic]: ...

    def plan(self, project: ProjectSpec) -> list[ArtifactSpec]: ...
