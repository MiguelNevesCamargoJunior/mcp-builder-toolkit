# MCP Builder Toolkit

[![PyPI](https://img.shields.io/pypi/v/mcp-builder-toolkit)](https://pypi.org/project/mcp-builder-toolkit/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-builder-toolkit)](https://pypi.org/project/mcp-builder-toolkit/)
[![CI](https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/MiguelNevesCamargoJunior/mcp-builder-toolkit/branch/main/graph/badge.svg)](https://codecov.io/gh/MiguelNevesCamargoJunior/mcp-builder-toolkit)
[![License](https://img.shields.io/github/license/MiguelNevesCamargoJunior/mcp-builder-toolkit)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-yellow)]()

Manifest-driven CLI that generates readable, tested Python MCP server projects with safe regeneration and optional Docker/CI assets.

> MCP defines the protocol. MCP Builder Toolkit defines a repeatable way to create, inspect, test, and package an MCP server.

**Status:** v0.1.0a2 published; v0.1.0a3 in release hardening. Alpha software,
not production-ready.

## What the YAML controls

The manifest declares project-generation intent:

- FastMCP Python compatibility profile and MCP protocol version;
- stdio or Streamable HTTP transport;
- package name and supported Python range;
- tests, linting, typing, Docker, Compose, GitHub Actions, and structured logs;
- whether to include the replaceable example tool.

Tool behavior and API integrations remain normal, user-owned Python code. The
alpha does not generate arbitrary tools from YAML or convert OpenAPI documents.
See [YAML capabilities and boundaries](https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/blob/main/docs/yaml-capabilities.md) for the complete
boundary and an API integration example.

## Install

```bash
uv tool install mcp-builder-toolkit
mcp-builder --version
```

From a source checkout:

```bash
uv sync --all-extras
uv run mcp-builder --version
```

## Guided quickstart (recommended)

**Full walkthrough (generate → implement tools → test → call with a real MCP client):**

→ **[Guided quickstart](https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/blob/main/docs/guided-quickstart.md)**

### Short path

```bash
mkdir -p ~/dev/my-mcp && cd ~/dev/my-mcp
mcp-builder init --name my-mcp --transport stdio --no-interactive
mcp-builder validate
mcp-builder generate

uv sync --all-extras
uv run pytest
uv run python -m my_mcp.server
```

Streamable HTTP + Docker: see the guided quickstart (Step 12) or set `transport.type: streamable-http` and `features.docker/compose: true`, then `mcp-builder generate`.

For generated containers, the server binds to `0.0.0.0` inside the container
while Compose preserves the manifest's conservative host-side publication
(default `127.0.0.1`).

## Commands

| Command | Purpose |
|---------|---------|
| `mcp-builder init` | Create a minimal `mcp-builder.yaml` |
| `mcp-builder validate` | Schema + semantic + compatibility checks |
| `mcp-builder generate` | Plan and write project files (`--dry-run`, `--force-managed`) |
| `mcp-builder doctor` | Manifest, state, drift, and local tool checks |

## Architecture

```text
manifest.yaml
    → parse + validate + normalize
    → protocol-independent ProjectSpec
    → FastMCP adapter + Docker/Compose/CI features
    → ArtifactPlan (managed / scaffold-once / derived)
    → locked staged apply + .mcp-builder/state.json
```

Generated projects do **not** depend on this builder at runtime.

## Compatibility profile

| Field | Value |
|-------|-------|
| Profile | `fastmcp-python-2026.07` |
| FastMCP | `>=3.4.4,<3.5` |
| Python | `>=3.12,<3.15` |
| MCP protocol | `2025-11-25` |
| Manifest API | `mcpbuilder.dev/v1alpha1` (frozen for alpha) |

## Development

```bash
uv sync --all-extras
uv run ruff check src tests
uv run mypy src
uv run pytest
# optional: pre-commit install
```

Update golden trees after intentional template changes:

```bash
uv run python scripts/update_golden.py
```

## Documentation

| Doc | Content |
|-----|---------|
| `CHANGELOG.md` | Version history and alpha boundaries |
| `specs/001-core-builder/` | Feature spec, plan, tasks, contracts |
| `docs/guided-quickstart.md` | **Build a working MCP server step by step** |
| `docs/architecture.md` | System architecture |
| `docs/extending.md` | Target/feature extension guide |
| `docs/threat-model.md` | Threat model |
| `docs/yaml-capabilities.md` | YAML capabilities and API integration boundary |
| `docs/release-readiness-plan.md` | Alpha correction and verification plan |
| `docs/pilot-feedback.md` | Pilot form (SC-001/SC-002) |
| `docs/release-notes-0.1.0.md` | Release notes / publish checklist |
| `SECURITY.md` / `SUPPORT.md` / `CONTRIBUTING.md` | Project policies |

## Explicit v0.1 boundary

Not in this release: OAuth, policy engines, budgets, audit receipts, A2A, agent contracts, gateways, multi-language generation, hosted control plane.

## License

Apache-2.0
