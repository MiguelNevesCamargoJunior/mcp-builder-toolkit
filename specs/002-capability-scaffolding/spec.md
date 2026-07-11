# Feature 002: Capability Scaffolding

**Status:** Draft
**Target release:** v0.2

## Summary

Extend the builder beyond project generation by allowing developers to add
individual MCP capabilities (tools, resources, prompts) to an existing
generated project.

## Motivation

Today the builder creates a single example tool. After that, the developer
must manually create files, register handlers, and write tests. This feature
makes the builder useful throughout development, not just at project creation.

## Commands

```bash
mcp-builder add tool search-documents
mcp-builder add resource customer-profile --uri "customer://{customer_id}"
mcp-builder add prompt summarize-case
```

## Behavior

- Files are created as `scaffold-once` — never overwritten.
- Each capability generates:
  - Typed function/class with docstring
  - Registration in the server
  - Initial test file
  - No invented business logic
- The manifest is NOT modified (capabilities are code, not configuration).

## Non-goals

- OpenAPI/API conversion
- Declarative tools in the manifest
- Code generation from natural language

## Exclusions

No runtime governance, budgets, A2A, or multi-language targets in this feature.
