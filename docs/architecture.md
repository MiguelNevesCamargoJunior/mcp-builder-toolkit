# Architecture: Builder Core and Ecosystem Evolution

## Context

MCP Builder Toolkit begins as a local developer tool. It compiles a small project manifest into source code and operational assets. The long-term ecosystem may add runtime packages and protocol adapters, but the core builder remains useful independently.

## System context

```text
Developer / Platform Engineer
          │
          │ manifest + CLI
          ▼
MCP Builder Toolkit
          │
          ├── generated Python/FastMCP source
          ├── tests and documentation
          ├── Docker/CI assets
          └── local generation state
                         │
                         ▼
                MCP host/client ecosystem
```

The builder is not in the runtime request path after generation.

## Core architecture

```text
┌─────────────────────────────────────────────────────────┐
│ CLI                                                     │
│ init | validate | generate | doctor                     │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Manifest & Diagnostics                                  │
│ parse | schema | semantic checks | normalization        │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Project Domain                                          │
│ ProjectSpec | TransportSpec | FeatureSelection          │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Generation Planner                                      │
│ TargetAdapter + FeatureGenerators → ArtifactPlan        │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│ State & Filesystem Transaction                          │
│ ownership | hashes | conflicts | dry-run | atomic apply │
└─────────────────────────────────────────────────────────┘
```

## Separation rules

1. Manifest models do not import SDK runtime classes.
2. Target adapters do not write directly to disk.
3. Feature generators emit artifacts through the same planner.
4. Only the transaction layer mutates the target filesystem.
5. Domain and generation logic produce diagnostics rather than printing.
6. Runtime governance is not placed in the builder core package.

## Evolution model

### Layer 1 — Builder core

Local CLI, manifest, target adapters, feature generators, safe regeneration, compatibility testing.

### Layer 2 — Production feature packs

Optional generated/runtime integrations:

- auth configuration and provider adapters;
- OpenTelemetry setup;
- structured audit events;
- rate limiting and request controls;
- security hardening profiles.

These may combine generated config with small runtime packages.

### Layer 3 — Governance runtime

Separate packages/services for:

- policy enforcement;
- approvals;
- execution budgets;
- loop/repetition control;
- tamper-evident receipts;
- PII/egress controls.

The builder can install/configure them, but they should not make the generator a runtime dependency.

### Layer 4 — Ecosystem adapters

- A2A Agent Card/server adapter;
- gateway descriptors;
- registry publishing metadata;
- agent contract compilation or compatibility adapters.

## Why not a universal agent model now?

MCP servers, A2A agents, gateways, and governance runtimes have different lifecycle and security semantics. A universal abstraction created before two or more concrete adapters exist will likely erase important differences. The project therefore shares only proven concepts—identity metadata, compatibility profile, generated artifacts, and extension modules—until real implementations justify more.

## Potential future repository split

```text
mcp-builder-toolkit       # CLI, manifest, generators
mcp-builder-runtime       # optional shared middleware primitives
mcp-builder-otel          # telemetry feature pack
mcp-builder-governance    # policy/budget/audit pack
mcp-builder-a2a           # A2A adapter
```

A monorepo may be simpler initially, but package boundaries should reflect runtime coupling and release cadence rather than branding.
