"""CLI contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from mcp_builder.cli.app import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "mcp-builder" in result.stdout
    assert "0.1.0" in result.stdout


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "validate" in result.stdout
    assert "generate" in result.stdout
    assert "doctor" in result.stdout


def test_init_validate_generate_stdio(tmp_path: Path) -> None:
    project = tmp_path / "my-server"
    project.mkdir()

    result = runner.invoke(
        app,
        [
            "init",
            str(project),
            "--name",
            "my-server",
            "--transport",
            "stdio",
            "--no-interactive",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (project / "mcp-builder.yaml").is_file()

    result = runner.invoke(app, ["validate", "-f", str(project / "mcp-builder.yaml")])
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        ["generate", "-f", str(project / "mcp-builder.yaml"), "--dry-run"],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        ["generate", "-f", str(project / "mcp-builder.yaml")],
    )
    assert result.exit_code == 0, result.output
    assert (project / "src" / "my_server" / "server.py").is_file()
    assert (project / "pyproject.toml").is_file()
    assert (project / "tests" / "test_example_tool.py").is_file()
    assert (project / ".github" / "workflows" / "ci.yml").is_file()
    assert (project / ".mcp-builder" / "state.json").is_file()


def test_validate_json_invalid(tmp_path: Path) -> None:
    bad = tmp_path / "mcp-builder.yaml"
    bad.write_text("apiVersion: wrong\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", "-f", str(bad), "--format", "json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["command"] == "validate"
    assert payload["summary"]["errors"] >= 1
    assert "diagnostics" in payload


def test_scaffold_once_preserved(tmp_path: Path) -> None:
    project = tmp_path / "preserve-demo"
    project.mkdir()
    runner.invoke(
        app,
        [
            "init",
            str(project),
            "--name",
            "preserve-demo",
            "--transport",
            "stdio",
            "--no-interactive",
        ],
    )
    runner.invoke(app, ["generate", "-f", str(project / "mcp-builder.yaml")])

    tool = project / "src" / "preserve_demo" / "tools" / "example.py"
    original = tool.read_text(encoding="utf-8")
    tool.write_text(original + "\n# user change\n", encoding="utf-8")

    result = runner.invoke(app, ["generate", "-f", str(project / "mcp-builder.yaml")])
    assert result.exit_code == 0, result.output
    assert "# user change" in tool.read_text(encoding="utf-8")


def test_init_refuses_overwrite(tmp_path: Path) -> None:
    project = tmp_path / "twice"
    project.mkdir()
    r1 = runner.invoke(
        app,
        ["init", str(project), "--name", "twice", "--no-interactive"],
    )
    assert r1.exit_code == 0
    r2 = runner.invoke(
        app,
        ["init", str(project), "--name", "twice", "--no-interactive"],
    )
    assert r2.exit_code == 2


def test_deterministic_generation(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    for d in (a, b):
        d.mkdir()
        runner.invoke(
            app,
            ["init", str(d), "--name", "same-proj", "--no-interactive"],
        )
        runner.invoke(app, ["generate", "-f", str(d / "mcp-builder.yaml")])

    files_a = sorted(
        p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file() and p.name != "state.json"
    )
    files_b = sorted(
        p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file() and p.name != "state.json"
    )
    assert files_a == files_b
    for rel in files_a:
        if rel == "mcp-builder.yaml":
            continue
        assert (a / rel).read_text(encoding="utf-8") == (b / rel).read_text(encoding="utf-8")


def test_init_json_http_and_invalid_inputs(tmp_path: Path) -> None:
    http = tmp_path / "http"
    result = runner.invoke(
        app,
        [
            "init",
            str(http),
            "--name",
            "http-demo",
            "--transport",
            "streamable-http",
            "--no-interactive",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "ok"
    assert "streamable-http" in (http / "mcp-builder.yaml").read_text(encoding="utf-8")

    bad_transport = runner.invoke(
        app,
        ["init", str(tmp_path / "bad-transport"), "--transport", "sse", "--no-interactive"],
    )
    bad_name = runner.invoke(
        app,
        ["init", str(tmp_path / "bad-name"), "--name", "Bad Name", "--no-interactive"],
    )
    assert bad_transport.exit_code == 2
    assert "Unsupported transport" in bad_transport.output
    assert bad_name.exit_code == 2
    assert "cannot derive package name" in bad_name.output


def test_generate_json_and_invalid_manifest(tmp_path: Path) -> None:
    missing = runner.invoke(
        app,
        ["generate", "-f", str(tmp_path / "missing.yaml"), "--format", "json"],
    )
    assert missing.exit_code == 2
    assert json.loads(missing.stdout)["status"] == "error"

    project = tmp_path / "json-generate"
    project.mkdir()
    init = runner.invoke(
        app,
        ["init", str(project), "--name", "json-generate", "--no-interactive"],
    )
    assert init.exit_code == 0
    generated = runner.invoke(
        app,
        ["generate", "-f", str(project / "mcp-builder.yaml"), "--format", "json"],
    )
    assert generated.exit_code == 0
    assert json.loads(generated.stdout)["changes"]


def test_global_flags_and_interactive_name(tmp_path: Path) -> None:
    project = tmp_path / "interactive"
    result = runner.invoke(app, ["--quiet", "--no-color", "init", str(project)], input="chosen\n")
    assert result.exit_code == 0
    assert "name: chosen" in (project / "mcp-builder.yaml").read_text(encoding="utf-8")
