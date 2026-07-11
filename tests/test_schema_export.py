"""T012: runtime schema export vs public contract."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from jsonschema import Draft202012Validator

from mcp_builder.manifest.schema import export_manifest_schema, public_contract_keys

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SCHEMA = ROOT / "specs/001-core-builder/contracts/manifest.schema.json"
EXAMPLE = ROOT / "specs/001-core-builder/contracts/manifest.example.yaml"


def test_export_has_public_required_keys() -> None:
    exported = export_manifest_schema()
    assert public_contract_keys().issubset(set(exported.get("properties", {})))
    assert exported.get("$id", "").endswith("manifest/v1alpha1.json")


def test_public_schema_validates_example() -> None:
    import yaml

    schema = json.loads(PUBLIC_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)


def test_example_loads_via_runtime_models() -> None:
    from mcp_builder.manifest.loader import load_manifest_text
    from mcp_builder.manifest.normalize import normalize

    loaded = load_manifest_text(EXAMPLE.read_text(encoding="utf-8"))
    assert loaded.ok
    assert loaded.manifest is not None
    spec, diags = normalize(loaded.manifest)
    assert not diags
    assert spec is not None
