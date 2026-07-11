# ADR 0004: Defer Runtime Governance from the Core Builder Release

**Status:** Proposed  
**Date:** 2026-07-10

## Context

Execution budgets, loop detection, audit receipts, policy, approvals, agent contracts, and A2A are strategically relevant. They also introduce substantial runtime semantics and adoption friction.

## Decision

Do not implement these capabilities in v0.1. Reserve namespaced extension seams and document the ecosystem roadmap.

## Consequences

- the initial product has a clear adoption story;
- architecture must avoid assumptions that block later middleware/adapter composition;
- the project cannot initially claim comprehensive production governance;
- future features require separate specifications and validation evidence.
