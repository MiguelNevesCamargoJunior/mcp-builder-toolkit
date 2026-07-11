"""Export the manifest JSON Schema from the Pydantic model and validate
that the committed public schema is up to date.

Usage:
    uv run python scripts/export_manifest_schema.py         # print schema
    uv run python scripts/export_manifest_schema.py --check  # check committed
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs/001-core-builder/contracts/manifest.schema.json"


def export() -> dict:
    from mcp_builder.manifest.schema import export_manifest_schema
    return export_manifest_schema()


def main() -> None:
    schema = export()
    text = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"

    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        committed = SCHEMA_PATH.read_text(encoding="utf-8")
        if text != committed:
            print("error: manifest.schema.json is out of date with ManifestModel")
            print("Run: uv run python scripts/export_manifest_schema.py > specs/.../contracts/manifest.schema.json")
            sys.exit(1)
        print("ok: schema is up to date")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
