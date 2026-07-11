"""T025: golden-tree tests for minimal stdio generation output."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_builder.cli.commands.generate import run_generate
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.domain.diagnostics import CommandStatus

GOLDEN_ROOT = Path(__file__).parent / "golden"
STDIO_MANIFEST = GOLDEN_ROOT / "stdio-minimal.manifest.yaml"
STDIO_TREE = GOLDEN_ROOT / "stdio-minimal"

# Paths/segments never part of the generation golden snapshot.
_IGNORE_PARTS = {
    ".mcp-builder",
    ".ruff_cache",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
}


def _should_skip(rel: str) -> bool:
    parts = rel.split("/")
    if any(part in _IGNORE_PARTS for part in parts):
        return True
    return any(part.endswith(".pyc") or part.endswith(".pyo") for part in parts)


def _file_map(root: Path) -> dict[str, str]:
    """Relative posix path -> text content for all files under root."""
    mapping: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if _should_skip(rel):
            continue
        mapping[rel] = path.read_text(encoding="utf-8")
    return mapping


@pytest.mark.golden
def test_golden_stdio_minimal_tree(tmp_path: Path) -> None:
    """Generated stdio tree must match the committed golden snapshot."""
    assert STDIO_MANIFEST.is_file(), f"missing {STDIO_MANIFEST}"
    assert STDIO_TREE.is_dir(), f"missing {STDIO_TREE}"

    project = tmp_path / "project"
    project.mkdir()
    manifest_path = project / "mcp-builder.yaml"
    manifest_path.write_text(STDIO_MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")

    result, code = run_generate(
        file=manifest_path,
        output=project,
        dry_run=False,
        force_managed=set(),
    )
    assert code is ExitCode.SUCCESS, result.diagnostics
    assert result.status is CommandStatus.OK

    expected = _file_map(STDIO_TREE)
    actual = _file_map(project)
    # Drop the input manifest from actual comparison
    actual.pop("mcp-builder.yaml", None)

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    assert not missing, f"missing generated files: {missing}"
    assert not extra, f"unexpected generated files: {extra}"

    mismatches: list[str] = []
    for rel in sorted(expected):
        if expected[rel] != actual[rel]:
            mismatches.append(rel)
    assert not mismatches, (
        "content mismatch for:\n"
        + "\n".join(f"  - {m}" for m in mismatches)
        + "\nUpdate tests/golden/stdio-minimal after intentional template changes."
    )
