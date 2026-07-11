# ADR 0002: Manifest Represents Project Intent, Not Complete Tool Runtime State

**Status:** Proposed  
**Date:** 2026-07-10

## Context

An infrastructure-as-code analogy suggests declaring every MCP resource in YAML. For code-defined tools, this risks duplicating names, schemas, descriptions, and type information between YAML and Python.

## Decision

The v1 manifest configures generation target, compatibility, transport, package shape, and optional project assets. Tool implementations and Python type hints remain runtime truth. The manifest may request scaffold examples, not maintain a complete tool catalog.

## Consequences

Positive:

- smaller manifest;
- less drift and duplication;
- idiomatic FastMCP development;
- easier adoption.

Negative:

- the builder cannot reason about every tool before inspecting code;
- future policy/budget assignment per tool needs an introspected catalog or separate contract layer.

## Revisit condition

Revisit when implementing audit/policy/budget features. Prefer generating a catalog from code before requiring manual duplication.
