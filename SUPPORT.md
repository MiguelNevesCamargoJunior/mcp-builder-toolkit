# Support policy

## Alpha support (`0.1.x`)

MCP Builder Toolkit is in **alpha**. Support is best-effort:

- Bug reports: GitHub Issues with repro steps and `mcp-builder doctor --format json` output when relevant.
- Questions: GitHub Discussions or Issues labeled `question`.
- Security: follow `SECURITY.md` (private disclosure).

### What we support

- CLI commands: `init`, `validate`, `generate`, `doctor`
- Manifest API: `mcpbuilder.dev/v1alpha1`
- Compatibility profile: `fastmcp-python-2026.07` (FastMCP `>=3.4.4,<3.5`, Python `>=3.12,<3.15`, MCP `2025-11-25`)

### What we do not promise in alpha

- API stability across minor releases (breaking changes noted in release notes)
- Enterprise SLA / 24×7 support
- Hosted control plane or managed runtime
- Full enterprise auth, policy, audit, or multi-language generation

## Generated project support

The builder does **not** ship as a runtime dependency of generated projects.
Once generated, maintain FastMCP/dependency upgrades in the generated repo.

## Compatibility upgrades

When a new profile (for example `fastmcp-python-2026.xx`) is published:

1. Update `spec.target.profile` in `mcp-builder.yaml`
2. Run `mcp-builder generate --dry-run`
3. Resolve managed-file conflicts with `--force-managed PATH` as needed
