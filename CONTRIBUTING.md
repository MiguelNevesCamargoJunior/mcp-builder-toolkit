# Contributing

Thanks for helping improve MCP Builder Toolkit.

## Prerequisites

- Python 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/)

```bash
uv sync --all-extras
uv run ruff check src tests
uv run mypy src
uv run pytest
```

## Spec-driven workflow

Read before changing behavior:

1. `.specify/memory/constitution.md`
2. `specs/001-core-builder/spec.md`, `plan.md`, `tasks.md`
3. Public contracts under `specs/001-core-builder/contracts/`

Do **not** add runtime governance, budgets, audit, A2A, or multi-language targets to `001-core-builder` without an ADR exception.

## Project layout

| Path | Role |
|------|------|
| `src/mcp_builder/domain/` | Protocol-independent models |
| `src/mcp_builder/manifest/` | Load, validate, normalize manifests |
| `src/mcp_builder/generation/` | Planner, renderer, lock, state, apply |
| `src/mcp_builder/targets/` | Target adapters (FastMCP Python first) |
| `src/mcp_builder/features/` | Composable generators (Docker, CI, …) |
| `tests/golden/` | Committed generation snapshots |

## Adding a target adapter

1. Implement `TargetAdapter` in `src/mcp_builder/targets/<name>/`.
2. Keep FastMCP (or other SDK) imports **out** of `domain/` and `manifest/`.
3. Register the adapter in `service.build_planner()` (internal API in v0.1).
4. Add a compatibility profile in `targets/compatibility.py`.
5. Add unit + golden + generated-project tests.

See `docs/extending.md`.

## Adding a feature generator

1. Implement `FeatureGenerator` under `src/mcp_builder/features/<name>/`.
2. Use `supports()` / `validate()` / `plan()`.
3. Prefer `managed` ownership for operational files.
4. Register in `service.build_planner()`.
5. Update contracts/docs if the manifest gains fields.

## Regenerating golden trees

After intentional template changes:

```bash
# regenerate fixtures and review the diff carefully
uv run python scripts/update_golden.py
uv run pytest -m golden
```

## Pull requests

1. **Fork** the repository (external contributors) or create a **branch** (maintainers).
2. Open a PR against `main` with a clear title and description (see `.github/PULL_REQUEST_TEMPLATE.md`).
3. Ensure **all status checks pass** before requesting review:
   - `ruff check src tests`
   - `mypy src`
   - `pytest --cov=mcp_builder --cov-branch`
4. Keep PRs focused and vertical (working generate path preferred).
5. Update acceptance tests when generated output changes.
6. Never silently overwrite scaffold-once semantics.
7. Include constitution check notes if behavior is security- or ownership-sensitive.

The `main` branch is **protected**: direct pushes are blocked, all merges require a PR with at least one approval and passing CI.

## License

Contributions are accepted under the Apache-2.0 license of this repository.
