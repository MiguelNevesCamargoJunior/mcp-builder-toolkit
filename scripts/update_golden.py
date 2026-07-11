#!/usr/bin/env python3
"""Regenerate committed golden trees from the current templates."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcp_builder.cli.commands.generate import run_generate  # noqa: E402
from mcp_builder.cli.exit_codes import ExitCode  # noqa: E402

PROFILES = [
    ("stdio-minimal.manifest.yaml", "stdio-minimal"),
    ("http-docker.manifest.yaml", "http-docker"),
]


def update_profile(manifest_name: str, output_name: str) -> bool:
    manifest = ROOT / "tests/golden" / manifest_name
    output = ROOT / "tests/golden" / output_name
    staging = ROOT / f".golden-staging-{output_name}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    shutil.copy(manifest, staging / "mcp-builder.yaml")
    result, code = run_generate(
        file=staging / "mcp-builder.yaml",
        output=staging,
        dry_run=False,
        force_managed=set(),
    )
    if code is not ExitCode.SUCCESS:
        print(result.diagnostics, file=sys.stderr)
        return False

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    ignore = {".mcp-builder", "mcp-builder.yaml"}
    for path in staging.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(staging)
        if rel.parts[0] in ignore:
            continue
        dest = output / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        print("wrote", dest.relative_to(ROOT))
    shutil.rmtree(staging)
    print(f"golden updated: {output_name}")
    return True


def main() -> int:
    for manifest_name, output_name in PROFILES:
        if not update_profile(manifest_name, output_name):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
