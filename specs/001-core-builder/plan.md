# Implementation Plan: Core MCP Project Builder

**Feature:** `001-core-builder`  
**Plan version:** 0.1  
**Date:** 2026-07-10

## Technical context

- **Language:** Python 3.12+
- **CLI:** Typer + Rich
- **Domain/validation:** Pydantic v2
- **Manifest:** YAML via safe parser; JSON Schema exported from the domain model
- **Templates:** Jinja2 with strict undefined variables
- **First target:** FastMCP 3.x, compatibility-pinned by builder release profile
- **Packaging:** `pyproject.toml`, `uv`-friendly workflow, standard wheel/sdist
- **Testing:** pytest, pytest-cov, approval/golden tests, end-to-end generated-project tests
- **Quality:** Ruff, mypy, pre-commit optional
- **CI:** GitHub Actions across Linux/macOS/Windows
- **Release:** PyPI plus signed GitHub release artifacts in a later release hardening task

## Architecture goal

Separate the desired project model from target-specific code generation:

```text
manifest.yaml
    │
    ▼
parse + validate + normalize
    │
    ▼
protocol-independent ProjectSpec
    │
    ├── generation planner
    │      ├── target adapter: fastmcp-python
    │      ├── feature module: tests
    │      ├── feature module: docker
    │      ├── feature module: compose
    │      └── feature module: github-actions
    │
    ▼
ArtifactPlan
    │
    ├── create
    ├── update
    ├── preserve
    ├── conflict
    └── remove-managed
    │
    ▼
staged filesystem transaction + state update
```

The domain core does not know FastMCP APIs. The FastMCP adapter maps normalized project intent to templates and generated dependencies.

## Proposed source tree

```text
src/mcp_builder/
├── __init__.py
├── cli/
│   ├── app.py
│   ├── commands/
│   │   ├── init.py
│   │   ├── validate.py
│   │   ├── generate.py
│   │   └── doctor.py
│   ├── output.py
│   └── exit_codes.py
├── domain/
│   ├── project.py
│   ├── transport.py
│   ├── features.py
│   ├── artifacts.py
│   └── diagnostics.py
├── manifest/
│   ├── loader.py
│   ├── models.py
│   ├── normalize.py
│   └── schema.py
├── generation/
│   ├── planner.py
│   ├── renderer.py
│   ├── transaction.py
│   ├── ownership.py
│   ├── state.py
│   └── interfaces.py
├── targets/
│   └── fastmcp_python/
│       ├── adapter.py
│       ├── compatibility.py
│       └── templates/
├── features/
│   ├── tests/
│   ├── docker/
│   ├── compose/
│   └── github_actions/
└── resources/
    └── schemas/
```

## Bounded contexts

### Manifest context

Responsible for loading, schema validation, semantic validation, migration, and normalization. It produces `ProjectSpec`; it does not render files.

### Generation planning context

Combines a target adapter and selected feature modules into an ordered `ArtifactPlan`. It handles collisions and dependency relationships before touching disk.

### Filesystem state context

Tracks ownership, content hashes, builder version, profile, and prior artifacts. It classifies planned changes against current disk state.

### Target adapter context

Maps protocol-independent intent to a concrete SDK/project implementation. In v0.1, only `fastmcp-python` exists.

### Diagnostics context

Produces stable, structured diagnostics consumed by text and JSON renderers. Core logic never prints directly.

## Key interfaces

```python
class TargetAdapter(Protocol):
    id: str

    def validate(self, project: ProjectSpec) -> list[Diagnostic]: ...
    def plan(self, project: ProjectSpec) -> list[ArtifactSpec]: ...
    def compatibility_profile(self) -> CompatibilityProfile: ...


class FeatureGenerator(Protocol):
    id: str

    def supports(self, project: ProjectSpec) -> bool: ...
    def validate(self, project: ProjectSpec) -> list[Diagnostic]: ...
    def plan(self, project: ProjectSpec) -> list[ArtifactSpec]: ...
```

These are internal interfaces in v0.1. Backward compatibility for third-party plugins is not promised.

## Generated artifact ownership

| Class | Meaning | Regeneration behavior |
|---|---|---|
| `managed` | Operational file controlled by builder template | Update only when current file still matches previous generated hash; conflict otherwise |
| `scaffold-once` | User implementation starting point | Create if absent; preserve thereafter |
| `derived` | Machine-generated metadata/state | Recompute atomically; never hand-edit |

Candidate classifications:

- `src/<package>/server.py`: scaffold-once
- `src/<package>/tools/example.py`: scaffold-once
- `tests/test_example_tool.py`: scaffold-once
- `pyproject.toml`: managed initially, with a documented escape hatch if user takes ownership
- `Dockerfile`: managed
- `.github/workflows/ci.yml`: managed
- generated README sections: managed as a whole in v0.1; partial managed blocks deferred
- `.mcp-builder/state.json`: derived

