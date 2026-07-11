"""Local build state at .mcp-builder/state.json."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mcp_builder.domain.artifacts import ArtifactPlan
from mcp_builder.domain.diagnostics import Ownership
from mcp_builder.manifest.paths import normalize_relative_path, safe_project_path

STATE_DIR = ".mcp-builder"
STATE_FILE = "state.json"
STATE_VERSION = "1"


class ArtifactState(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    ownership: Ownership
    generated_hash: str = Field(alias="generatedHash")
    origin: str
    template_origin: str | None = Field(default=None, alias="templateOrigin")


class BuildState(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    state_version: str = Field(alias="stateVersion", default=STATE_VERSION)
    builder_version: str = Field(alias="builderVersion")
    profile: str
    protocol_version: str = Field(alias="protocolVersion")
    manifest_hash: str = Field(alias="manifestHash")
    artifacts: dict[str, ArtifactState] = Field(default_factory=dict)

    @field_validator("artifacts")
    @classmethod
    def validate_artifact_paths(cls, value: dict[str, ArtifactState]) -> dict[str, ArtifactState]:
        normalized: dict[str, ArtifactState] = {}
        for path, artifact in value.items():
            safe = normalize_relative_path(path)
            if safe != path.replace("\\", "/"):
                raise ValueError(f"artifact path is not canonical: {path!r}")
            normalized[safe] = artifact
        return normalized

    @classmethod
    def from_plan(cls, plan: ArtifactPlan) -> BuildState:
        arts = {
            a.relative_path.replace("\\", "/"): ArtifactState(
                ownership=a.ownership,
                generatedHash=a.content_hash,
                origin=a.origin,
                templateOrigin=a.origin,
            )
            for a in plan.artifacts
        }
        return cls(
            stateVersion=STATE_VERSION,
            builderVersion=plan.builder_version,
            profile=plan.profile,
            protocolVersion=plan.protocol_version,
            manifestHash=plan.manifest_hash,
            artifacts=arts,
        )


def state_path(project_root: Path) -> Path:
    return safe_project_path(project_root, f"{STATE_DIR}/{STATE_FILE}")


def load_state(project_root: Path) -> BuildState | None:
    """Load build state, or None if missing.

    Raises:
        ValueError / json.JSONDecodeError / ValidationError: corrupt state.
    """
    path = state_path(project_root)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return BuildState.model_validate(data)


def try_load_state(project_root: Path) -> tuple[BuildState | None, Exception | None]:
    """Load state without raising; returns (state, error)."""
    try:
        path = state_path(project_root)
        if not path.is_file():
            return None, None
        return load_state(project_root), None
    except Exception as exc:
        return None, exc


def save_state(project_root: Path, state: BuildState) -> None:
    path = state_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path = safe_project_path(project_root, f"{STATE_DIR}/{STATE_FILE}")
    payload = state.model_dump(by_alias=True, mode="json")
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=".state.", suffix=".tmp", dir=path.parent)
    tmp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def state_to_dict(state: BuildState) -> dict[str, Any]:
    return state.model_dump(by_alias=True, mode="json")
