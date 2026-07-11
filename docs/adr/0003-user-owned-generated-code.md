# ADR 0003: Generated Runtime Code Is User-Owned

**Status:** Proposed  
**Date:** 2026-07-10

## Decision

Generated server and tool source are conventional Python and do not depend on the builder package at runtime. Files are classified as managed, scaffold-once, or derived. User implementation files are scaffold-once by default.

## Consequences

- users can leave the builder without rewriting the server;
- generated code is inspectable and debuggable;
- regeneration requires explicit state and conflict semantics;
- future runtime feature packs must use explicit dependencies rather than hidden generator magic.