## Filesystem transaction strategy

1. Parse and validate the manifest.
2. Build a complete in-memory `ArtifactPlan`.
3. Read prior state and current file hashes.
4. Classify every action.
5. Abort if unresolved conflicts exist.
6. Render into a temporary directory on the same filesystem.
7. Validate rendered artifacts and required paths.
8. Apply changes with atomic replacement where supported.
9. Write state last.
10. On failure, retain the original tree and emit a recovery diagnostic.

A cross-platform lock file prevents concurrent generation into the same project.

## Compatibility profile

The builder release owns a compatibility record, for example:

```yaml
profile: fastmcp-python-2026.07
protocol: "2025-11-25"
python: ">=3.12,<3.15"
fastmcp: ">=3.4.4,<3.5"
```

The manifest selects a target and protocol profile, not arbitrary untested dependency combinations. Advanced overrides may be added later with an explicit unsupported warning.

## Security design

### Threats in scope

- path traversal through manifest names or output paths;
- unsafe YAML tags or parser resource exhaustion;
- template injection or access to arbitrary template loaders;
- overwriting unrelated user files;
- symlink traversal during generation;
- credentials accidentally embedded in examples;
- generated HTTP server exposed broadly without clear user choice;
- compromised release artifact or dependency.

### Controls

- use safe YAML loading and reject custom tags;
- cap manifest file size and nested collection depth;
- normalize and validate all relative paths against project root;
- do not follow symlinks for managed writes unless explicitly supported and tested;
- use Jinja strict mode and package-owned templates only;
- stage all outputs before apply;
- never delete untracked files;
- conservative host defaults and security notes in generated HTTP README;
- dependency review, secret scanning, CodeQL where suitable, and release provenance roadmap.

## Testing strategy

### Unit tests

- manifest parsing and diagnostics;
- normalization and canonical hashing;
- path validation;
- compatibility profile selection;
- artifact planning;
- ownership classification;
- state migration;
- CLI output mapping.

### Golden tests

Reference manifests generate committed expected trees. Golden updates require explicit review and are grouped by target/profile.

### Property-based tests

Use Hypothesis selectively for path normalization, identifier validation, and deterministic canonicalization.

### End-to-end tests

For each reference profile:

1. generate into a temporary directory;
2. create/install an isolated environment;
3. run lint, type check, and tests;
4. start the server;
5. perform MCP initialize/list-tools/call-tool using a supported client;
6. for HTTP, build and start the container and repeat a smoke call.

### Cross-platform tests

Run generator and core tests on Linux, macOS, and Windows. Container smoke tests may remain Linux-only.

## Observability of the CLI

The CLI itself uses structured internal diagnostics but does not ship telemetry in v0.1. No usage data is collected. Verbose/debug logs are local and redact environment values that appear secret-like.

## Constitution check

| Principle | Plan compliance |
|---|---|
| DX first | Four commands, minimal manifest, generated quickstart |
| Standards aligned | Stable MCP profile; FastMCP adapter; no protocol additions |
| User ownership | No builder runtime dependency; scaffold-once source |
| Deterministic/safe | normalized hashes, dry-run, staging transaction, conflict detection |
| Protocol-independent core | `ProjectSpec` and adapter boundary |
| Secure defaults | safe YAML, path controls, conservative network defaults, CI hygiene |
| Contract-first testing | JSON schemas, CLI contract, E2E generated project tests |
| Evidence-based expansion | governance and multi-protocol work deferred |

No constitution exception is requested.

## Delivery slices

### Slice A — Minimal vertical builder

- manifest loader and schema;
- `init`, `validate`, `generate`;
- stdio FastMCP project;
- scaffold-once source;
- baseline tests and README.

This is the first publishable alpha.

### Slice B — Safe regeneration

- state file;
- artifact ownership;
- dry-run;
- conflict detection;
- transactional writes.

This is required before recommending repeated use.

### Slice C — HTTP and operational assets

- Streamable HTTP profile;
- Docker/Compose;
- GitHub Actions;
- generated project E2E tests.

### Slice D — Diagnostics and extensibility hardening

- `doctor`;
- JSON diagnostics;
- target/feature interfaces;
- compatibility profile reporting;
- contribution documentation.

## Deferred architecture seams

The following future capabilities receive interfaces or namespaces only; no implementation is included:

- `features.auth`
- `features.telemetry`
- `features.audit`
- `features.policy`
- `features.budget`
- `adapters.a2a`
- `contracts.agent`

A seam means the core can compose another feature generator or runtime middleware package later. It does not justify generalized abstractions before a concrete feature exists.
