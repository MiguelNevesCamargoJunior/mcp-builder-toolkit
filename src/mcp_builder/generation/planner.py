"""Compose target adapter and feature modules into an ArtifactPlan."""

from __future__ import annotations

from pathlib import Path

from mcp_builder import __version__
from mcp_builder.domain.artifacts import ArtifactPlan, ArtifactSpec
from mcp_builder.domain.diagnostics import Codes, Diagnostic, Severity
from mcp_builder.domain.project import ProjectSpec
from mcp_builder.generation.interfaces import FeatureGenerator, TargetAdapter
from mcp_builder.manifest.normalize import manifest_hash
from mcp_builder.manifest.paths import normalize_relative_path


class GenerationPlanner:
    def __init__(
        self,
        adapter: TargetAdapter,
        features: list[FeatureGenerator] | None = None,
    ) -> None:
        self._adapter = adapter
        self._features = features or []

    def plan(self, project: ProjectSpec, project_root: Path) -> ArtifactPlan:
        diagnostics: list[Diagnostic] = []
        artifacts: list[ArtifactSpec] = []

        diagnostics.extend(self._adapter.validate(project))
        for feature in self._features:
            if feature.supports(project):
                diagnostics.extend(feature.validate(project))

        if any(d.severity is Severity.ERROR for d in diagnostics):
            return ArtifactPlan(
                project_root=str(project_root.resolve()),
                manifest_hash=manifest_hash(project),
                builder_version=__version__,
                profile=project.target.profile,
                artifacts=[],
                diagnostics=diagnostics,
            )

        artifacts.extend(self._adapter.plan(project))
        for feature in self._features:
            if feature.supports(project):
                artifacts.extend(feature.plan(project))

        # Duplicate destination check
        seen: dict[str, str] = {}
        for art in artifacts:
            try:
                key = normalize_relative_path(art.relative_path)
            except ValueError as exc:
                diagnostics.append(
                    Diagnostic(
                        code=Codes.PATH_INVALID,
                        severity=Severity.ERROR,
                        message=f"Unsafe generated destination: {exc}",
                        path=art.relative_path,
                    )
                )
                continue
            if key in seen:
                diagnostics.append(
                    Diagnostic(
                        code=Codes.GEN_DUPLICATE,
                        severity=Severity.ERROR,
                        message=f"Duplicate destination planned: {key}",
                        path=key,
                        details={"origins": [seen[key], art.origin]},
                    )
                )
            else:
                seen[key] = art.origin

        if any(d.severity is Severity.ERROR for d in diagnostics):
            artifacts = []

        return ArtifactPlan(
            project_root=str(project_root.resolve()),
            manifest_hash=manifest_hash(project),
            builder_version=__version__,
            profile=project.target.profile,
            artifacts=artifacts,
            diagnostics=diagnostics,
        )
