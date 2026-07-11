# Release notes — v0.1.0a1

## Summary

Manifest-driven CLI that generates readable, tested Python MCP server projects
with safe regeneration and optional Docker/CI assets.

This is the first public alpha. It is intended for evaluation and pilot
projects, not production workloads.

## Highlights

- Generate stdio or Streamable HTTP FastMCP Python projects.
- Preview changes and safely preserve scaffold-once implementation files.
- Detect managed-file conflicts and project drift.
- Generate tests, Ruff, mypy, Docker, Compose, GitHub Actions, and JSON logs.
- Run generated projects without a runtime dependency on the builder.
- Validate the generated server with real MCP client smoke tests.

## Supported profile

| Field | Value |
|-------|-------|
| Profile | `fastmcp-python-2026.07` |
| Runtime | `fastmcp-python` |
| FastMCP | `>=3.4.4,<3.5` |
| Python | `>=3.12,<3.14` |
| MCP protocol | `2025-11-25` |
| Manifest API | `mcpbuilder.dev/v1alpha1` |

## Commands

- `mcp-builder init`
- `mcp-builder validate`
- `mcp-builder generate` (`--dry-run`, `--force-managed`)
- `mcp-builder doctor`

## Security / support scope

- Alpha software; best-effort support (see `SUPPORT.md`, `SECURITY.md`).
- No runtime governance, auth providers, budgets, audit, A2A, or multi-language targets.
- Generated projects do not depend on this package at runtime.

## Migration notes (alpha series)

- Manifest and diagnostics schemas are frozen as **v1alpha1** for the alpha line.
- Breaking manifest changes require a new `apiVersion` or documented migration.
- Rebuild managed assets after upgrading the builder: `mcp-builder generate --dry-run`.

## Maintainer publishing checklist

```bash
uv sync --all-extras --locked
uv run ruff format --check src tests
uv run ruff check src tests
uv run mypy src
uv run pytest --cov=mcp_builder --cov-branch
uv build
uv export --preview-features sbom-export --format cyclonedx1.5 --no-dev --locked -o sbom.cdx.json
# Test index (example):
# uv publish --publish-url https://test.pypi.org/legacy/ --token $TEST_PYPI_TOKEN
# External install test:
# uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-builder --version
```

SBOM / Sigstore signing are configured in release CI when maintainers enable the
release workflow (see `.github/workflows/release.yml`). The tag for this release
must be exactly `v0.1.0a1` and match `pyproject.toml`.
