# Release notes — v0.1.0a4

Infrastructure and community readiness alpha.

## Highlights

- **hatch-vcs**: package version now derives from the git tag automatically.
  No more `__version__` in `__init__.py`, no bump script, no auto-bump CI step.
  The tag is the single source of truth.
- **CI optimized**: matrix reduced from 9 to 5 runs (all Python versions on
  Linux, macOS/Windows on 3.13 only).
- **GitHub Actions updated**: `checkout` v7, `setup-uv` v8, `upload/download-artifact` v7/v8,
  `sigstore` v3.4, `scorecard` v2.4.3, `codeql` v3.29.11.
- **Dependabot configured**: grouped security and patch updates, weekly schedule.
- **Branch protection**: `main` is now protected with PR requirement, 1 approval,
  and required status checks (`test` + `security`).
- **Issue/PR templates**: bug report, feature request, PR template, security report link.
- **CONTRIBUTING.md**: comprehensive guide for external contributors (fork workflow,
  quality gates, spec-driven changes).
- **AGENTS.md**: expanded rules for AI agents (36 rules covering constitution,
  testing, security, release, dependabot).
- **Wiki**: Home, Roadmap, Architecture, and FAQ pages created.
- **Dependency graph**: enabled, with `dependency-review` back in CI.

## Compatibility

- Manifest: `mcpbuilder.dev/v1alpha1`
- Profile: `fastmcp-python-2026.07`
- MCP: `2025-11-25`
- FastMCP: `>=3.4.4,<3.5`
- Python: `>=3.12,<3.15`

This remains an evaluation alpha, not a production-readiness claim.
