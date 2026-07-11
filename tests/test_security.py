"""T062: malicious manifest / path / symlink security tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_builder.cli.commands.generate import run_generate
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.domain.diagnostics import Severity
from mcp_builder.manifest.loader import MAX_MANIFEST_BYTES, load_manifest_text
from mcp_builder.manifest.normalize import normalize
from mcp_builder.manifest.paths import normalize_relative_path
from mcp_builder.service import build_planner


def test_rejects_python_yaml_tag() -> None:
    text = "!!python/object/apply:os.system ['id']\n"
    loaded = load_manifest_text(text)
    assert not loaded.ok
    assert any(d.severity is Severity.ERROR for d in loaded.diagnostics)


def test_rejects_oversized_manifest() -> None:
    huge = "x: " + ("a" * (MAX_MANIFEST_BYTES + 10))
    loaded = load_manifest_text(huge)
    assert not loaded.ok
    assert any(d.code == "MBT-MANIFEST-005" for d in loaded.diagnostics)


def test_path_normalize_blocks_escape() -> None:
    with pytest.raises(ValueError):
        normalize_relative_path("../secrets")


def test_generate_does_not_follow_symlink_escape(tmp_path: Path) -> None:
    """Managed writes stay under project root (symlink target outside is not written via relative plan)."""
    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    # Place a symlink inside project pointing outside — apply should still only write planned relative paths
    link = project / "leak"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not supported on this platform")

    manifest = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: sec-demo
  version: 0.1.0
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.15"
    packageName: sec_demo
  transport:
    type: stdio
  features:
    tests: true
    lint: true
    typing: true
    githubActions: false
"""
    (project / "mcp-builder.yaml").write_text(manifest, encoding="utf-8")
    result, code = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=False,
        force_managed=set(),
    )
    assert code is ExitCode.SUCCESS, result.diagnostics
    # Outside file content unchanged
    assert outside.read_text(encoding="utf-8") == "secret"
    # No planned artifact should be absolute or escape
    loaded = load_manifest_text(manifest)
    assert loaded.manifest is not None
    project_spec, _ = normalize(loaded.manifest)
    assert project_spec is not None
    plan = build_planner().plan(project_spec, project)
    for art in plan.artifacts:
        assert ".." not in art.relative_path.split("/")
        assert not art.relative_path.startswith("/")


def test_planner_paths_are_relative(tmp_path: Path, stdio_manifest_text: str) -> None:
    loaded = load_manifest_text(stdio_manifest_text)
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, tmp_path)
    for art in plan.artifacts:
        normalize_relative_path(art.relative_path)
