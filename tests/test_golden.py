"""T025: golden-tree tests for generation output."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_builder.cli.commands.generate import run_generate
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.domain.diagnostics import CommandStatus

GOLDEN_ROOT = Path(__file__).parent / "golden"

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


def _assert_golden_tree(tmp_path: Path, manifest_rel: str, tree_rel: str) -> None:
    manifest_path = GOLDEN_ROOT / manifest_rel
    tree_path = GOLDEN_ROOT / tree_rel
    assert manifest_path.is_file(), f"missing {manifest_path}"
    assert tree_path.is_dir(), f"missing {tree_path}"

    project = tmp_path / "project"
    project.mkdir()
    proj_manifest = project / "mcp-builder.yaml"
    proj_manifest.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")

    result, code = run_generate(
        file=proj_manifest,
        output=project,
        dry_run=False,
        force_managed=set(),
    )
    assert code is ExitCode.SUCCESS, result.diagnostics
    assert result.status is CommandStatus.OK

    expected = _file_map(tree_path)
    actual = _file_map(project)
    actual.pop("mcp-builder.yaml", None)

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    assert not missing, f"missing generated files ({tree_rel}): {missing}"
    assert not extra, f"unexpected generated files ({tree_rel}): {extra}"

    mismatches: list[str] = []
    for rel in sorted(expected):
        if expected[rel] != actual[rel]:
            mismatches.append(rel)
    assert not mismatches, (
        "content mismatch for:\n"
        + "\n".join(f"  - {m}" for m in mismatches)
        + f"\nUpdate {tree_rel} after intentional template changes."
    )


@pytest.mark.golden
def test_golden_stdio_minimal_tree(tmp_path: Path) -> None:
    _assert_golden_tree(tmp_path, "stdio-minimal.manifest.yaml", "stdio-minimal")


@pytest.mark.golden
def test_golden_http_docker_tree(tmp_path: Path) -> None:
    _assert_golden_tree(tmp_path, "http-docker.manifest.yaml", "http-docker")
