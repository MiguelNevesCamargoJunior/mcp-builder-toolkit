# Feature 003: Server Verification

**Status:** Draft
**Target release:** v0.2

## Summary

Allow developers to verify that their generated server works correctly,
both locally (stdio) and remotely (HTTP), without leaving the CLI.

## Motivation

Today the only way to test a generated server is to run it and call it
manually. A built-in `mcp-builder verify` command gives instant feedback
and enables CI integration.

## Command

```bash
mcp-builder verify
mcp-builder verify --command "uv run my-server"
mcp-builder verify --url http://localhost:8000/mcp
mcp-builder verify --format json
```

## Checks

- MCP initialize / handshake
- Negotiated protocol version
- List tools, resources, prompts
- All schemas are valid JSON Schema
- Optional: call `health` tool
- Timeout and cancellation behavior
- No unintended `0.0.0.0` exposure when remote
- Structured JSON output for CI

## Non-goals

- Performance benchmarks
- Load testing
- Security scanning (covered by other tools)
