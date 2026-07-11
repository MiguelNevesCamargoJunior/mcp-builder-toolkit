"""Application service wiring for CLI commands."""

from __future__ import annotations

from mcp_builder.features.compose import ComposeFeature
from mcp_builder.features.docker import DockerFeature
from mcp_builder.features.github_actions import GitHubActionsFeature
from mcp_builder.generation.planner import GenerationPlanner
from mcp_builder.targets.fastmcp_python import FastMCPPythonAdapter

DEFAULT_MANIFEST = "mcp-builder.yaml"


def build_planner() -> GenerationPlanner:
    return GenerationPlanner(
        adapter=FastMCPPythonAdapter(),
        features=[
            DockerFeature(),
            ComposeFeature(),
            GitHubActionsFeature(),
        ],
    )
