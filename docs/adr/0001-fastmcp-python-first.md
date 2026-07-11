# ADR 0001: FastMCP Python as the First Generation Target

**Status:** Proposed  
**Date:** 2026-07-10

## Context

The project needs a first MCP runtime target. Supporting several SDKs immediately would multiply implementation and conformance cost.

## Decision

Generate Python 3.12+ projects using a tested FastMCP 3.x compatibility profile.

FastMCP is treated as a target adapter. The domain core cannot depend on FastMCP classes.

## Consequences

Positive:

- fast path to strong Python developer experience;
- existing middleware/auth/telemetry capabilities for future packs;
- smaller generated code surface than low-level SDK use.

Negative:

- dependency on a rapidly evolving project;
- builder releases need integration tests and version constraints;
- some MCP draft/stable transitions may arrive at different times.

## Revisit condition

Revisit after v0.1 when implementing a TypeScript or official low-level Python adapter spike.
