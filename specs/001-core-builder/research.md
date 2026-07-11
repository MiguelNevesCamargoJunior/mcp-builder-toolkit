# Research: MCP Builder Toolkit Core

**Research date:** 2026-07-10  
**Scope:** decisions required for the first builder release while preserving a credible ecosystem path.

## Decision 1 — Position as a builder, not another MCP SDK

**Decision:** Build on an established MCP runtime and official protocol behavior. Do not implement JSON-RPC/MCP transport internals unless required for testing or an upstream contribution.

**Rationale:** Official SDKs already own protocol implementation, while FastMCP provides a mature Python development surface, middleware, auth patterns, and OpenTelemetry support. The unfilled product space is a coherent project-generation and lifecycle experience.

**Rejected alternatives:**

- New MCP runtime: duplicates active, fast-changing work and creates conformance risk.
- Static GitHub template only: useful for one copy but weak for validation, profiles, safe regeneration, and future feature composition.
- Gateway-first product: solves a later organizational problem and competes with existing gateways.

## Decision 2 — FastMCP Python first

**Decision:** Generate FastMCP 3.x projects first and pin a tested compatibility range per builder release.

**Evidence:** FastMCP is actively maintained and its July 2026 releases include substantial auth, proxy, SSRF, DNS-rebinding, schema, middleware, and reliability work. Its pace is an advantage for runtime capability but requires explicit compatibility testing from the builder.

**Risk:** FastMCP’s rapid release cadence can break generated templates or create security-sensitive defaults. The builder therefore owns tested profiles rather than using an unconstrained latest dependency.

**Rejected alternatives:**

- Official Python SDK low-level API first: more direct but requires the builder to generate more infrastructure and offers less immediate DX.
- TypeScript first: viable second target, but Python better matches initial contributor expertise and agent/MLOps adoption.
- Multi-target v1: multiplies tests and forces premature abstractions.

## Decision 3 — Stable MCP protocol profile

**Decision:** Target MCP specification `2025-11-25` for v0.1 and track subsequent stateless/draft changes separately.

**Rationale:** The MCP ecosystem is actively evolving through Specification Enhancement Proposals, extensions, working groups, conformance work, and SDK tiering. The builder must isolate protocol compatibility rather than encode draft assumptions in its domain core.

**Implication:** protocol date version is a compatibility input. It is not the builder’s own API version.

## Decision 4 — Manifest describes project intent, not complete runtime truth

**Decision:** The v1 manifest configures target, protocol profile, transport, package shape, and generated operational features. Python source and type hints remain authoritative for tool implementation and runtime schemas.

**Rationale:** Requiring users to duplicate every tool schema in YAML creates drift between manifest and code. The builder may scaffold tool files, but it should later derive a server catalog by introspection/conformance rather than require dual authoring.

**Future option:** an explicit contract or catalog file can be generated from code and enriched with policies, risk annotations, or budgets when those layers exist.

## Decision 5 — Thin custom generator over static templates

**Decision:** Use Jinja2 and a small generation planner with artifact ownership/state.

**Rationale:** Cookiecutter is optimized for initial scaffolding. Copier offers update semantics but introduces its own answers/update model. The core differentiation here is a versioned manifest, compatibility profiles, composable feature outputs, and safe file ownership. A thin project-specific planner keeps those semantics explicit.

**Risk:** custom regeneration logic is easy to get wrong. It must be transactional, test-heavy, and intentionally limited.

## Decision 6 — Generated code has no builder runtime dependency

**Decision:** Generated projects depend on FastMCP and ordinary Python libraries, not on the builder package.

**Rationale:** This improves transparency, makes adoption reversible, and prevents the builder from becoming an accidental control plane.

**Trade-off:** runtime controls added later cannot rely solely on builder-generated wrappers if users regenerate infrequently. They should be optional runtime packages or middleware modules with explicit versions.

## Decision 7 — Internal extension seams, no public plugin API yet

**Decision:** Introduce internal `TargetAdapter` and `FeatureGenerator` protocols but do not promise third-party compatibility in v0.1.

**Rationale:** A second implementation is required to prove abstractions. The interfaces are initially refactorable.

## Ecosystem map

### SDK/runtime layer

- MCP Python SDK — official protocol implementation.
- MCP TypeScript, Java, C#, and other official SDKs — future target candidates.
- FastMCP — high-level Python MCP framework and selected first target.

