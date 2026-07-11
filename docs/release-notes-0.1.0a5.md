# Release notes — v0.1.0a5

Security, validation, and review-response alpha.

## Highlights

- **Lock security**: `GenerationLock` now uses `safe_project_path` to block
  symlink and junction traversal. Stale lock verification validates content
  before removal.
- **Read-only release builds**: The release workflow no longer modifies the
  checked-out source. Coverage badge updates are handled by a separate
  workflow on `main` push.
- **Doctor Python check fixed**: Reads supported versions from the
  compatibility profile — correctly reports Python 3.14 as supported.
- **Schema in sync**: JSON Schema is now generated from Pydantic models.
  CI fails if the committed `manifest.schema.json` diverges from the
  runtime models.
- **Init validation**: `mcp-builder init` now validates profile existence,
  DNS label format, and rejects Python keywords as package names before
  writing the manifest.
- **Generated CI includes 3.14**: Projects generated with `githubActions`
  feature now test Python 3.12, 3.13, and 3.14.

## Compatibility

- Manifest: `mcpbuilder.dev/v1alpha1`
- Profile: `fastmcp-python-2026.07`
- MCP: `2025-11-25`
- FastMCP: `>=3.4.4,<3.5`
- Python: `>=3.12,<3.15`

This remains an evaluation alpha, not a production-readiness claim.
