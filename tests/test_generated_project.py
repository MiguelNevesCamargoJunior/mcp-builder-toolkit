"""T027: generated-project acceptance — install, lint, type-check, pytest.

Generates a stdio FastMCP project into a temporary directory, installs its
dependencies with uv, then runs the same quality gates a developer would run
after `mcp-builder generate`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mcp_builder.cli.commands.generate import run_generate
from mcp_builder.cli.commands.init import run_init
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.domain.diagnostics import CommandStatus

# Generation itself is fast; dependency install needs headroom for cold caches.
_UV_TIMEOUT_S = 300
_TOOL_TIMEOUT_S = 180


def _require_uv() -> str:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is required for generated-project acceptance tests")
    return uv


def _run(
    args: list[str],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    # Keep CI/local output readable and avoid interactive prompts.
    merged.setdefault("UV_NO_PROGRESS", "1")
    merged.setdefault("CI", "1")
    return subprocess.run(
        args,
        cwd=cwd,
        env=merged,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _assert_ok(result: subprocess.CompletedProcess[str], step: str) -> None:
    if result.returncode == 0:
        return
    detail = (
        f"{step} failed with exit {result.returncode}\n"
        f"cmd: {' '.join(result.args) if isinstance(result.args, list) else result.args}\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}"
    )
    pytest.fail(detail)


@pytest.mark.generated
def test_generated_stdio_project_install_lint_typecheck_pytest(tmp_path: Path) -> None:
    """Generate → uv sync → ruff → mypy → pytest for a minimal stdio project."""
    uv = _require_uv()
    project = tmp_path / "generated-stdio"
    project.mkdir()

    init = run_init(
        directory=project,
        name="generated-stdio",
        transport="stdio",
        profile="fastmcp-python-2026.07",
        no_interactive=True,
        force_empty=True,
    )
    assert init.status is CommandStatus.OK, init.diagnostics

    gen, code = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=False,
        force_managed=set(),
    )
    assert code is ExitCode.SUCCESS, gen.diagnostics
    assert (project / "src" / "generated_stdio" / "server.py").is_file()
    assert (project / "pyproject.toml").is_file()

    # Isolated venv under the generated project (do not pollute the builder env).
    sync = _run(
        [
            uv,
            "sync",
            "--all-extras",
            "--python",
            f"{sys.version_info.major}.{sys.version_info.minor}",
        ],
        cwd=project,
        timeout=_UV_TIMEOUT_S,
    )
    _assert_ok(sync, "uv sync")

    lint = _run(
        [uv, "run", "ruff", "check", "."],
        cwd=project,
        timeout=_TOOL_TIMEOUT_S,
    )
    _assert_ok(lint, "ruff check")

    typing = _run(
        [uv, "run", "mypy", "src"],
        cwd=project,
        timeout=_TOOL_TIMEOUT_S,
    )
    _assert_ok(typing, "mypy")

    tests = _run(
        [uv, "run", "pytest", "-q"],
        cwd=project,
        timeout=_TOOL_TIMEOUT_S,
    )
    _assert_ok(tests, "pytest")
