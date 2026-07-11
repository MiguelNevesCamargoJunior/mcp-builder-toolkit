"""T043: example invalid manifests with expected diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_builder.domain.diagnostics import Severity
from mcp_builder.manifest.loader import load_manifest_text
from mcp_builder.manifest.normalize import normalize

FIXTURES = Path(__file__).parent / "fixtures" / "invalid"
EXPECTED = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("filename", sorted(EXPECTED.keys()))
def test_invalid_manifest_fixture(filename: str) -> None:
    text = (FIXTURES / filename).read_text(encoding="utf-8")
    loaded = load_manifest_text(text)
    diagnostics = list(loaded.diagnostics)
    if loaded.manifest is not None:
        _, norm = normalize(loaded.manifest)
        diagnostics.extend(norm)

    errors = [d for d in diagnostics if d.severity is Severity.ERROR]
    spec = EXPECTED[filename]
    assert len(errors) >= spec["minErrors"], diagnostics
    codes = {d.code for d in errors}
    assert codes.intersection(spec["codesAny"]), f"got {codes}, expected any of {spec['codesAny']}"
