"""GitHub Actions feature generator."""

from __future__ import annotations

from mcp_builder.domain.artifacts import ArtifactSpec
from mcp_builder.domain.diagnostics import Diagnostic, Ownership
from mcp_builder.domain.project import ProjectSpec
from mcp_builder.generation.renderer import content_hash

CI_YML = """\
name: CI

on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - name: Install uv
        uses: astral-sh/setup-uv@0c5e2b8115b80b4c7c5ddf6ffdd634974642d182 # v5.4.1
      - name: Set up Python
        run: uv python install ${{{{ matrix.python-version }}}}
      - name: Install dependencies
        run: uv sync --all-extras
{lint_step}\
{type_step}\
{test_step}\
"""


class GitHubActionsFeature:
    id = "github-actions"

    def supports(self, project: ProjectSpec) -> bool:
        return project.features.github_actions

    def validate(self, project: ProjectSpec) -> list[Diagnostic]:
        return []

    def plan(self, project: ProjectSpec) -> list[ArtifactSpec]:
        lint_step = ""
        type_step = ""
        test_step = ""
        if project.features.lint:
            lint_step = "      - name: Lint\n        run: uv run ruff check .\n"
        if project.features.typing:
            type_step = "      - name: Type check\n        run: uv run mypy src\n"
        if project.features.tests:
            test_step = "      - name: Test\n        run: uv run pytest\n"

        content = CI_YML.format(
            lint_step=lint_step,
            type_step=type_step,
            test_step=test_step,
        )
        return [
            ArtifactSpec(
                relative_path=".github/workflows/ci.yml",
                content=content,
                content_hash=content_hash(content),
                ownership=Ownership.MANAGED,
                origin="feature.github-actions/ci.yml",
            )
        ]
