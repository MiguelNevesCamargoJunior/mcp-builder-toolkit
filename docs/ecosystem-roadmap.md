# Ecosystem Roadmap

The roadmap protects a simple adoption path while preserving the broader agent-governance vision.

## Stage 0 — Validate the golden path

**Question:** Does a deterministic builder solve a real problem that coding agents and static templates do not?

Deliver:

- CLI and manifest prototype;
- FastMCP stdio server;
- tests and generated README;
- five user interviews and three observed pilot runs.

Kill or pivot signal: users consistently prefer a maintained static template or coding-agent skill and see no value in regeneration/diagnostics.

## Stage 1 — Builder v0.x

**Promise:** Create and evolve a well-structured Python MCP server project.

- stable manifest alpha;
- safe generation and regeneration;
- stdio and Streamable HTTP;
- Docker/Compose/CI;
- compatibility profiles;
- doctor and conformance smoke tests;
- MCP Registry metadata generation may be added if low-cost.

No runtime control plane.

## Stage 2 — Production feature packs

**Promise:** Add common operational capabilities without custom assembly.

Candidate packs, ordered by evidence and ecosystem fit:

1. OpenTelemetry configuration and semantic conventions;
2. auth integration recipes/adapters using existing providers and MCP auth extensions;
3. rate limiting and conservative network/security profile;
4. audit-event middleware with pluggable sinks;
5. release/SBOM/provenance pack.

Each pack must remain optional and independently testable.

## Stage 3 — Runtime governance

**Promise:** Put enforceable limits around autonomous use of tools.

Potential capabilities:

- execution budgets: calls, wall-clock, retries, depth;
- repetition and loop detection;
- tokens and cost only where the runtime can observe them reliably;
- policy-as-code adapters;
- human approval gates;
- egress and PII controls;
- tamper-evident audit receipts.

Design rule: observe before enforcing by default; enforcement is explicit per profile/tool/environment.

## Stage 4 — Agent ecosystem adapters

**Promise:** Compile shared operational intent into multiple agent protocol surfaces.

- A2A Agent Card and server adapter;
- gateway and registry outputs;
- contract descriptors mapped to emerging standards rather than invented in isolation;
- shared identity, policy, telemetry, and receipt primitives where semantics truly align.

## Stage 5 — Platform ecosystem, only if adoption justifies it

Possible organization-level capabilities:

- curated internal profile registry;
- signed template/profile distribution;
- compatibility dashboards;
- fleet inventory and drift reporting;
- policy bundles and evidence export.

This stage must not force hosted infrastructure on open-source users.

## Cross-stage guardrails

- No stage begins because it is conceptually attractive; it begins after user evidence.
- The core manifest stays small. Feature packs own their schemas through namespaced extensions.
- Gateways are integrated, not rebuilt.
- MCP and A2A remain distinct target semantics.
- Contracts map to existing standards or publish explicit experimental status.
- Token/cost claims distinguish measured, provider-reported, and estimated values.
