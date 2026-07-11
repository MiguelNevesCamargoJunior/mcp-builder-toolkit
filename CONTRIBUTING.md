# Contributing to MCP Builder Toolkit

Thanks for helping improve MCP Builder Toolkit. This guide covers how to
contribute effectively, whether you are fixing a bug, adding a feature, or
improving documentation.

## Table of Contents

- [Quick start](#quick-start)
- [Ways to contribute](#ways-to-contribute)
- [Development setup](#development-setup)
- [Code quality](#code-quality)
- [Testing](#testing)
- [Pull request workflow](#pull-request-workflow)
- [Spec-driven changes](#spec-driven-changes)
- [Architecture overview](#architecture-overview)

---

## Quick start

```bash
# Fork and clone the repository, then:
uv sync --all-extras
uv run ruff check src tests
uv run mypy src
uv run pytest
```

---

## Ways to contribute

| Type | Where | Best for |
|------|-------|----------|
| 🐛 Bug report | [Issues](https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/issues) | Reporting unexpected behavior |
| 💡 Feature idea | [Discussions](https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/discussions) | Proposing new capabilities |
| 📖 Documentation | PR against `docs/` or `README.md` | Fixing typos, clarifying guides |
| 🧪 Test addition | PR against `tests/` | Improving coverage |
| 🚀 Code change | PR against `src/` | Bug fixes, features, refactors |
| 🐧 Pilot feedback | PR to `docs/pilot-evidence.md` | Running the quickstart and reporting results |

---

## Development setup

### Prerequisites

- **Python** 3.12 or 3.13
- **[uv](https://docs.astral.sh/uv/)** — package manager and tool runner

### Install

```bash
git clone https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit.git
cd mcp-builder-toolkit
uv sync --all-extras
```

### First build and test

```bash
uv run mcp-builder --version
uv run pytest -m "not generated and not mcp_smoke" -q
```

### Optional: pre-commit hooks

```bash
uv sync --all-extras
uv run pre-commit install
uv run pre-commit run --all-files
```

Pre-commit is **optional**. CI is the real enforcement. You can skip hooks
at any time with `git commit --no-verify`.

### Using the local build for development

```bash
# Create a test project
mkdir -p ~/tmp/my-server && cd ~/tmp/my-server
uv run --project /path/to/mcp-builder-toolkit mcp-builder init --name my-server --no-interactive
uv run --project /path/to/mcp-builder-toolkit mcp-builder generate
```

---

## Code quality

All four gates must pass before a PR is merged:

```bash
# 1. Formatting
uv run ruff format --check src tests

# 2. Linting
uv run ruff check src tests

# 3. Type checking
uv run mypy src

# 4. Tests with coverage
uv run pytest --cov=mcp_builder --cov-branch --cov-report=term-missing -q
```

To auto-fix fixable issues:

```bash
uv run ruff format src tests
uv run ruff check src tests --fix
```

---

## Testing

### Test categories

| Marker | What it tests | Requires network? |
|--------|--------------|-------------------|
| `golden` | Byte-for-byte output comparison | No |
| `generated` | Full generated project (install + lint + type + test) | Yes — `uv sync` |
| `mcp_smoke` | Real MCP client calls against generated server | Yes — FastMCP |
| _(none)_ | Unit, CLI, manifest, generation, security | No |

### Run fast tests only (no network)

```bash
uv run pytest -m "not generated and not mcp_smoke" -q
```

### Run all tests

```bash
uv run pytest -q
```

### Update golden trees after template changes

```bash
uv run python scripts/update_golden.py
uv run pytest -m golden -q
```

---

## Change classification

| Change type | Requirements |
|-------------|-------------|
| Documentation | CI basics |
| Bug fix | Regression test |
| Generated output change | Golden trees + acceptance test |
| Contract/public API change | Spec update + ADR + migration note + schema diff |
| New profile/target | ADR + compatibility suite |
| New feature generator | Tests + golden tree + acceptance |
| Runtime dependency | Security review + written justification |
| Release | Changelog + release notes + artifact smoke |

PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat(cli): add interactive profile selection
fix(generator): reject junction-based path escape
docs: clarify Streamable HTTP exposure
test(security): cover tampered state paths
chore(deps): update development dependencies
```

## Pull request workflow

### For external contributors (fork)

1. **Fork** the repository on GitHub.
2. **Clone** your fork: `git clone https://github.com/YOUR-USERNAME/mcp-builder-toolkit.git`
3. **Create a branch**: `git checkout -b my-change`
4. **Make your changes** and commit.
5. **Run all quality gates** (see [Code quality](#code-quality)).
6. **Push** to your fork: `git push origin my-change`
7. **Open a PR** against `MiguelNevesCamargoJunior/mcp-builder-toolkit/main`.
   - Use the PR template (automatically included).
   - Reference the issue if applicable.

### For maintainers (direct branch)

1. **Create a branch** on the main repo: `git checkout -b fix/my-fix`
2. **Make your changes** and commit.
3. **Push**: `git push origin fix/my-fix`
4. **Open a PR** against `main`.

### PR checklist

Before requesting review:

- [ ] `ruff format --check src tests` passes
- [ ] `ruff check src tests` passes
- [ ] `mypy src` passes
- [ ] `pytest --cov=mcp_builder --cov-branch` passes
- [ ] If generated output changed: golden trees updated (`scripts/update_golden.py`)
- [ ] If contracts changed: specs and docs updated
- [ ] PR description explains the change and motivation

### After merge

The `main` branch is **protected**:
- Direct pushes are **blocked**.
- All merges require a PR with **1 approval** and **passing CI**.
- Use **Squash and merge** or **Rebase and merge** (avoid merge commits).

---

## Spec-driven changes

Before changing behavior, read:

1. **Constitution** — `.specify/memory/constitution.md`
   - Project principles and hard boundaries.
2. **Feature spec** — `specs/001-core-builder/spec.md`
   - What v0.1 includes and explicitly excludes.
3. **Plan & tasks** — `specs/001-core-builder/plan.md`, `tasks.md`
   - Current iteration scope and completion criteria.
4. **Public contracts** — `specs/001-core-builder/contracts/`
   - Manifest schema, CLI contract, diagnostics schema.

### Hard boundaries (v0.1 alpha)

Do **not** add to feature `001-core-builder` without an ADR exception:

- Runtime governance (auth, budgets, audit)
- Agent-to-agent (A2A) protocols
- Multi-language code generation
- Hosted control plane
- On-chain or ledger-based features

### Architecture decision records

Significant design decisions are documented in `docs/adr/`. If your change
introduces a new architectural pattern or reverses a previous decision, add an
ADR.

---

## Architecture overview

```
mcp-builder.yaml              # User-authored manifest
       │
       ▼
┌─ manifest/ ───────────────┐
│  loader.py    — parse YAML │
│  schema.py    — JSON Schema│
│  models.py    — pydantic   │
│  normalize.py — ProjectSpec│
└────────────────────────────┘
       │
       ▼
┌─ generation/ ─────────────┐
│  planner.py   — plan files │
│  renderer.py  — templates  │
│  lock.py      — mutex      │
│  transaction  — apply/     │
│  .py            rollback   │
│  state.py     — .mcp-      │
│                  builder/  │
└────────────────────────────┘
       │
       ▼
   Generated project (no runtime dependency on the builder)
```

### Key directories

| Path | Role |
|------|------|
| `src/mcp_builder/domain/` | Protocol-independent models (ProjectSpec, diagnostics, artifacts) |
| `src/mcp_builder/manifest/` | Parse, validate, and normalize YAML manifests |
| `src/mcp_builder/generation/` | Plan, render, lock, state, and atomic apply |
| `src/mcp_builder/targets/` | Target adapters (FastMCP Python first) |
| `src/mcp_builder/features/` | Composable generators (Docker, Compose, CI) |
| `src/mcp_builder/cli/` | Typer CLI commands |
| `tests/golden/` | Committed generation snapshots |
| `specs/001-core-builder/contracts/` | Public schemas and contracts |

### Extending

- [Adding a target adapter](docs/extending.md) — new runtimes or SDKs
- [Adding a feature generator](docs/extending.md) — new capabilities
- [Architecture overview](docs/architecture.md) — detailed design

---

## License

Contributions are accepted under the [Apache 2.0 license](LICENSE) of this
repository. By contributing, you agree that your contributions will be licensed
under the same license.
