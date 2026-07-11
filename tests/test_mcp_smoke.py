"""T028: MCP client smoke against a generated stdio server.

Uses FastMCP's supported Client for:
1. In-process transport against the generated server module.
2. Stdio transport spawning ``python -m <package>.server``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from mcp_builder.cli.commands.generate import run_generate
from mcp_builder.cli.commands.init import run_init
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.domain.diagnostics import CommandStatus
from mcp_builder.manifest.normalize import name_to_package

_UV_TIMEOUT_S = 300
_SMOKE_TIMEOUT_S = 120

PROJECT_NAME = "mcp-smoke"


def _require_uv() -> str:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is required for MCP smoke tests")
    return uv


def _run(
    args: list[str],
    *,
    cwd: Path,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("UV_NO_PROGRESS", "1")
    env.setdefault("CI", "1")
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _assert_ok(result: subprocess.CompletedProcess[str], step: str) -> None:
    if result.returncode == 0:
        return
    pytest.fail(
        f"{step} failed with exit {result.returncode}\n"
        f"cmd: {result.args}\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}"
    )


def _prepare_generated_project(tmp_path: Path) -> tuple[Path, str]:
    project = tmp_path / "mcp-smoke"
    project.mkdir()
    init = run_init(
        directory=project,
        name=PROJECT_NAME,
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
    package = name_to_package(PROJECT_NAME)
    return project, package


def _in_process_script(package: str) -> str:
    return textwrap.dedent(
        f"""\
        import asyncio
        from {package}.server import mcp
        from fastmcp import Client

        async def main() -> None:
            async with Client(mcp) as client:
                tools = await client.list_tools()
                names = {{t.name for t in tools}}
                assert "echo" in names, names
                assert "health" in names, names
                echo = await client.call_tool("echo", {{"message": "from-client"}})
                assert echo.is_error is False
                assert echo.data == "from-client"
                health = await client.call_tool("health", {{}})
                assert health.is_error is False
                payload = health.data if isinstance(health.data, dict) else health.structured_content
                assert payload is not None
                assert payload.get("status") == "ok"
                print("IN_PROCESS_SMOKE_OK")

        asyncio.run(main())
        """
    )


def _stdio_script(package: str) -> str:
    return textwrap.dedent(
        f"""\
        import asyncio
        import sys
        from pathlib import Path
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport

        async def main() -> None:
            transport = StdioTransport(
                command=sys.executable,
                args=["-m", "{package}.server"],
                cwd=str(Path.cwd()),
            )
            async with Client(transport) as client:
                tools = await client.list_tools()
                names = {{t.name for t in tools}}
                assert "echo" in names, names
                result = await client.call_tool("echo", {{"message": "stdio-ok"}})
                assert result.is_error is False
                assert result.data == "stdio-ok"
                print("STDIO_SMOKE_OK")

        asyncio.run(main())
        """
    )


@pytest.mark.generated
@pytest.mark.mcp_smoke
def test_generated_server_mcp_client_in_process_and_stdio(tmp_path: Path) -> None:
    """Initialize, list tools, and call example tool via FastMCP Client."""
    uv = _require_uv()
    project, package = _prepare_generated_project(tmp_path)

    py = f"{sys.version_info.major}.{sys.version_info.minor}"
    sync = _run(
        [uv, "sync", "--all-extras", "--python", py],
        cwd=project,
        timeout=_UV_TIMEOUT_S,
    )
    _assert_ok(sync, "uv sync")

    in_process = _run(
        [uv, "run", "python", "-c", _in_process_script(package)],
        cwd=project,
        timeout=_SMOKE_TIMEOUT_S,
    )
    _assert_ok(in_process, "in-process MCP client smoke")
    assert "IN_PROCESS_SMOKE_OK" in in_process.stdout

    stdio = _run(
        [uv, "run", "python", "-c", _stdio_script(package)],
        cwd=project,
        timeout=_SMOKE_TIMEOUT_S,
    )
    _assert_ok(stdio, "stdio MCP client smoke")
    assert "STDIO_SMOKE_OK" in stdio.stdout
