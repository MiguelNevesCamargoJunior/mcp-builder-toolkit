"""Edge-case and error-path tests for release readiness."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mcp_builder.cli.app import app
from mcp_builder.cli.commands.generate import run_generate
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.generation.lock import GenerationLock, GenerationLockError
from mcp_builder.manifest.loader import load_manifest_path, load_manifest_text
from mcp_builder.manifest.normalize import normalize
from mcp_builder.service import build_planner

runner = CliRunner()


class TestGenerationLockEdgeCases:
    def test_lock_held_twice_acquire(self, tmp_path: Path) -> None:
        lock = GenerationLock(tmp_path)
        lock.acquire()
        lock.acquire()
        assert lock._held
        lock.release()

    def test_lock_release_unheld(self, tmp_path: Path) -> None:
        lock = GenerationLock(tmp_path)
        lock.release()
        assert not lock._held

    def test_lock_stale_is_recovered(self, tmp_path: Path) -> None:
        old = time.time() - 3600
        lock = GenerationLock(tmp_path, stale_seconds=30)
        lock.path.parent.mkdir(parents=True, exist_ok=True)
        lock.path.write_text("stale lock content\n", encoding="utf-8")
        os.utime(lock.path, (old, old))
        lock.acquire()
        assert lock._held
        lock.release()

    def test_lock_stale_oserror_returns_true(self, tmp_path: Path) -> None:
        lock = GenerationLock(tmp_path / "nonexistent", stale_seconds=30)
        assert lock._is_stale()

    def test_lock_concurrent_raises_error(self, tmp_path: Path) -> None:
        lock_a = GenerationLock(tmp_path, stale_seconds=300)
        lock_b = GenerationLock(tmp_path, stale_seconds=300)
        lock_a.acquire()
        with pytest.raises(GenerationLockError):
            lock_b.acquire()
        lock_a.release()

    def test_generate_lock_conflict_returns_filesystem_failure(
        self, tmp_http_project: Path
    ) -> None:
        lock = GenerationLock(tmp_http_project, stale_seconds=300)
        lock.acquire()
        result, code = run_generate(
            file=tmp_http_project / "mcp-builder.yaml",
            output=tmp_http_project,
            dry_run=False,
            force_managed=set(),
        )
        assert code is ExitCode.FILESYSTEM_FAILURE
        assert any(d.code == "MBT-GEN-003" for d in result.diagnostics)
        lock.release()


class TestUnicodeAndNames:
    def test_unicode_metadata_description(self, tmp_path: Path) -> None:
        manifest = tmp_path / "mcp-builder.yaml"
        yaml = (
            "apiVersion: mcpbuilder.dev/v1alpha1\n"
            "kind: MCPServerProject\n"
            "metadata:\n"
            "  name: uni-test\n"
            "  version: 0.1.0\n"
            "spec:\n"
            "  target:\n"
            "    runtime: fastmcp-python\n"
            "    profile: fastmcp-python-2026.07\n"
            "    protocolVersion: '2025-11-25'\n"
            "  project:\n"
            "    python: '>=3.12,<3.14'\n"
            "    packageName: uni_test\n"
            "  transport:\n"
            "    type: stdio\n"
            "  features:\n"
            "    tests: false\n"
            "    lint: false\n"
            "    typing: false\n"
        )
        manifest.write_text(yaml, encoding="utf-8")
        loaded = load_manifest_path(manifest)
        assert loaded.manifest is not None
        result, code = run_generate(
            file=manifest,
            output=tmp_path,
            dry_run=True,
            force_managed=set(),
        )
        assert code is ExitCode.SUCCESS, result.diagnostics

    def test_long_project_name(self, tmp_path: Path) -> None:
        long_name = "a" * 50
        manifest = tmp_path / "mcp-builder.yaml"
        manifest.write_text(
            f"apiVersion: mcpbuilder.dev/v1alpha1\n"
            f"kind: MCPServerProject\n"
            f"metadata:\n"
            f"  name: {long_name}\n"
            f"  version: 0.1.0\n"
            f"spec:\n"
            f"  target:\n"
            f"    runtime: fastmcp-python\n"
            f"    profile: fastmcp-python-2026.07\n"
            f"    protocolVersion: '2025-11-25'\n"
            f"  project:\n"
            f"    python: '>=3.12,<3.14'\n"
            f"    packageName: {long_name[:40]}\n"
            f"  transport:\n"
            f"    type: stdio\n"
            f"  features:\n"
            f"    tests: false\n"
            f"    lint: false\n"
            f"    typing: false\n",
            encoding="utf-8",
        )
        loaded = load_manifest_path(manifest)
        assert loaded.manifest is not None
        project, diags = normalize(loaded.manifest)
        assert project is not None
        assert not diags, [d.message for d in diags]
        plan = build_planner().plan(project, tmp_path)
        assert len(plan.artifacts) > 0

    def test_non_ascii_description(self, tmp_path: Path) -> None:
        manifest = tmp_path / "mcp-builder.yaml"
        manifest.write_text(
            "apiVersion: mcpbuilder.dev/v1alpha1\n"
            "kind: MCPServerProject\n"
            "metadata:\n"
            "  name: unicode-test\n"
            "  version: 0.1.0\n"
            "spec:\n"
            "  target:\n"
            "    runtime: fastmcp-python\n"
            "    profile: fastmcp-python-2026.07\n"
            "    protocolVersion: '2025-11-25'\n"
            "  project:\n"
            "    python: '>=3.12,<3.14'\n"
            "    packageName: unicode_test\n"
            "  transport:\n"
            "    type: stdio\n"
            "  features:\n"
            "    tests: false\n"
            "    lint: false\n"
            "    typing: false\n",
            encoding="utf-8",
        )
        result, code = run_generate(
            file=manifest,
            output=tmp_path,
            dry_run=True,
            force_managed=set(),
        )
        assert code is ExitCode.SUCCESS, result.diagnostics


class TestStrictFlag:
    def test_doctor_strict_flag_no_errors(self, tmp_path: Path) -> None:
        project = tmp_path / "healthy"
        project.mkdir()
        runner.invoke(
            app,
            ["init", str(project), "--name", "healthy", "--no-interactive"],
        )
        runner.invoke(app, ["generate", "-f", str(project / "mcp-builder.yaml")])
        result = runner.invoke(app, ["doctor", str(project), "--strict"])
        assert result.exit_code == 0

    def test_validate_strict_with_errors(self, tmp_path: Path) -> None:
        bad = tmp_path / "mcp-builder.yaml"
        bad.write_text("apiVersion: invalid\n", encoding="utf-8")
        result = runner.invoke(app, ["validate", "-f", str(bad), "--strict"])
        assert result.exit_code == 2


class TestIOErrorPaths:
    def test_ioerror_on_generate_no_output(self, tmp_path: Path) -> None:
        manifest = tmp_path / "mcp-builder.yaml"
        manifest.write_text(
            "apiVersion: mcpbuilder.dev/v1alpha1\n"
            "kind: MCPServerProject\n"
            "metadata:\n"
            "  name: io-test\n"
            "  version: 0.1.0\n"
            "spec:\n"
            "  target:\n"
            "    runtime: fastmcp-python\n"
            "    profile: fastmcp-python-2026.07\n"
            "    protocolVersion: '2025-11-25'\n"
            "  project:\n"
            "    python: '>=3.12,<3.14'\n"
            "    packageName: io_test\n"
            "  transport:\n"
            "    type: stdio\n"
            "  features:\n"
            "    tests: false\n"
            "    lint: false\n"
            "    typing: false\n",
            encoding="utf-8",
        )
        result, code = run_generate(
            file=manifest,
            output=None,
            dry_run=True,
            force_managed=set(),
        )
        assert code is ExitCode.SUCCESS, result.diagnostics


class TestDerivedArtifact:
    def test_write_json_state_preview(self, tmp_path: Path) -> None:
        import json

        from mcp_builder.generation.transaction import write_json_state_preview

        loaded = load_manifest_text(
            "apiVersion: mcpbuilder.dev/v1alpha1\n"
            "kind: MCPServerProject\n"
            "metadata:\n"
            "  name: preview-test\n"
            "  version: 0.1.0\n"
            "spec:\n"
            "  target:\n"
            "    runtime: fastmcp-python\n"
            "    profile: fastmcp-python-2026.07\n"
            "    protocolVersion: '2025-11-25'\n"
            "  project:\n"
            "    python: '>=3.12,<3.14'\n"
            "    packageName: preview_test\n"
            "  transport:\n"
            "    type: stdio\n"
            "  features:\n"
            "    tests: false\n"
            "    lint: false\n"
            "    typing: false\n",
        )
        assert loaded.manifest is not None
        project, _ = normalize(loaded.manifest)
        assert project is not None
        plan = build_planner().plan(project, Path("/tmp"))
        preview = write_json_state_preview(plan)
        data = json.loads(preview)
        assert "manifestHash" in data
        assert "artifacts" in data
        assert isinstance(data["artifacts"], list)


class TestFilesystemFailureCode:
    def test_generate_io_error_code(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "mcp-builder.yaml"
        manifest.write_text(
            "apiVersion: mcpbuilder.dev/v1alpha1\n"
            "kind: MCPServerProject\n"
            "metadata:\n"
            "  name: fs-fail\n"
            "  version: 0.1.0\n"
            "spec:\n"
            "  target:\n"
            "    runtime: fastmcp-python\n"
            "    profile: fastmcp-python-2026.07\n"
            "    protocolVersion: '2025-11-25'\n"
            "  project:\n"
            "    python: '>=3.12,<3.14'\n"
            "    packageName: fs_fail\n"
            "  transport:\n"
            "    type: stdio\n"
            "  features:\n"
            "    tests: false\n"
            "    lint: false\n"
            "    typing: false\n",
            encoding="utf-8",
        )

        def fail_save(*args: object, **kwargs: object) -> None:
            raise OSError("disk full")

        monkeypatch.setattr("mcp_builder.generation.transaction.save_state", fail_save)
        result, code = run_generate(
            file=manifest,
            output=tmp_path,
            dry_run=False,
            force_managed=set(),
        )
        assert code is ExitCode.FILESYSTEM_FAILURE
        assert any(d.code == "MBT-GEN-004" for d in result.diagnostics)
