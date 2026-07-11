# Agent Instructions

This file defines the rules and conventions that AI agents must follow when
working on MCP Builder Toolkit. It complements `CONTRIBUTING.md` (for human
contributors) with agent-specific constraints.

## Before any change

Read these first (in order):

1. `.specify/memory/constitution.md` — project principles and hard boundaries.
2. `specs/001-core-builder/spec.md` — feature scope for v0.1.
3. `specs/001-core-builder/plan.md` and `tasks.md` — current iteration.
4. `AGENTS.md` (this file) — agent rules.
5. `CONTRIBUTING.md` — human contributor workflow.

## Constitution rules

1. Treat contracts under `specs/001-core-builder/contracts/` as public alpha
   contracts — do not break them without a documented migration.
2. Do **not** add runtime governance, budgets, audit, A2A, agent contracts,
   gateways, or multi-language generation to feature `001-core-builder`.
   These require a new feature spec and an ADR.
3. Do **not** introduce a builder runtime dependency into generated projects.
   Generated projects must be installable and runnable without this package.
4. Preserve the distinction between `managed`, `scaffold-once`, and `derived`
   artifacts. Never silently change ownership semantics.
5. Verify current MCP protocol and FastMCP behavior from primary sources
   (fastmcp docs, MCP spec) before changing compatibility assumptions. Do
   not rely on pre-training knowledge for SDK specifics.
6. Add or update acceptance tests whenever generated output changes.
7. Never silently overwrite user-modified files. Respect scaffold-once
   semantics and report conflicts explicitly.
8. Prefer small vertical increments that keep generated reference projects
   executable after every PR.

When a proposed change conflicts with the constitution, write an ADR in
`docs/adr/` and stop implementation until the exception is explicitly
accepted by the maintainer.

## Branch and PR rules

9. The `main` branch is **protected**:
   - Direct pushes are **blocked** — always use a branch + PR.
   - PRs require **1 approval** and **passing CI**.
   - Use **Squash and merge** or **Rebase and merge** (avoid merge commits).
10. After pushing a branch, check that GitHub Actions reports the expected
    status checks before asking for review.

## Code quality gates

All four must pass before a PR can merge:

11. `uv run ruff format --check src tests` — formatting.
12. `uv run ruff check src tests` — linting.
13. `uv run mypy src` — type checking.
14. `uv run pytest --cov=mcp_builder --cov-branch -q` — tests with coverage
    (minimum **90%**, currently **92.9%**).

Auto-fix formatting and lint issues with:
```bash
uv run ruff format src tests
uv run ruff check src tests --fix
```

## Testing rules

15. When adding or modifying features, always add or update tests.
16. Run only fast tests during iteration (no network):
    ```
    uv run pytest -m "not generated and not mcp_smoke" -q
    ```
17. When generated output changes (templates, adapter, features):
    - Regenerate golden trees: `uv run python scripts/update_golden.py`
    - Verify golden tests: `uv run pytest -m golden -q`
    - Commit golden tree changes alongside the template changes.
18. New feature generators and target adapters need:
    - Unit tests for planning/validation.
    - Golden tree entries.
    - At least one acceptance test (`@pytest.mark.generated`).

## Security rules

19. **Path safety**: All generated and state-derived paths must be contained
    inside the project root. Reject symlinked destination components.
20. **Serialization**: Generated Python, TOML, and Compose values must be
    serialized contextually — never interpolate raw manifest values into
    code without escaping.
21. **YAML safety**: Reject YAML anchors, aliases, and unsafe tags before
    object construction. Use `yaml.SafeLoader` or equivalent.
22. **Validation**: Validate HTTP host, port, and path values at the manifest
    boundary. Reject context-breaking values (newlines, URL params, etc.).
23. **Versions**: Validate that package versions conform to PEP 440.
24. Do not commit secrets, API keys, or tokens. Never log sensitive data.
25. Do not introduce dependencies that could create a supply chain risk
    without explicit review.

## Release rules

26. The package version is derived from the **latest git tag** via `hatch-vcs`.
    The tag is the single source of truth — never hardcode a version.
27. To create a release, tag and push:
    ```bash
    git tag v0.1.0a4 && git push origin v0.1.0a4
    ```
28. The CI pipeline builds, signs, and publishes automatically.
    No manual bump or auto-bump step needed.
29. Release notes go in `docs/release-notes-<version>.md` and `CHANGELOG.md`.
    These are manual — create the file before tagging.

## Documentation rules

31. Update `CHANGELOG.md` for every user-facing change.
32. Keep `README.md` badges and install instructions in sync with the
    current release.
33. When adding a new profile, target, or feature, update:
    - `docs/release-readiness-plan.md` if applicable.
    - The compatibility table in `README.md` and `SUPPORT.md`.
34. ADRs go in `docs/adr/` with a sequential number and clear title.

## Dependabot and supply chain

35. Dependabot is configured in `.github/dependabot.yml`:
    - Runtime dependencies: weekly, grouped by patch.
    - GitHub Actions: monthly, grouped.
    - Security updates: grouped automatically.
    - FastMCP and MCP SDK are excluded (pinned by compatibility profile).
36. All GitHub Actions must be pinned to **immutable commit hashes**, not
    version tags. Use a trailing comment to document the semantic version:
    ```yaml
    - uses: actions/some-action@abc123def456... # vX.Y.Z
    ```
