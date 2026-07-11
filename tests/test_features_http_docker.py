"""Phase 6: HTTP, Docker, Compose generation and validation."""

from __future__ import annotations

from pathlib import Path

from mcp_builder.cli.commands.generate import run_generate
from mcp_builder.cli.exit_codes import ExitCode
from mcp_builder.domain.diagnostics import Severity
from mcp_builder.manifest.loader import load_manifest_text
from mcp_builder.manifest.normalize import normalize
from mcp_builder.service import build_planner

HTTP_DOCKER = """\
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


def test_http_docker_compose_plan(tmp_path: Path) -> None:
    loaded = load_manifest_text(HTTP_DOCKER)
    assert loaded.manifest is not None
    project, diags = normalize(loaded.manifest)
    assert project is not None
    assert not diags
    plan = build_planner().plan(project, tmp_path)
    paths = {a.relative_path for a in plan.artifacts}
    assert "Dockerfile" in paths
    assert ".dockerignore" in paths
    assert "compose.yaml" in paths
    assert "src/http_demo/server.py" in paths
    server = next(a for a in plan.artifacts if a.relative_path.endswith("server.py"))
    assert 'transport="http"' in server.content or "transport=" in server.content
    assert 'os.getenv("MCP_HOST", "127.0.0.1")' in server.content
    dockerfile = next(a for a in plan.artifacts if a.relative_path == "Dockerfile")
    assert 'ENV MCP_HOST="0.0.0.0"' in dockerfile.content


def test_compose_requires_http() -> None:
    text = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: compose-stdio
  version: 0.1.0
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.15"
    packageName: compose_stdio
  transport:
    type: stdio
  features:
    tests: true
    lint: true
    typing: true
    docker: true
    compose: true
"""
    loaded = load_manifest_text(text)
    assert loaded.manifest is not None
    project, _diags = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, Path("/tmp"))
    assert any(
        d.severity is Severity.ERROR and "compose" in d.message.lower() for d in plan.diagnostics
    )


def test_generate_http_tree(tmp_path: Path) -> None:
    project = tmp_path / "http-proj"
    project.mkdir()
    (project / "mcp-builder.yaml").write_text(HTTP_DOCKER, encoding="utf-8")
    result, code = run_generate(
        file=project / "mcp-builder.yaml",
        output=project,
        dry_run=False,
        force_managed=set(),
    )
    assert code is ExitCode.SUCCESS, result.diagnostics
    assert (project / "Dockerfile").is_file()
    assert (project / "compose.yaml").is_file()
    assert "127.0.0.1" in (project / "compose.yaml").read_text(encoding="utf-8")
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "Streamable HTTP" in readme or "streamable" in readme.lower() or "8000" in readme

    expected_paths = {
        line.strip()
        for line in (Path(__file__).parent / "golden" / "http-docker.paths.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    actual = {
        p.relative_to(project).as_posix()
        for p in project.rglob("*")
        if p.is_file() and ".mcp-builder" not in p.parts and p.name != "mcp-builder.yaml"
    }
    assert expected_paths.issubset(actual), sorted(expected_paths - actual)


def test_broad_bind_warning() -> None:
    text = HTTP_DOCKER.replace("127.0.0.1", "0.0.0.0")
    loaded = load_manifest_text(text)
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, Path("/tmp"))
    assert any("binds broadly" in d.message for d in plan.diagnostics)


def test_structured_logging_generates_json_formatter(tmp_path: Path) -> None:
    loaded = load_manifest_text(HTTP_DOCKER)
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, tmp_path)
    server = next(a for a in plan.artifacts if a.relative_path.endswith("server.py"))
    assert "class JsonFormatter" in server.content
    assert "json.dumps(payload" in server.content


def test_structured_logging_can_be_disabled(tmp_path: Path) -> None:
    loaded = load_manifest_text(
        HTTP_DOCKER.replace("structuredLogging: true", "structuredLogging: false")
    )
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, tmp_path)
    server = next(a for a in plan.artifacts if a.relative_path.endswith("server.py"))
    assert "class JsonFormatter" not in server.content


def test_docker_stdio_validation_warning(tmp_path: Path) -> None:
    text = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: docker-stdio
  version: 0.1.0
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.15"
    packageName: docker_stdio
  transport:
    type: stdio
  features:
    tests: false
    lint: false
    typing: false
    docker: true
    compose: false
"""
    loaded = load_manifest_text(text)
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, tmp_path)
    assert any(d.code == "MBT-MANIFEST-004" for d in plan.diagnostics), [
        d.message for d in plan.diagnostics
    ]


def test_docker_stdio_dockerfile_has_no_expose(tmp_path: Path) -> None:
    text = """\
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: docker-stdio-2
  version: 0.1.0
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.15"
    packageName: docker_stdio_2
  transport:
    type: stdio
  features:
    tests: false
    lint: false
    typing: false
    docker: true
    compose: false
"""
    loaded = load_manifest_text(text)
    assert loaded.manifest is not None
    project, _ = normalize(loaded.manifest)
    assert project is not None
    plan = build_planner().plan(project, tmp_path)
    dockerfile = next(a for a in plan.artifacts if a.relative_path == "Dockerfile")
    assert "# stdio: no EXPOSE" in dockerfile.content
    assert "ENV MCP_HOST=" not in dockerfile.content
    assert '.venv/bin:$PATH"' in dockerfile.content
