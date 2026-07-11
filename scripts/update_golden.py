#!/usr/bin/env python3
"""Regenerate tests/golden/stdio-minimal from the current templates."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcp_builder.cli.commands.generate import run_generate  # noqa: E402
from mcp_builder.cli.exit_codes import ExitCode  # noqa: E402

MANIFEST = ROOT / "tests/golden/stdio-minimal.manifest.yaml"
OUT = ROOT / "tests/golden/stdio-minimal"


def main() -> int:
    staging = ROOT / ".golden-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    shutil.copy(MANIFEST, staging / "mcp-builder.yaml")
    result, code = run_generate(
        file=staging / "mcp-builder.yaml",
        output=staging,
        dry_run=False,
        force_managed=set(),
    )
    if code is not ExitCode.SUCCESS:
        print(result.diagnostics, file=sys.stderr)
        return 1

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    ignore = {".mcp-builder", "mcp-builder.yaml"}
    for path in staging.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(staging)
        if rel.parts[0] in ignore:
            continue
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        print("wrote", dest.relative_to(ROOT))
    shutil.rmtree(staging)
    print("golden updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
