"""Pydantic models matching contracts/manifest.schema.json."""

from __future__ import annotations

import ipaddress
import re
from typing import Annotated, Literal

from packaging.version import InvalidVersion, Version
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NAME_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
PACKAGE_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]*$"
SEMVER_PATTERN = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
PROFILE_PATTERN = r"^[a-z0-9][a-z0-9.-]+$"
HOSTNAME_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*$"
)
HTTP_PATH_PATTERN = re.compile(r"^/[A-Za-z0-9._~!$&'()*+,;=:@%/-]*$")


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

    @field_validator("version")
    @classmethod
    def validate_python_version(cls, value: str) -> str:
        try:
            Version(value)
        except InvalidVersion as exc:
            raise ValueError("version must be valid PEP 440") from exc
        return value

    @field_validator("display_name", "license")
    @classmethod
    def reject_control_characters(cls, value: str | None) -> str | None:
        if value is not None and any(ord(character) < 32 for character in value):
            raise ValueError("value must not contain control characters")
        return value


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

    @field_validator("host")
    @classmethod
    def validate_http_host(cls, value: str) -> str:
        if value == "localhost":
            return value
        candidate = value.removeprefix("[").removesuffix("]")
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            if not HOSTNAME_PATTERN.fullmatch(value):
                raise ValueError("HTTP host must be an IP address or DNS hostname") from None
        return value

    @field_validator("path")
    @classmethod
    def validate_http_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("HTTP path must start with '/'")
        parts = [p for p in value.split("/") if p]
        if any(p in {".", ".."} for p in parts):
            raise ValueError("HTTP path must not contain path traversal segments")
        if not HTTP_PATH_PATTERN.fullmatch(value):
            raise ValueError("HTTP path contains unsupported URL characters")
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
