# Changelog

All notable changes to MCP Builder Toolkit are documented here. The project
uses semantic versioning; alpha releases may change internal extension APIs,
while published manifest and diagnostic contracts follow their own versioned
schemas.

## [Unreleased]

## [0.1.0a4] - 2026-07-10

### Added

- Dependabot configuration with grouped security and patch updates.
- Branch protection rules for `main` (PR + 1 approval + required checks).
- Issue and PR templates (bug report, feature request, security report).
- Comprehensive CONTRIBUTING.md for external contributors.
- Expanded AGENTS.md with 36 rules for AI agents.
- GitHub Wiki with Home, Roadmap, Architecture, and FAQ.

### Changed

- Package version now derives from git tags via `hatch-vcs`. No more
  `__version__` in `__init__.py` — the tag is the single source of truth.
- CI matrix optimized from 9 to 5 runs (all Python on Linux, macOS/Windows
  on 3.13 only).
- All GitHub Actions bumped to latest versions.
- Dependency graph enabled; `dependency-review` restored in CI.

### Removed

- `bump_version.py` simplified — no longer handles version bumps.
- Auto-bump step in release workflow (no longer needed with `hatch-vcs`).
- Hardcoded coverage badge removed (kept manual for security).

## [0.1.0a3] - 2026-07-10

### Security

- Contain plan and state paths inside the project and reject symlinked
  destination components.
- Serialize generated Python, TOML, and Compose values contextually.
- Reject YAML anchors and aliases before object construction.

### Changed

- Remove alpha CLI flags without implemented behavior and validate enum options.
- Use one package version source and verify release tags against it.
- Smoke-test wheel and sdist before the privileged publish job.

## [0.1.0a2] - 2026-07-10

- Added Python 3.14 support to the builder, generated profile, CI, and docs.
- Added PyPI token fallback for the alpha release workflow.

## [0.1.0a1] - 2026-07-10

First public alpha.

### Added

- `init`, `validate`, `generate`, and `doctor` CLI workflows.
- Versioned `mcpbuilder.dev/v1alpha1` YAML manifest and JSON Schema.
- FastMCP Python generation for stdio and Streamable HTTP.
- Optional Docker, Compose, GitHub Actions, tests, linting, typing, and JSON
  logging outputs.
- Dry-run planning, managed/scaffold-once/derived ownership, conflict detection,
  scoped managed-file override, locking, staged writes, and rollback.
- Generated-project quality tests and real MCP client smoke tests.
- Cross-platform CI, security workflows, release artifacts, CycloneDX SBOM, and
  Sigstore signing configuration.

### Security

- Restricted safe YAML loading with size, nesting, and collection limits.
- Path traversal and symlink-oriented generation tests.
- Conservative local HTTP defaults and non-root generated containers.

### Known alpha boundaries

- Tools and API integrations are implemented in generated Python source, not
  declaratively in YAML.
- Only FastMCP Python, Python 3.12-3.14, and MCP `2025-11-25` are supported.
- Authentication, gateways, governance, audit, A2A, and multi-language targets
  are outside this release.

[Unreleased]: https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/compare/v0.1.0a4...HEAD
[0.1.0a4]: https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/releases/tag/v0.1.0a4
[0.1.0a3]: https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/releases/tag/v0.1.0a3
[0.1.0a2]: https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/releases/tag/v0.1.0a2
[0.1.0a1]: https://github.com/MiguelNevesCamargoJunior/mcp-builder-toolkit/releases/tag/v0.1.0a1
