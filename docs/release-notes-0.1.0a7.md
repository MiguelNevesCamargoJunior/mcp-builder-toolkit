# Release notes — v0.1.0a7

Infrastructure hardening and review-response alpha.

## Highlights

- **PR lint fixed**: shell injection vector removed (env var), scope pattern restricted.
- **Auto-merge restricted**: patch only, dev dependencies and GitHub Actions only.
- **Stale bot disabled**: too early for automation; manual triage instead.
- **Wiki sync**: removed `--delete` flag to avoid overwriting manually created wiki pages.
- **Agent playbooks**: moved to `.agents/` directory with shared JSON Schema output.
- **Coverage badge auto-push removed**: branch protection prevents direct pushes.
- **New specs**: 002 (capability scaffolding), 003 (server verification), 004 (profile upgrades).

## Compatibility

- Manifest: `mcpbuilder.dev/v1alpha1`
- Profile: `fastmcp-python-2026.07`
- MCP: `2025-11-25`
- FastMCP: `>=3.4.4,<3.5`
- Python: `>=3.12,<3.15`
