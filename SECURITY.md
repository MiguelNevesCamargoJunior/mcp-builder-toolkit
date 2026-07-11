# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x (alpha) | Yes — best-effort security fixes |
| unreleased main | Yes — report against latest `main` |

Alpha releases are **not** covered by an SLA. Prefer pinning exact versions in production pilots.

## Scope of this project

MCP Builder Toolkit generates project scaffolds. Security responsibilities split as:

| Component | Responsibility |
|-----------|----------------|
| Builder CLI | Safe YAML load, path containment, no secret embedding, conflict-safe writes |
| Generated projects | Application-level auth, input validation, network exposure, dependency updates |
| FastMCP / MCP SDKs | Protocol implementation and framework security |

See `docs/threat-model.md` for the builder threat model.

## Reporting a vulnerability

**Do not** open a public GitHub issue for security-sensitive reports.

1. Use [GitHub private vulnerability reporting](https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/security/advisories/new) with:
   - description and impact
   - reproduction steps
   - affected versions / commit
   - optional suggested fix
2. Do not open a public issue containing vulnerability details. If private
   reporting is temporarily unavailable, contact the maintainer through the
   GitHub profile to establish a private channel first.
3. Allow a reasonable window (typically 90 days) before public disclosure.
4. We will acknowledge receipt and coordinate a fix and advisory when appropriate.

## Safe defaults in the builder

- YAML is loaded with a restricted safe loader (no custom tags).
- Manifest size and nesting are capped.
- Generation rejects path traversal.
- HTTP profiles default to loopback (`127.0.0.1`) and document exposure risks.
- Generated examples never embed real credentials.

## Supply chain

CI should include dependency review, secret scanning, and static analysis where the host platform allows (see `.github/workflows/`). Release packaging aims for SBOM/provenance in the release pipeline.
