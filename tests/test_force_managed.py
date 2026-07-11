"""Managed conflict resolution with --force-managed."""

from __future__ import annotations

from pathlib import Path

from mcp_builder.cli.commands.generate import run_generate
from mcp_builder.cli.commands.init import run_init
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.domain.diagnostics import CommandStatus


def test_force_managed_overwrites_conflict(tmp_path: Path) -> None:
    project = tmp_path / "force-demo"
    project.mkdir()
    run_init(
        directory=project,
        name="force-demo",
        transport="stdio",
        profile="fastmcp-python-2026.07",
        no_interactive=True,
        force_empty=True,
    )
    _, code = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=False,
        force_managed=set(),
    )
    assert code is ExitCode.SUCCESS

    readme = project / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\nUSER\n", encoding="utf-8")

    _conflict, ccode = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=False,
        force_managed=set(),
    )
    assert ccode is ExitCode.GENERATION_CONFLICT
    assert "USER" in readme.read_text(encoding="utf-8")

    forced, fcode = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=False,
        force_managed={"README.md"},
    )
    assert fcode is ExitCode.SUCCESS, forced.diagnostics
    assert forced.status is CommandStatus.OK
    assert "USER" not in readme.read_text(encoding="utf-8")
