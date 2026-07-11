# Feature 004: Profile Upgrades

**Status:** Draft
**Target release:** v0.3

## Summary

Allow developers to list, inspect, and upgrade compatibility profiles for
existing generated projects.

## Motivation

As FastMCP and the MCP protocol evolve, generated projects need a safe,
documented upgrade path. This feature makes compatibility visible and
actionable.

## Commands

```bash
mcp-builder profile list
mcp-builder profile show fastmcp-python-2026.07
mcp-builder profile check
mcp-builder upgrade --to fastmcp-python-2026.10
```

## Upgrade behavior

- Compare profiles and show differences
- Update only the manifest (never scaffold-once code)
- Dry-run regeneration before applying
- Point to required migration notes
- Fail if any managed files would conflict

## Non-goals

- Automatic dependency updates (handled by Dependabot)
- Multi-profile project generation
- Runtime migration of live servers
