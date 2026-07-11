# Alpha release readiness plan

This plan closes the gap between the implemented v0.1 alpha and a repository
that external users can safely evaluate. It does not expand the core builder
into declarative API or tool generation.

## Release blockers

- [x] Make generated Streamable HTTP containers reachable through their
  published port without changing the conservative host-side bind.
- [x] Turn the container HTTP check into a real MCP smoke test that fails CI on
  regressions.
- [x] Keep `scaffolds.exampleTool: false` compatible with generated tests.
- [x] Make staged generation roll back project files when apply or state writes
  fail.
- [x] Give the public `structuredLogging` option observable generated behavior.

## Quality gates

- [x] Add regression coverage for every release blocker.
- [x] Raise the enforced builder coverage threshold from 80% to 90%.
- [x] Pass Ruff, formatting, strict mypy, unit tests, generated-project tests,
  stdio MCP smoke tests, HTTP MCP smoke tests, and package build checks.
- [x] Keep public schemas and runtime schema export identical.

## Publication readiness

- [x] Present the product as a manifest-driven project generator, not a no-code
  API integration runtime.
- [x] Document YAML capabilities, boundaries, file ownership, security scope,
  and alpha support expectations.
- [x] Initialize local Git history without committing until maintainer review.
- [x] Create the personal GitHub repository and configure `origin` after GitHub
  authentication is restored.
- [ ] Run external pilot sessions after publication; pilot evidence remains a
  human-operated release follow-up.

## Acceptance criteria

The release candidate is ready for maintainer review: all automated gates pass
locally and the working tree contains only intentional files. Remaining actions
are the maintainer-approved first commit and push, green hosted workflows,
release-secret configuration, the `v0.1.0a3` tag, and post-publication pilots.