### Scaffold/template layer

- Community Python and TypeScript MCP boilerplates — direct substitutes for the initial copy experience.
- Agent skills and coding-agent generators — substitutes for “generate me a project,” but with lower determinism and lifecycle guarantees.

### Gateway/management layer

- Microsoft MCP Gateway and community gateway/registry projects.
- Auth proxies and commercial/API gateway MCP integrations.

These are integration targets, not v1 competitors.

### Governance/runtime-control layer

- Microsoft Agent Governance Toolkit / Agent Control Specification.
- OWASP Agent Observability Standard.
- emerging behavioral-contract and policy-as-code work.

These validate the long-term problem but also warn against inventing a competing contract system prematurely.

### Agent-to-agent layer

- A2A is complementary to MCP: agent-to-agent interoperability rather than agent-to-tool access.
- ACP has converged toward A2A.
- ANP and other decentralized proposals remain relevant research inputs but are not immediate targets.

## Opportunity assessment

### Strong opportunity

A predictable golden path that generates readable MCP projects, with tested compatibility profiles and safe regeneration, is meaningfully different from both a raw SDK and a static template.

### Medium opportunity

An internal platform profile mechanism could let organizations distribute approved defaults. This should follow public adoption, not precede it.

### Long-term opportunity

Production feature packs for auth, telemetry, audit, policy, and budgets can become the durable differentiation after the builder has users.

### Weak or dangerous opportunity

Trying to define a universal agent contract, gateway, control plane, and protocol abstraction in the first repository would create an incoherent product and conflict with active initiatives.

## Adoption risks

1. **AI coding agents make scaffolders feel unnecessary.**  
   Mitigation: compete on deterministic output, compatibility, repeatability, diagnostics, and upgrades—not raw code generation.

2. **FastMCP adds an official project generator.**  
   Mitigation: integrate or contribute rather than fork; retain value in profiles, safe regeneration, and operational feature composition.

3. **MCP specification changes quickly.**  
   Mitigation: compatibility profiles, conformance tests, adapter isolation, stable-profile default.

4. **“Production-ready” claims invite scrutiny.**  
   Mitigation: use precise language such as “production-oriented project baseline” and document exclusions.

5. **Manifest becomes another configuration language.**  
   Mitigation: keep it small; configure only project shape; derive rather than duplicate runtime facts.

6. **Regeneration damages user code.**  
   Mitigation: scaffold-once defaults, state hashes, dry-run, conflicts, transactional writes.

## Security and governance implications

MCP tools can access data and trigger actions, so generated projects need baseline input validation, access-control readiness, rate-limit readiness, safe output handling, conservative network exposure, and audit-friendly logging structures. Full enforcement belongs to later feature packs.

Agentic security guidance increasingly emphasizes least privilege, tool misuse, identity abuse, cascading failures, observability, approval gates, and supply-chain controls. These should influence the project constitution and roadmap without expanding v0.1 scope.

## Primary sources

- GitHub Spec Kit: https://github.com/github/spec-kit
- MCP specification 2025-11-25: https://modelcontextprotocol.io/specification/2025-11-25
- MCP roadmap: https://modelcontextprotocol.io/development/roadmap
- MCP SEPs: https://modelcontextprotocol.io/seps
- MCP extensions: https://modelcontextprotocol.io/extensions/overview
- MCP security best practices: https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- FastMCP documentation: https://gofastmcp.com/getting-started/welcome
- FastMCP middleware: https://gofastmcp.com/servers/middleware
- FastMCP telemetry: https://gofastmcp.com/servers/telemetry
- FastMCP releases: https://github.com/PrefectHQ/fastmcp/releases
- A2A protocol: https://a2a-protocol.org/latest/
- Microsoft Agent Governance Toolkit: https://github.com/microsoft/agent-governance-toolkit
- OWASP Agentic Top 10: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- OWASP Agent Observability Standard: https://owasp.org/www-project-agent-observability-standard-2/
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- CISA/partners agentic AI guidance: https://www.cisa.gov/resources-tools/resources/careful-adoption-agentic-ai-services
- OpenSSF Scorecard: https://scorecard.dev/
- SLSA provenance: https://slsa.dev/provenance/v1
- Sigstore: https://www.sigstore.dev/
