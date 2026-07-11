# Release notes — v0.1.0a3

Security and release-hardening alpha for MCP Builder Toolkit.

## Highlights

- Contains every generated and state-derived path inside the project root and
  rejects symlinked destination components.
- Serializes manifest values safely for generated Python, TOML, and Compose
  YAML.
- Rejects YAML anchors and aliases, invalid HTTP hosts/paths, and versions that
  are not valid PEP 440.
- Removes public CLI flags that had no alpha behavior and validates enum
  options at the command boundary.
- Uses one package-version source and verifies release tags against it.
- Builds with `--no-sources`, then installs and exercises both wheel and sdist
  before signing or publishing.
- Splits read-only build verification from the privileged publish job.

## Compatibility

- Manifest: `mcpbuilder.dev/v1alpha1`
- Profile: `fastmcp-python-2026.07`
- MCP: `2025-11-25`
- FastMCP: `>=3.4.4,<3.5`
- Python: `>=3.12,<3.15`

This remains an evaluation alpha, not a production-readiness claim.
