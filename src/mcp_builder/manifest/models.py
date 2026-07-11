"""Pydantic models matching contracts/manifest.schema.json."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NAME_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
PACKAGE_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]*$"
SEMVER_PATTERN = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
PROFILE_PATTERN = r"^[a-z0-9][a-z0-9.-]+$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class MetadataModel(StrictModel):
    name: Annotated[str, Field(pattern=NAME_PATTERN)]
    display_name: Annotated[
        str | None, Field(alias="displayName", default=None, min_length=1, max_length=100)
    ] = None
    description: Annotated[str | None, Field(default=None, max_length=500)] = None
    version: Annotated[str, Field(pattern=SEMVER_PATTERN)]
    license: Annotated[str | None, Field(default=None, min_length=1, max_length=100)] = None


class TargetModel(StrictModel):
    runtime: Literal["fastmcp-python"]
    profile: Annotated[str, Field(pattern=PROFILE_PATTERN)]
    protocol_version: Annotated[
        Literal["2025-11-25"],
        Field(alias="protocolVersion"),
    ]


class ProjectModel(StrictModel):
    python: Annotated[str, Field(min_length=1)]
    package_name: Annotated[str, Field(alias="packageName", pattern=PACKAGE_PATTERN)]
    layout: Literal["src"] = "src"
    dependency_manager: Annotated[
        Literal["uv"],
        Field(alias="dependencyManager", default="uv"),
    ] = "uv"


class StdioTransportModel(StrictModel):
    type: Literal["stdio"]


class StreamableHttpTransportModel(StrictModel):
    type: Literal["streamable-http"]
    host: str = "127.0.0.1"
    port: Annotated[int, Field(ge=1, le=65535)] = 8000
    path: str = "/mcp"

    @field_validator("path")
    @classmethod
    def validate_http_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("HTTP path must start with '/'")
        parts = [p for p in value.split("/") if p]
        if any(p in {".", ".."} for p in parts):
            raise ValueError("HTTP path must not contain path traversal segments")
        return value


TransportModel = Annotated[
    StdioTransportModel | StreamableHttpTransportModel,
    Field(discriminator="type"),
]


class FeaturesModel(StrictModel):
    tests: bool
    lint: bool
    typing: bool
    docker: bool = False
    compose: bool = False
    github_actions: Annotated[bool, Field(alias="githubActions")] = True
    structured_logging: Annotated[bool, Field(alias="structuredLogging")] = True

    @model_validator(mode="after")
    def compose_requires_docker(self) -> FeaturesModel:
        if self.compose and not self.docker:
            raise ValueError("features.compose requires features.docker to be true")
        return self


class ScaffoldsModel(StrictModel):
    example_tool: Annotated[bool, Field(alias="exampleTool")] = True


class SpecModel(StrictModel):
    target: TargetModel
    project: ProjectModel
    transport: TransportModel
    features: FeaturesModel
    scaffolds: ScaffoldsModel = Field(default_factory=ScaffoldsModel)


class ManifestModel(StrictModel):
    api_version: Annotated[Literal["mcpbuilder.dev/v1alpha1"], Field(alias="apiVersion")]
    kind: Literal["MCPServerProject"]
    metadata: MetadataModel
    spec: SpecModel
