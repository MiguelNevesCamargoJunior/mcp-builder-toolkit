"""T042: end-to-end quickstart path from quickstart.md."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mcp_builder.cli.commands.generate import run_generate
from mcp_builder.cli.commands.init import run_init
from mcp_builder.cli.commands.validate import run_validate
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.domain.diagnostics import CommandStatus


@pytest.mark.generated
def test_quickstart_init_validate_generate_test(tmp_path: Path) -> None:
    """Mirrors quickstart.md steps 2-5 (stdio) without interactive prompts."""
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv required")

    project = tmp_path / "customer-ops-mcp"
    project.mkdir()

    init = run_init(
        directory=project,
        name="customer-ops-mcp",
        transport="stdio",
        profile="fastmcp-python-2026.07",
        no_interactive=True,
        force_empty=True,
    )
    assert init.status is CommandStatus.OK
    assert (project / "mcp-builder.yaml").is_file()

    val = run_validate(file=project / "mcp-builder.yaml")
    assert val.status is CommandStatus.OK

    dry, dry_code = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=True,
        force_managed=set(),
    )
    assert dry_code is ExitCode.SUCCESS
    assert dry.changes

    gen, code = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=False,
        force_managed=set(),
    )
    assert code is ExitCode.SUCCESS, gen.diagnostics
    assert (project / "src" / "customer_ops_mcp" / "server.py").is_file()

    env = os.environ.copy()
    env["UV_NO_PROGRESS"] = "1"
    py = f"{sys.version_info.major}.{sys.version_info.minor}"
    sync = subprocess.run(
        [uv, "sync", "--all-extras", "--python", py],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert sync.returncode == 0, sync.stderr

    for cmd in (
        [uv, "run", "ruff", "check", "."],
        [uv, "run", "mypy", "src"],
        [uv, "run", "pytest", "-q"],
    ):
        result = subprocess.run(
            cmd,
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode == 0, f"{cmd} failed:\n{result.stdout}\n{result.stderr}"
