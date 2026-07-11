"""Manifest loading and normalization tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from mcp_builder.manifest.loader import (
    MAX_COLLECTION_ITEMS,
    MAX_MANIFEST_BYTES,
    MAX_NESTING_DEPTH,
    load_manifest_path,
    load_manifest_text,
)
from mcp_builder.manifest.normalize import manifest_hash, name_to_package, normalize


def test_load_valid_stdio(stdio_manifest_text: str) -> None:
    result = load_manifest_text(stdio_manifest_text)
    assert result.ok
    assert result.manifest is not None
    assert result.manifest.metadata.name == "demo-mcp"
    assert result.manifest.spec.transport.type == "stdio"


def test_normalize_valid(stdio_manifest_text: str) -> None:
    loaded = load_manifest_text(stdio_manifest_text)
    assert loaded.manifest is not None
    spec, diags = normalize(loaded.manifest)
    assert not diags
    assert spec is not None
    assert spec.project.package_name == "demo_mcp"
    assert spec.target.profile == "fastmcp-python-2026.07"


def test_manifest_hash_stable(stdio_manifest_text: str) -> None:
    loaded = load_manifest_text(stdio_manifest_text)
    assert loaded.manifest is not None
    spec, _ = normalize(loaded.manifest)
    assert spec is not None
    h1 = manifest_hash(spec)
    h2 = manifest_hash(spec)
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_unknown_profile_rejected() -> None:
    text = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: demo-mcp
  version: 0.1.0
spec:
  target:
    runtime: fastmcp-python
    profile: not-a-real-profile
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.14"
    packageName: demo_mcp
  transport:
    type: stdio
  features:
    tests: true
    lint: true
    typing: true
"""
    loaded = load_manifest_text(text)
    assert loaded.manifest is not None
    spec, diags = normalize(loaded.manifest)
    assert spec is None
    assert any(d.code == "MBT-COMPAT-001" for d in diags)


def test_compose_requires_docker() -> None:
    text = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: demo-mcp
  version: 0.1.0
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.14"
    packageName: demo_mcp
  transport:
    type: stdio
  features:
    tests: true
    lint: true
    typing: true
    docker: false
    compose: true
"""
    loaded = load_manifest_text(text)
    assert not loaded.ok
    assert loaded.manifest is None


def test_unsafe_yaml_tag_rejected() -> None:
    text = "!!python/object/apply:os.system ['echo pwned']\n"
    loaded = load_manifest_text(text)
    assert not loaded.ok
    assert any(d.code in {"MBT-MANIFEST-006", "MBT-MANIFEST-002"} for d in loaded.diagnostics)


def test_invalid_name_schema() -> None:
    text = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: INVALID_NAME
  version: 0.1.0
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.14"
    packageName: demo_mcp
  transport:
    type: stdio
  features:
    tests: true
    lint: true
    typing: true
"""
    loaded = load_manifest_text(text)
    assert not loaded.ok


def test_name_to_package() -> None:
    assert name_to_package("customer-ops-mcp") == "customer_ops_mcp"


def test_load_missing_file(tmp_path: Path) -> None:
    from mcp_builder.manifest.loader import load_manifest_path

    result = load_manifest_path(tmp_path / "missing.yaml")
    assert not result.ok
    assert any(d.code == "MBT-MANIFEST-001" for d in result.diagnostics)


def test_public_example_manifest() -> None:
    example = (
        Path(__file__).resolve().parents[1]
        / "specs/001-core-builder/contracts/manifest.example.yaml"
    )
    text = example.read_text(encoding="utf-8")
    loaded = load_manifest_text(text)
    assert loaded.ok, loaded.diagnostics
    assert loaded.manifest is not None
    spec, diags = normalize(loaded.manifest)
    assert not diags
    assert spec is not None
    assert spec.transport.type == "streamable-http"  # type: ignore[union-attr]


def test_manifest_path_must_be_regular_file(tmp_path: Path) -> None:
    result = load_manifest_path(tmp_path)
    assert not result.ok
    assert result.diagnostics[0].code == "MBT-MANIFEST-002"


def test_manifest_path_size_limit(tmp_path: Path) -> None:
    path = tmp_path / "large.yaml"
    path.write_text("x" * (MAX_MANIFEST_BYTES + 1), encoding="utf-8")
    result = load_manifest_path(path)
    assert not result.ok
    assert result.diagnostics[0].code == "MBT-MANIFEST-005"


def test_empty_scalar_and_malformed_yaml_are_rejected() -> None:
    empty = load_manifest_text("")
    scalar = load_manifest_text("hello\n")
    malformed = load_manifest_text("metadata: [broken\n")
    assert empty.diagnostics[0].message == "Manifest is empty"
    assert scalar.diagnostics[0].message == "Manifest root must be a mapping"
    assert malformed.diagnostics[0].code == "MBT-MANIFEST-002"
    assert malformed.diagnostics[0].line is not None
    assert malformed.diagnostics[0].column is not None


def test_manifest_nesting_and_collection_limits() -> None:
    nested: object = "leaf"
    for _ in range(MAX_NESTING_DEPTH + 1):
        nested = {"child": nested}
    too_deep = load_manifest_text(yaml.safe_dump(nested))
    too_many = load_manifest_text(yaml.safe_dump({"items": list(range(MAX_COLLECTION_ITEMS + 1))}))
    assert too_deep.diagnostics[0].code == "MBT-MANIFEST-006"
    assert too_many.diagnostics[0].code == "MBT-MANIFEST-006"


def test_schema_diagnostics_sanitize_complex_inputs() -> None:
    result = load_manifest_text("apiVersion: []\nkind: {}\n")
    assert not result.ok
    inputs = {
        diagnostic.details["input"] for diagnostic in result.diagnostics if diagnostic.details
    }
    assert "list" in inputs
    assert "dict" in inputs
