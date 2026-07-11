"""Phase 7: doctor fixtures and JSON envelope."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from typer.testing import CliRunner

from mcp_builder.cli.app import app
from mcp_builder.cli.commands.doctor import run_doctor
from mcp_builder.cli.commands.generate import run_generate
from mcp_builder.cli.commands.init import run_init
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.domain.diagnostics import CommandStatus, Severity
from mcp_builder.generation.state import state_path

ROOT = Path(__file__).resolve().parents[1]
DIAG_SCHEMA = json.loads(
    (ROOT / "specs/001-core-builder/contracts/diagnostics.schema.json").read_text(encoding="utf-8")
)
runner = CliRunner()


def _healthy_project(tmp_path: Path) -> Path:
    project = tmp_path / "healthy"
    project.mkdir()
    run_init(
        directory=project,
        name="healthy",
        transport="stdio",
        profile="fastmcp-python-2026.07",
        no_interactive=True,
        force_empty=True,
    )
    result, code = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=False,
        force_managed=set(),
    )
    assert code is ExitCode.SUCCESS, result.diagnostics
    return project


def test_doctor_healthy(tmp_path: Path) -> None:
    project = _healthy_project(tmp_path)
    result = run_doctor(directory=project, file=None)
    assert result.status in {CommandStatus.OK, CommandStatus.WARNING}
    assert result.summary.errors == 0


def test_doctor_missing_manifest(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = run_doctor(directory=empty, file=None)
    assert result.status is CommandStatus.ERROR
    assert any(d.code == "MBT-MANIFEST-001" for d in result.diagnostics)


def test_doctor_drifted_managed(tmp_path: Path) -> None:
    project = _healthy_project(tmp_path)
    readme = project / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    result = run_doctor(directory=project, file=None)
    assert any(d.code == "MBT-DOCTOR-002" for d in result.diagnostics)


def test_doctor_corrupt_state(tmp_path: Path) -> None:
    project = _healthy_project(tmp_path)
    state_path(project).write_text("{not-json", encoding="utf-8")
    result = run_doctor(directory=project, file=None)
    assert result.status is CommandStatus.ERROR
    assert any(d.code == "MBT-DOCTOR-003" for d in result.diagnostics)


def test_doctor_json_matches_schema(tmp_path: Path) -> None:
    project = _healthy_project(tmp_path)
    cli = runner.invoke(app, ["doctor", str(project), "--format", "json"])
    assert cli.exit_code == 0, cli.output
    payload = json.loads(cli.stdout)
    jsonschema.validate(instance=payload, schema=DIAG_SCHEMA)


def test_doctor_missing_expected_file(tmp_path: Path) -> None:
    project = _healthy_project(tmp_path)
    (project / "pyproject.toml").unlink()
    result = run_doctor(directory=project, file=None)
    assert any(
        d.code == "MBT-DOCTOR-001" and d.severity in {Severity.WARNING, Severity.ERROR}
        for d in result.diagnostics
    )


def test_doctor_file_option_uses_manifest_directory(tmp_path: Path) -> None:
    project = _healthy_project(tmp_path)
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()

    result = run_doctor(directory=unrelated, file=project / "mcp-builder.yaml")

    assert result.summary.errors == 0
    assert not any(d.code == "MBT-DOCTOR-001" for d in result.diagnostics)
    state_diagnostic = next(d for d in result.diagnostics if d.code == "MBT-GEN-021")
    assert state_diagnostic.path == str(project / ".mcp-builder" / "state.json")


def test_doctor_reports_symlinked_state_directory(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (project / ".mcp-builder").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not supported on this platform")

    result = run_doctor(directory=project, file=None)

    assert any(d.code == "MBT-PATH-002" for d in result.diagnostics)


def test_doctor_docker_check_docker_not_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "mcp_builder.cli.commands.doctor.shutil.which",
        lambda cmd: "/usr/bin/docker" if cmd == "docker" else None,
    )
    project = tmp_path / "dock-proj"
    project.mkdir()
    run_init(
        directory=project,
        name="dock-proj",
        transport="streamable-http",
        profile="fastmcp-python-2026.07",
        no_interactive=True,
        force_empty=True,
    )
    manifest_path = project / "mcp-builder.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")
    manifest = manifest.replace("docker: false", "docker: true")
    manifest = manifest.replace("compose: false", "compose: true")
    manifest_path.write_text(manifest, encoding="utf-8")

    result, code = run_generate(
        file=manifest_path,
        output=project,
        dry_run=False,
        force_managed=set(),
    )
    assert code is ExitCode.SUCCESS

    monkeypatch.setattr(
        "mcp_builder.cli.commands.doctor.shutil.which",
        lambda cmd: None if cmd == "docker" else "/usr/bin/uv",
    )
    result = run_doctor(directory=project, file=None)
    assert any(d.code == "MBT-DOCTOR-011" for d in result.diagnostics)
    assert any(d.code == "MBT-DOCTOR-010" for d in result.diagnostics) is False


def test_doctor_hints_attached_for_known_codes(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = run_doctor(directory=empty, file=None)
    hinted_codes = {"MBT-MANIFEST-001", "MBT-DOCTOR-010"}
    for d in result.diagnostics:
        if d.code in hinted_codes:
            assert d.hint is not None, f"Missing hint for {d.code}"
