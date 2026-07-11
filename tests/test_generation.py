"""Generation planner and transaction tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_builder.domain.artifacts import ArtifactPlan, ArtifactSpec
from mcp_builder.domain.diagnostics import Ownership
from mcp_builder.generation.renderer import content_hash
from mcp_builder.generation.transaction import apply_plan
from mcp_builder.manifest.loader import load_manifest_path
from mcp_builder.manifest.normalize import normalize
from mcp_builder.service import build_planner


def test_plan_includes_expected_paths(tmp_project: Path) -> None:
    loaded = load_manifest_path(tmp_project / "mcp-builder.yaml")
    assert loaded.manifest is not None
    project, diags = normalize(loaded.manifest)
    assert project is not None
    assert not diags

    plan = build_planner().plan(project, tmp_project)
    paths = {a.relative_path for a in plan.artifacts}
    assert "pyproject.toml" in paths
    assert "src/demo_mcp/server.py" in paths
    assert "src/demo_mcp/tools/example.py" in paths
    assert "tests/test_example_tool.py" in paths
    assert ".github/workflows/ci.yml" in paths
    assert not any(d.severity.value == "error" for d in plan.diagnostics)


def test_apply_writes_files(tmp_project: Path) -> None:
    loaded = load_manifest_path(tmp_project / "mcp-builder.yaml")
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, tmp_project)
    result = apply_plan(plan, tmp_project)
    assert result.applied
    assert (tmp_project / "src/demo_mcp/server.py").is_file()
    assert (tmp_project / ".mcp-builder/state.json").is_file()


def test_dry_run_no_writes(tmp_project: Path) -> None:
    loaded = load_manifest_path(tmp_project / "mcp-builder.yaml")
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, tmp_project)
    result = apply_plan(plan, tmp_project, dry_run=True)
    assert not result.applied
    assert not (tmp_project / "src").exists()
    assert any(c.action.value == "create" for c in result.changes)


def test_managed_conflict(tmp_project: Path) -> None:
    loaded = load_manifest_path(tmp_project / "mcp-builder.yaml")
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, tmp_project)
    apply_plan(plan, tmp_project)

    readme = tmp_project / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\n# user edit\n", encoding="utf-8")

    # Re-plan same content — still conflict because user modified managed file
    # and desired still differs from current
    result = apply_plan(plan, tmp_project)
    assert not result.applied
    assert any(c.action.value == "conflict" for c in result.changes)


def test_example_tool_disabled_omits_tool_test(tmp_project: Path) -> None:
    manifest = tmp_project / "mcp-builder.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("exampleTool: true", "exampleTool: false"),
        encoding="utf-8",
    )
    loaded = load_manifest_path(manifest)
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, tmp_project)
    paths = {artifact.relative_path for artifact in plan.artifacts}
    assert "src/demo_mcp/tools/example.py" not in paths
    assert "tests/test_example_tool.py" not in paths
    smoke = next(a for a in plan.artifacts if a.relative_path == "tests/test_server_smoke.py")
    assert "assert names == set()" in smoke.content


def test_state_write_failure_rolls_back_project_files(
    tmp_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loaded = load_manifest_path(tmp_project / "mcp-builder.yaml")
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, tmp_project)

    def fail_state_write(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated state failure")

    monkeypatch.setattr("mcp_builder.generation.transaction.save_state", fail_state_write)
    result = apply_plan(plan, tmp_project)

    assert not result.applied
    assert not (tmp_project / "src").exists()
    assert not (tmp_project / "README.md").exists()
    assert not (tmp_project / ".mcp-builder/state.json").exists()


def test_derived_artifact_create_update_and_unchanged(tmp_path: Path) -> None:
    def plan_for(content: str) -> ArtifactPlan:
        return ArtifactPlan(
            project_root=str(tmp_path),
            manifest_hash="sha256:manifest",
            builder_version="test",
            profile="test-profile",
            artifacts=[
                ArtifactSpec(
                    relative_path="generated/index.json",
                    content=content,
                    content_hash=content_hash(content),
                    ownership=Ownership.DERIVED,
                    origin="test/index",
                )
            ],
        )

    created = apply_plan(plan_for("one\n"), tmp_path)
    unchanged = apply_plan(plan_for("one\n"), tmp_path, dry_run=True)
    updated = apply_plan(plan_for("two\n"), tmp_path)
    assert created.changes[0].action.value == "create"
    assert unchanged.changes[0].action.value == "unchanged"
    assert updated.changes[0].action.value == "update"


def test_duplicate_path_error_in_plan(tmp_project: Path) -> None:

    loaded = load_manifest_path(tmp_project / "mcp-builder.yaml")
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None

    plan = build_planner().plan(project, tmp_project)
    diags = [d for d in plan.diagnostics if d.code == "MBT-GEN-002"]
    assert not diags, f"unexpected duplicates in minimal plan: {diags}"


def test_rollback_failure_logs_additional_detail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mcp_builder.domain.artifacts import ArtifactPlan, ArtifactSpec
    from mcp_builder.domain.diagnostics import Ownership
    from mcp_builder.generation.renderer import content_hash
    from mcp_builder.generation.transaction import apply_plan

    spec = ArtifactSpec(
        relative_path="test.txt",
        content="hello",
        content_hash=content_hash("hello"),
        ownership=Ownership.MANAGED,
        origin="test",
    )
    plan = ArtifactPlan(
        project_root=str(tmp_path),
        manifest_hash="sha256:test",
        builder_version="test",
        profile="test",
        artifacts=[spec],
    )

    def fail_save(*args: object, **kwargs: object) -> None:
        raise OSError("state write failed")

    def fail_restore(*args: object, **kwargs: object) -> OSError:
        return OSError("restore also failed")

    monkeypatch.setattr("mcp_builder.generation.transaction.save_state", fail_save)
    monkeypatch.setattr("mcp_builder.generation.transaction._restore_files", fail_restore)
    result = apply_plan(plan, tmp_path)
    assert not result.applied
    assert any("rollback also failed" in d.message for d in result.diagnostics)


def test_no_prior_state_user_modified(tmp_path: Path) -> None:
    from mcp_builder.domain.artifacts import ArtifactPlan, ArtifactSpec
    from mcp_builder.domain.diagnostics import Ownership
    from mcp_builder.generation.renderer import content_hash
    from mcp_builder.generation.transaction import apply_plan

    existing = tmp_path / "existing.txt"
    existing.write_text("user content\n", encoding="utf-8")

    spec = ArtifactSpec(
        relative_path="existing.txt",
        content="generated content\n",
        content_hash=content_hash("generated content\n"),
        ownership=Ownership.MANAGED,
        origin="test",
    )
    plan = ArtifactPlan(
        project_root=str(tmp_path),
        manifest_hash="sha256:test",
        builder_version="test",
        profile="test",
        artifacts=[spec],
    )
    result = apply_plan(plan, tmp_path)
    assert not result.applied
    assert any(c.action.value == "conflict" for c in result.changes)
    assert "generated content" not in existing.read_text(encoding="utf-8")


def test_removed_managed_file_is_deleted_but_modified_file_becomes_orphan(
    tmp_path: Path,
) -> None:
    def managed_plan(paths: dict[str, str]) -> ArtifactPlan:
        return ArtifactPlan(
            project_root=str(tmp_path),
            manifest_hash="sha256:manifest",
            builder_version="test",
            profile="test-profile",
            artifacts=[
                ArtifactSpec(
                    relative_path=path,
                    content=content,
                    content_hash=content_hash(content),
                    ownership=Ownership.MANAGED,
                    origin="test/managed",
                )
                for path, content in paths.items()
            ],
        )

    initial = managed_plan({"remove.txt": "remove\n", "orphan.txt": "original\n"})
    assert apply_plan(initial, tmp_path).applied
    (tmp_path / "orphan.txt").write_text("user edit\n", encoding="utf-8")

    result = apply_plan(managed_plan({}), tmp_path)
    actions = {change.path: change.action.value for change in result.changes}
    assert result.applied
    assert actions == {"remove.txt": "remove-managed", "orphan.txt": "orphan"}
    assert not (tmp_path / "remove.txt").exists()
    assert (tmp_path / "orphan.txt").read_text(encoding="utf-8") == "user edit\n"
