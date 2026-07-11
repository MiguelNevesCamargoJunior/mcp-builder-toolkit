# Data Model: Core MCP Project Builder

The domain model represents desired project shape and generation state. It intentionally excludes runtime agent governance in v0.1.

## Aggregate: ProjectSpec

Normalized, immutable input to generation.

| Field | Type | Description |
|---|---|---|
| `api_version` | string | Builder manifest schema version, e.g. `mcpbuilder.dev/v1alpha1` |
| `kind` | enum | `MCPServerProject` |
| `metadata` | `ProjectMetadata` | Identity and human-facing metadata |
| `target` | `TargetSpec` | Generation runtime target and compatibility profile |
| `transport` | `TransportSpec` | stdio or Streamable HTTP settings |
| `project` | `PythonProjectSpec` | Package/layout/runtime choices |
| `features` | `FeatureSelection` | Optional generated operational assets |
| `scaffolds` | `ScaffoldSelection` | Initial user-owned examples/stubs |

### Invariants

- `metadata.name` is a DNS-label-like project identifier.
- `project.package_name` is a valid Python import identifier.
- target `fastmcp-python` requires a supported Python and FastMCP compatibility profile.
- stdio transport cannot define HTTP host/port/path.
- Streamable HTTP path starts with `/` and contains no traversal segments.
- all manifest paths are project-relative and normalized.

## Entity: ProjectMetadata

| Field | Required | Rules |
|---|---:|---|
| `name` | yes | lowercase letters, digits, hyphens; 1–63 chars |
| `display_name` | no | human-readable, 1–100 chars |
| `description` | no | plain text, max 500 chars |
| `version` | yes | semantic version; default `0.1.0` |
| `license` | no | SPDX identifier; recommended `Apache-2.0` |

## Value object: TargetSpec

| Field | Type | Example |
|---|---|---|
| `runtime` | enum | `fastmcp-python` |
| `profile` | string | `fastmcp-python-2026.07` |
| `protocol_version` | date-version string | `2025-11-25` |

A compatibility registry resolves profile to tested dependency constraints.

## Value object: TransportSpec

Discriminated union.

### StdioTransport

```yaml
type: stdio
```

### StreamableHttpTransport

```yaml
type: streamable-http
host: 127.0.0.1
port: 8000
path: /mcp
```

Host defaults remain local for direct developer execution. A container profile may override the container bind address while publishing only explicitly configured ports.

## Value object: PythonProjectSpec

| Field | Type | Default |
|---|---|---|
| `python` | version constraint | `>=3.12,<3.15` |
| `package_name` | Python identifier | derived from metadata name |
| `layout` | enum | `src` |
| `dependency_manager` | enum | `uv` |
| `readme` | boolean | true |

Only `src` and `uv` are supported by the first profile; they remain explicit to avoid future schema breaks.

## Value object: FeatureSelection

```yaml
features:
  tests: true
  lint: true
  typing: true
  docker: false
  compose: false
  githubActions: true
  structuredLogging: true
```

Feature validation can express dependencies:

- `compose` requires `docker`.
- `githubActions` always includes generated test/lint/type steps selected by the profile.
- features unsupported by the target produce validation errors, not silent omissions.

## Value object: ScaffoldSelection

```yaml
scaffolds:
  exampleTool: true
```

Scaffolds create user-owned source once. They are not regenerated after modification.

Future forms may include `toolStubs`, `resourceStubs`, or `promptStubs`; they are excluded from the v1 schema until semantics are proven.

## Aggregate: ArtifactPlan

A complete proposed filesystem change set.

| Field | Type | Description |
|---|---|---|
| `project_root` | path | canonical target root |
| `manifest_hash` | SHA-256 | hash of normalized project spec |
| `builder_version` | semver | generator version |
| `profile` | string | compatibility profile |
| `artifacts` | list[`ArtifactSpec`] | desired files/directories |
| `diagnostics` | list[`Diagnostic`] | warnings/errors before apply |

## Entity: ArtifactSpec

| Field | Type | Description |
|---|---|---|
| `relative_path` | safe relative path | destination |
| `content` | bytes/text | fully rendered output |
| `content_hash` | SHA-256 | desired content hash |
| `ownership` | enum | `managed`, `scaffold-once`, `derived` |
| `origin` | string | adapter/feature/template identifier |
| `mode` | optional integer | executable/regular mode where portable |

### Invariants

- path remains inside project root after normalization;
- no duplicate destinations across generators;
- a directory cannot also be emitted as a file;
- template origin is package-owned in v0.1;
- secret-like values are not permitted in standard templates.

## Aggregate: BuildState

Stored at `.mcp-builder/state.json`.

```json
{
  "stateVersion": "1",
  "builderVersion": "0.1.0",
  "profile": "fastmcp-python-2026.07",
  "protocolVersion": "2025-11-25",
  "manifestHash": "sha256:...",
  "artifacts": {
    "Dockerfile": {
      "ownership": "managed",
      "generatedHash": "sha256:...",
      "origin": "feature.docker/Dockerfile.j2"
    }
  }
}
```

Build state is local project metadata. It contains no credentials and no telemetry identifiers.

## Entity: PlannedChange

| Status | Meaning |
|---|---|
| `create` | desired file absent |
| `update` | managed file equals prior generated hash and desired content changed |
| `unchanged` | current and desired hashes match |
| `preserve` | scaffold-once file exists |
| `conflict` | managed file was modified and desired output differs |
| `remove-managed` | previously managed file no longer desired and still unmodified |
| `orphan` | previously managed file no longer desired but modified; preserve and warn |

## Entity: Diagnostic

| Field | Type | Description |
|---|---|---|
| `code` | stable string | e.g. `MBT-MANIFEST-001` |
| `severity` | enum | `info`, `warning`, `error` |
| `message` | string | concise user-facing message |
| `path` | optional string | manifest field or file path |
| `line`/`column` | optional integer | source location where available |
| `hint` | optional string | actionable correction |
| `details` | optional object | machine-readable context without secrets |

## Future domain boundaries—not part of v0.1

Future feature packs may introduce separate aggregates rather than expanding `ProjectSpec` indiscriminately:

- `RuntimeControlSpec` — auth, policy, approvals, egress;
- `ExecutionBudgetSpec` — calls, time, depth, repetition, tokens/cost where observable;
- `AuditReceiptSpec` — event schemas and sinks;
- `AgentContractSpec` — obligations and measurable runtime constraints;
- `A2AAdapterSpec` — Agent Card and agent-to-agent endpoint generation.

They should be versioned independently and composed through extensions.
