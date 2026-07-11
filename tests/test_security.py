"""T062: malicious manifest / path / symlink security tests."""

from __future__ import annotations

import ast
import json
import tomllib
from pathlib import Path

import pytest
import yaml

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
    with pytest.raises(ValueError):
        normalize_relative_path("safe/../secrets")
    with pytest.raises(ValueError):
        normalize_relative_path("C:\\secrets")
    with pytest.raises(ValueError):
        normalize_relative_path("CON.txt")


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


def test_tampered_state_cannot_remove_outside_file(
    tmp_path: Path, stdio_manifest_text: str
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("keep", encoding="utf-8")
    (project / "mcp-builder.yaml").write_text(stdio_manifest_text, encoding="utf-8")
    state_dir = project / ".mcp-builder"
    state_dir.mkdir()
    state = {
        "stateVersion": "1",
        "builderVersion": "0.1.0a1",
        "profile": "fastmcp-python-2026.07",
        "protocolVersion": "2025-11-25",
        "manifestHash": "sha256:tampered",
        "artifacts": {
            "../../outside.txt": {
                "ownership": "managed",
                "generatedHash": "sha256:tampered",
                "origin": "tampered",
            }
        },
    }
    (state_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    result, code = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=False,
        force_managed=set(),
    )

    assert code is ExitCode.FILESYSTEM_FAILURE
    assert outside.read_text(encoding="utf-8") == "keep"
    assert any("corrupt or unsafe" in diagnostic.message for diagnostic in result.diagnostics)


@pytest.mark.parametrize("symlink_parent", ["src", ".github", ".mcp-builder"])
def test_generate_rejects_symlinked_managed_parent(
    tmp_path: Path, stdio_manifest_text: str, symlink_parent: str
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / "mcp-builder.yaml").write_text(stdio_manifest_text, encoding="utf-8")
    link = project / symlink_parent
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not supported on this platform")

    result, code = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=False,
        force_managed=set(),
    )

    assert code is ExitCode.USAGE_OR_VALIDATION or code is ExitCode.FILESYSTEM_FAILURE
    assert not any(outside.iterdir())
    assert any("symbolic link" in diagnostic.message for diagnostic in result.diagnostics)


def test_manifest_values_are_contextually_serialized(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    payload = 'Break"); __import__("os").system("echo injected"); #'
    manifest = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: quoted-mcp
  displayName: placeholder
  description: |-
    Handles: #tags, ${VALUES}, Unicode ç, quotes ' " and backslashes \\.
    Second line stays data.
  version: 0.1.0
  license: 'Apache-2.0 OR "MIT"'
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.15"
    packageName: quoted_mcp
  transport:
    type: streamable-http
    host: localhost
    port: 8000
    path: /api/mcp
  features:
    tests: true
    lint: true
    typing: true
    docker: true
    compose: true
    githubActions: false
    structuredLogging: true
"""
    manifest = manifest.replace(
        "  displayName: placeholder", f"  displayName: {json.dumps(payload)}"
    )
    manifest_path = project / "mcp-builder.yaml"
    manifest_path.write_text(manifest, encoding="utf-8")

    result, code = run_generate(
        file=manifest_path,
        output=project,
        dry_run=False,
        force_managed=set(),
    )

    assert code is ExitCode.SUCCESS, result.diagnostics
    server = (project / "src/quoted_mcp/server.py").read_text(encoding="utf-8")
    tool = (project / "src/quoted_mcp/tools/example.py").read_text(encoding="utf-8")
    server_tree = ast.parse(server)
    tool_tree = ast.parse(tool)
    assert any(
        isinstance(node, ast.Constant) and node.value == payload for node in ast.walk(server_tree)
    )
    assert any(
        isinstance(node, ast.Constant) and node.value == payload for node in ast.walk(tool_tree)
    )
    assert not any(
        isinstance(node, ast.Name) and node.id == "__import__" for node in ast.walk(server_tree)
    )
    pyproject = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["description"].startswith("Handles: #tags")
    compose = yaml.safe_load((project / "compose.yaml").read_text(encoding="utf-8"))
    assert compose["services"]["mcp"]["ports"] == ["localhost:8000:8000"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("host", "bad.host\nservices: {}"),
        ("path", "/mcp?redirect=bad"),
    ],
)
def test_http_transport_rejects_context_breaking_values(field: str, value: str) -> None:
    text = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: unsafe-http
  version: 0.1.0
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.15"
    packageName: unsafe_http
  transport:
    type: streamable-http
    host: 127.0.0.1
    port: 8000
    path: /mcp
  features:
    tests: true
    lint: true
    typing: true
"""
    text = text.replace(
        f"    {field}: " + ("127.0.0.1" if field == "host" else "/mcp"),
        f"    {field}: {json.dumps(value)}",
    )
    loaded = load_manifest_text(text)
    assert not loaded.ok
