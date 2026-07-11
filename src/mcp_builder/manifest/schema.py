"""Runtime JSON Schema export for the public manifest contract."""

from __future__ import annotations

from typing import Any

from mcp_builder.manifest.models import ManifestModel


def export_manifest_schema() -> dict[str, Any]:
    """Export JSON Schema derived from Pydantic models (by alias).

    The committed public schema under ``contracts/manifest.schema.json`` is the
    human-facing alpha contract. This export is used for compatibility checks
    and documentation generation; it may include additional ``$defs`` metadata.
    """
    schema = ManifestModel.model_json_schema(by_alias=True, mode="serialization")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://mcpbuilder.dev/schemas/manifest/v1alpha1.json"
    schema["title"] = "MCP Builder Toolkit Project Manifest"
    return schema


def public_contract_keys() -> set[str]:
    """Top-level keys required by the public alpha contract."""
    return {"apiVersion", "kind", "metadata", "spec"}
