"""Protocol-independent project domain model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TransportType = Literal["stdio", "streamable-http"]
RuntimeId = Literal["fastmcp-python"]
LayoutId = Literal["src"]
DependencyManagerId = Literal["uv"]


@dataclass(frozen=True, slots=True)
class ProjectMetadata:
    name: str
    version: str
    display_name: str | None = None
    description: str | None = None
    license: str | None = None


@dataclass(frozen=True, slots=True)
class TargetSpec:
    runtime: RuntimeId
    profile: str
    protocol_version: str


@dataclass(frozen=True, slots=True)
class StdioTransport:
    type: Literal["stdio"] = "stdio"


@dataclass(frozen=True, slots=True)
class StreamableHttpTransport:
    type: Literal["streamable-http"] = "streamable-http"
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp"


TransportSpec = StdioTransport | StreamableHttpTransport


@dataclass(frozen=True, slots=True)
class PythonProjectSpec:
    python: str
    package_name: str
    layout: LayoutId = "src"
    dependency_manager: DependencyManagerId = "uv"


@dataclass(frozen=True, slots=True)
class FeatureSelection:
    tests: bool
    lint: bool
    typing: bool
    docker: bool = False
    compose: bool = False
    github_actions: bool = True
    structured_logging: bool = True


@dataclass(frozen=True, slots=True)
class ScaffoldSelection:
    example_tool: bool = True


@dataclass(frozen=True, slots=True)
class ProjectSpec:
    """Normalized, immutable generation input."""

    api_version: str
    kind: Literal["MCPServerProject"]
    metadata: ProjectMetadata
    target: TargetSpec
    project: PythonProjectSpec
    transport: TransportSpec
    features: FeatureSelection
    scaffolds: ScaffoldSelection
