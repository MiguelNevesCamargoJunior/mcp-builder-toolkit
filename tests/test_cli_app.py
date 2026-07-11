"""CLI entry-point tests for main() and error handler coverage."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from mcp_builder.cli.app import _STATE, app, main

runner = CliRunner()


def test_main_typer_exit_is_re_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fail_app() -> None:
        calls.append("called")
        raise typer.Exit(code=42)

    monkeypatch.setattr("mcp_builder.cli.app.app", fail_app)
    with pytest.raises(typer.Exit) as exc_info:
        main()
    assert exc_info.value.exit_code == 42
    assert calls == ["called"]


def test_main_internal_error_prints_to_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_app() -> None:
        raise ValueError("boom")

    monkeypatch.setattr("mcp_builder.cli.app.app", fail_app)
    _STATE["verbose"] = False
    stderr = io.StringIO()
    monkeypatch.setattr("sys.stderr", stderr)

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    assert "unexpected internal error" in stderr.getvalue()
    assert "boom" in stderr.getvalue()


def test_main_verbose_re_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_app() -> None:
        raise ValueError("boom")

    monkeypatch.setattr("mcp_builder.cli.app.app", fail_app)
    _STATE["verbose"] = True

    with pytest.raises(ValueError, match="boom"):
        main()


def test_main_callback_state_flags(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--verbose", "--quiet", "--no-color", "--version"])
    assert result.exit_code == 0


def test_version_output() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "mcp-builder" in result.stdout


def test_internal_error_code_in_stdout(tmp_path: Path) -> None:
    result = runner.invoke(app, ["generate", "-f", str(tmp_path / "nonexistent.yaml")])
    assert result.exit_code == 2
