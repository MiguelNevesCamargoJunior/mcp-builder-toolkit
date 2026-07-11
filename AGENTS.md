# Agent Instructions

Before changing implementation or specifications:

1. Read `.specify/memory/constitution.md`.
2. Read `specs/001-core-builder/spec.md`, `plan.md`, and `tasks.md`.
3. Treat contracts under `specs/001-core-builder/contracts/` as public alpha contracts.
4. Do not add runtime governance, budgets, audit, A2A, agent contracts, gateways, or multi-language generation to feature `001-core-builder`.
5. Do not introduce a builder runtime dependency into generated projects.
6. Preserve the distinction between managed, scaffold-once, and derived artifacts.
7. Verify current MCP/FastMCP behavior from primary sources before changing compatibility assumptions.
8. Add or update acceptance tests whenever generated output changes.
9. Never silently overwrite user-modified files.
10. Prefer small vertical increments that keep generated reference projects executable.

When a proposed change conflicts with the constitution, write an ADR and stop implementation until the exception is explicitly accepted.
