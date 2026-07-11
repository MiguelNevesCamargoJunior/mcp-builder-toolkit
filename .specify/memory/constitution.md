# MCP Builder Toolkit Constitution

## Preamble

MCP Builder Toolkit exists to reduce the operational and cognitive cost of creating maintainable MCP servers. It must not become a competing protocol, a hidden runtime, or a speculative governance platform before it solves the basic developer workflow well.

This constitution governs product decisions, architecture, specifications, implementation plans, and contributions.

## Core principles

### I. Developer experience before platform breadth

The primary release path MUST optimize for a developer reaching a running, understandable MCP server quickly.

- The common path MUST be short, documented, and deterministic.
- Advanced controls MUST be opt-in and introduced progressively.
- A feature that increases conceptual surface without improving the initial build-run-test workflow MUST NOT enter the v1 core.
- Defaults MUST be useful without requiring knowledge of future governance concepts.

**Rationale:** adoption is more likely to come from a useful builder than from an ambitious but heavy agent-governance platform.

### II. Standards alignment, not protocol invention

The toolkit MUST compose with the MCP specification and official ecosystem rather than redefine them.

- Protocol-level concepts MUST retain their MCP meaning.
- Toolkit-specific concepts MUST use an explicit toolkit namespace.
- Stable MCP features MUST be preferred over draft behavior.
- Draft and experimental protocol features MUST be isolated behind compatibility profiles or adapters.
- The project MUST contribute findings upstream when implementation experience reveals a specification or ecosystem gap.

**Rationale:** the toolkit should absorb ecosystem complexity for users, not create a parallel standard.

### III. Transparent generation and user ownership

Generated code MUST be readable, conventional, and owned by the user.

- A generated server MUST run without the builder as a production runtime dependency.
- The builder MUST NOT require a proprietary control plane or hosted service.
- Generated source files intended for user modification MUST be scaffold-once by default.
- Managed files MUST be clearly identified and safely regenerated.
- The user MUST be able to inspect planned changes before files are written.

**Rationale:** hidden generation and runtime coupling undermine trust, maintainability, and open-source adoption.

### IV. Deterministic and safe generation

For the same normalized manifest, builder version, and generation profile, the output MUST be reproducible except for explicitly documented non-deterministic metadata.

- Generation MUST support dry-run output.
- Existing user changes MUST NOT be silently overwritten.
- File ownership and previous hashes MUST be recorded in local build state.
- Conflicts MUST fail clearly unless the user explicitly chooses a resolution strategy.
- Every generated artifact MUST have a traceable originating template and builder version.

**Rationale:** an infrastructure-inspired builder is only credible if change is predictable.

### V. Protocol-independent domain core

The core domain model MUST describe desired project capabilities and generation intent without depending directly on FastMCP implementation classes.

- FastMCP Python is the first target adapter, not the domain model.
- Transport, packaging, testing, and project-shape concepts MUST be represented independently of a concrete SDK where practical.
- New targets MUST be addable without rewriting manifest parsing or generation orchestration.
- Abstractions MUST be earned by a real second use case; premature generalization is prohibited.

**Rationale:** the project needs a future path beyond one SDK without paying the complexity cost immediately.

### VI. Secure defaults and supply-chain hygiene

The builder and generated projects MUST apply baseline secure engineering practices.

- Secrets MUST never be embedded in generated source or manifests.
- YAML parsing MUST use safe loading.
- Network binding MUST default to the least exposed useful setting.
- Dependencies MUST be pinned or constrained through tested compatibility profiles.
- CI MUST include tests, linting, type checks, dependency review, and secret scanning where available.
- Releases SHOULD produce provenance and signed artifacts when the release pipeline is introduced.

**Rationale:** a tool that generates integration servers becomes part of the software supply chain.

### VII. Contract-first testing

Externally visible behavior MUST be specified and tested before implementation is considered complete.

- CLI exit codes, diagnostics, manifest schema, and generated project acceptance tests MUST be treated as public contracts.
- Unit tests MUST cover domain and generation behavior.
- Golden/snapshot tests MAY be used for generated trees but MUST be reviewed for semantic value.
- End-to-end tests MUST run generated servers through at least one real MCP client or conformance path.
- Compatibility with the selected MCP/FastMCP profile MUST be continuously tested.

**Rationale:** generated output is the product; testing only the generator internals is insufficient.

### VIII. Evidence-based expansion

Roadmap expansion MUST follow demonstrated user pain, interoperability requirements, or upstream protocol evolution.

- Runtime governance, budgets, audit, contracts, and A2A MUST remain separate roadmap layers until validated.
- New modules MUST define a user, threat, or operational problem and measurable success criteria.
- The project MUST avoid claims such as “production-ready,” “secure,” or “enterprise-grade” without explicit scope and evidence.
- Research artifacts MUST distinguish stable facts, current ecosystem behavior, assumptions, and hypotheses.

**Rationale:** the long-term ecosystem vision is useful only if it does not distort the first product.

## Quality gates

A feature cannot be marked complete unless:

1. Its specification has testable acceptance scenarios.
2. Constitution checks in the implementation plan pass.
3. Public contracts are updated.
4. Tests cover success, failure, and conflict paths.
5. Generated code remains understandable without internal project knowledge.
6. Documentation enables an external developer to reproduce the intended workflow.
7. Security-sensitive behavior has an explicit threat analysis or documented non-applicability.

## Governance

- This constitution supersedes informal architectural preferences.
- Amendments require a written rationale, impact assessment, and migration note.
- Principle removals or semantic reversals require a major constitution version.
- New enforceable principles require a minor version.
- Clarifications and non-semantic wording changes require a patch version.
- Specifications and plans MUST include a constitution compliance section.
- Exceptions MUST be temporary, documented in an ADR, and include an expiry or review condition.

**Version:** 1.0.0  
**Ratified:** 2026-07-10  
**Last amended:** 2026-07-10
