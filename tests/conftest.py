"""Shared fixtures for MCP Builder Toolkit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

EXAMPLE_STDIO = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: demo-mcp
  version: 0.1.0
  license: Apache-2.0
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.15"
    packageName: demo_mcp
    layout: src
    dependencyManager: uv
  transport:
    type: stdio
  features:
    tests: true
    lint: true
    typing: true
    docker: false
    compose: false
    githubActions: true
    structuredLogging: true
  scaffolds:
    exampleTool: true
"""

EXAMPLE_HTTP = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: http-demo
  version: 0.1.0
  license: Apache-2.0
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.15"
    packageName: http_demo
  transport:
    type: streamable-http
    host: 127.0.0.1
    port: 8000
    path: /mcp
  features:
    tests: true
    lint: true
    typing: true
    docker: true
    compose: true
    githubActions: true
    structuredLogging: true
  scaffolds:
    exampleTool: true
"""


@pytest.fixture
def stdio_manifest_text() -> str:
    return EXAMPLE_STDIO


@pytest.fixture
def http_manifest_text() -> str:
    return EXAMPLE_HTTP


@pytest.fixture
def tmp_project(tmp_path: Path, stdio_manifest_text: str) -> Path:
    path = tmp_path / "mcp-builder.yaml"
    path.write_text(stdio_manifest_text, encoding="utf-8")
    return tmp_path


@pytest.fixture
def tmp_http_project(tmp_path: Path, http_manifest_text: str) -> Path:
    path = tmp_path / "mcp-builder.yaml"
    path.write_text(http_manifest_text, encoding="utf-8")
    return tmp_path
