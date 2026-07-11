# Feature Specification: Core MCP Project Builder

**Feature branch:** `001-core-builder`  
**Status:** Draft for implementation planning  
**Created:** 2026-07-10  
**Target release:** v0.1.0

## Summary

Build the first usable release of MCP Builder Toolkit: a command-line tool that creates, validates, previews, and generates a conventional Python MCP server project from a small declarative manifest.

The release is optimized for adoption. It generates transparent source code, tests, packaging, local execution instructions, optional HTTP deployment assets, and CI. It does not introduce runtime governance, agent contracts, budgets, or multi-protocol behavior.

## Problem statement

Creating a small MCP server is easy. Creating one with a coherent project layout, reproducible dependencies, testing, container packaging, CI, error handling, documentation, and safe update behavior requires repeated manual decisions.

Existing SDKs and frameworks correctly focus on protocol implementation and runtime capabilities. Static templates help with one initial copy, but they do not provide a durable, manifest-driven workflow for validating desired project shape, previewing changes, or evolving generated operational assets safely.

## Target users

### Primary user

A Python developer who understands APIs and basic MCP concepts and wants a maintainable server scaffold without researching every project-level decision.

### Secondary user

A platform or enablement engineer who wants to publish an internal golden path for MCP servers while retaining readable, user-owned code.

### Non-target users for v0.1

- teams seeking a centralized MCP gateway;
- teams requiring complete enterprise identity integration;
- users seeking an agent framework;
- users seeking automatic conversion of arbitrary APIs into high-quality MCP tools;
- users seeking A2A orchestration.

## Clarifications and resolved assumptions

1. The first target is Python using FastMCP 3.x.
2. The CLI executable is `mcp-builder`; repository/package naming remains `mcp-builder-toolkit`.
3. The stable MCP protocol profile is `2025-11-25`; draft features are excluded.
4. The manifest describes project generation intent, not the authoritative runtime catalog of all tools.
5. Tool source code and Python type hints remain the source of truth for runtime schemas.
6. Generated user source is scaffold-once; managed operational files use hash-aware regeneration.
7. Generation works offline once the builder package and templates are installed. Dependency installation is a separate optional action.
8. Authentication, telemetry, audit, budgets, policy, A2A, and contracts are explicitly deferred.

## User scenarios and acceptance

### User Story 1 — Generate a runnable local MCP server (Priority: P1)

As a Python developer, I can initialize a project and generate a runnable stdio MCP server so that I can begin implementing tools without assembling boilerplate.

**Independent test:** on a clean machine with supported Python and the builder installed, create a project, generate it, install dependencies, run tests, and connect with an MCP inspector/client.

**Acceptance scenarios**

1. **Given** an empty directory, **when** the user runs `mcp-builder init`, **then** the CLI creates a valid minimal manifest with a project name, Python target, stdio transport, and baseline generation features.
2. **Given** a valid manifest, **when** the user runs `mcp-builder generate`, **then** the CLI creates a Python `src` project containing a FastMCP server, one example tool, tests, configuration, and a generated README.
3. **Given** the generated project and installed dependencies, **when** the user runs the documented test command, **then** all generated tests pass.
4. **Given** the generated project, **when** the user runs the documented local command, **then** the MCP server starts successfully over stdio.
5. **Given** an invalid project name or unsupported manifest value, **when** validation occurs, **then** the CLI returns actionable diagnostics and does not write partial output.

### User Story 2 — Preview and safely regenerate project assets (Priority: P1)

As a developer maintaining a generated project, I can preview changes and regenerate managed files without losing my implementation code.

**Independent test:** generate a project, modify a user-owned tool and a managed file, change the manifest, run dry-run, and verify conflict behavior.

**Acceptance scenarios**

1. **Given** an existing generated project, **when** `generate --dry-run` is executed, **then** the CLI lists files that would be created, updated, preserved, conflicted, or removed without modifying disk.
2. **Given** a user-owned source file changed after generation, **when** generation runs again, **then** the file is preserved.
3. **Given** a managed file changed by the user and also changed by the new template, **when** generation runs without an explicit override, **then** generation fails with a conflict diagnostic and leaves the file unchanged.
4. **Given** an unchanged managed file, **when** its template output changes, **then** the file is safely updated.
5. **Given** the same normalized manifest and builder version, **when** generation runs twice from a clean directory, **then** the resulting file contents are identical.

### User Story 3 — Generate a deployable Streamable HTTP profile (Priority: P2)

As a developer, I can select Streamable HTTP and Docker assets so that the generated server can be exercised as a remote MCP server.

**Independent test:** generate the HTTP profile, build the container, start it locally, and perform an MCP initialization/tool call through an official or supported client.

**Acceptance scenarios**

1. **Given** `transport.type: streamable-http`, **when** the project is generated, **then** the server exposes the configured MCP path using the target adapter’s supported HTTP runtime.
2. **Given** Docker generation enabled, **when** the container image is built, **then** it starts the generated server with a non-root runtime user where supported.
3. **Given** no explicit host configuration, **when** local HTTP mode is generated, **then** the least exposed useful binding is selected and documented.
4. **Given** CI generation enabled, **when** the generated GitHub Actions workflow runs, **then** lint, type-check, unit tests, and a build smoke test execute.
5. **Given** an unsupported combination of transport and target options, **when** validation runs, **then** generation is blocked with an explanation.

### User Story 4 — Diagnose environment and project health (Priority: P2)

As a developer, I can run a diagnostic command so that common setup and drift problems are identified before debugging the server manually.

**Independent test:** run `doctor` against valid, incomplete, and drifted generated projects and verify machine-readable and human-readable diagnostics.

**Acceptance scenarios**

1. **Given** a generated project, **when** `mcp-builder doctor` runs, **then** it checks manifest validity, builder state, expected files, supported Python version, and known dependency/profile constraints.
2. **Given** a modified or missing managed file, **when** doctor runs, **then** it reports the drift without modifying the project.
3. **Given** `--format json`, **when** validation or doctor runs, **then** diagnostics conform to the public diagnostic schema.
4. **Given** no problems, **when** doctor completes, **then** it returns exit code 0 and a concise health summary.

## Edge cases

- Target directory exists and is non-empty.
- Manifest file is syntactically valid YAML but semantically invalid.
- YAML anchors or unsupported custom tags are present.
- Package name differs from display name.
- Windows path behavior differs from POSIX paths.
- Project generation is interrupted midway.
- Two concurrent generation processes target the same directory.
- A file previously managed by the builder is removed from a newer generation profile.
- The builder version is older than the project’s recorded generation version.
- The manifest requests a FastMCP profile not supported by the installed builder.
- The generated server’s dependency installation requires network access, but generation itself does not.

## Functional requirements

### CLI and workflow

- **FR-001:** The system MUST provide `init`, `validate`, `generate`, and `doctor` commands.
- **FR-002:** Every command MUST support `--help` with examples for its common path.
- **FR-003:** `validate` and `doctor` MUST support human-readable and JSON output.
- **FR-004:** Commands MUST use stable documented exit codes.
- **FR-005:** Non-interactive operation MUST be possible for CI and automation.

### Manifest

- **FR-006:** The system MUST accept a versioned YAML manifest validated against a published JSON Schema.
- **FR-007:** The manifest MUST identify API version, kind, project metadata, generation target, protocol profile, Python profile, transport, and generated features.
- **FR-008:** Unknown top-level fields MUST fail validation by default for v1 schemas.
- **FR-009:** Toolkit-specific fields MUST not be represented as MCP protocol fields.
- **FR-010:** Manifest normalization MUST produce a canonical internal representation used for hashing and generation.

### Generation

- **FR-011:** The first generation target MUST be FastMCP Python.
- **FR-012:** The generator MUST support stdio and Streamable HTTP project profiles.
- **FR-013:** Generated projects MUST use a `src` layout and include a runnable server entry point.
- **FR-014:** Generated projects MUST include at least one example tool that is clearly marked for replacement.
- **FR-015:** Generated projects MUST include unit tests and one server smoke test.
- **FR-016:** Generated projects MUST include `pyproject.toml`, `.gitignore`, `.env.example`, README, and development commands.
- **FR-017:** Dockerfile, Compose, and GitHub Actions MUST be independently selectable generation features.
- **FR-018:** Generation MUST be deterministic for the same normalized inputs and builder profile.
- **FR-019:** Generation MUST execute through a staging directory and commit changes only after validation succeeds.

### File ownership and regeneration

- **FR-020:** Generated artifacts MUST be classified as `managed`, `scaffold-once`, or `derived`.
- **FR-021:** User modifications to scaffold-once files MUST be preserved by default.
- **FR-022:** Managed file conflicts MUST not be overwritten without explicit user action.
- **FR-023:** The builder MUST store local generation state containing builder version, manifest hash, generation profile, artifact ownership, and content hashes.
- **FR-024:** `--dry-run` MUST show a complete change plan without writes.
- **FR-025:** `--force` MUST be scoped and explicit; it MUST NOT imply deletion of arbitrary untracked files.

### Architecture and extensibility

- **FR-026:** The internal domain model MUST not import FastMCP runtime classes.
- **FR-027:** Target-specific generation MUST implement a documented adapter interface.
- **FR-028:** Feature generators such as Docker and CI MUST be composable modules rather than embedded directly in the target adapter.
- **FR-029:** The extension mechanism MUST be internal-only in v0.1; third-party plugin stability is not promised.
- **FR-030:** The generated project MUST not require `mcp-builder-toolkit` at runtime.

### Security and quality

- **FR-031:** YAML MUST be parsed using safe loading and size/depth limits where supported.
- **FR-032:** Generated files MUST not contain real credentials or secret-like sample values.
- **FR-033:** HTTP profiles MUST document exposure risks and use conservative defaults.
- **FR-034:** The builder MUST reject path traversal in names, output paths, template paths, and manifest-provided module paths.
- **FR-035:** Release CI MUST test generation on Linux, macOS, and Windows.
- **FR-036:** The builder core MUST maintain at least 90% line coverage, with branch coverage reported.

## Non-functional requirements

- **NFR-001:** A first-time user familiar with Python SHOULD reach a successful generated test run within 10 minutes, excluding dependency download time.
- **NFR-002:** A typical generation run SHOULD complete in under two seconds excluding dependency installation and container builds.
- **NFR-003:** Error messages MUST identify the failing field/file, reason, and likely correction.
- **NFR-004:** Generated code MUST follow standard Python conventions and pass generated lint/type checks without manual changes.
- **NFR-005:** The builder MUST operate without network access after installation.
- **NFR-006:** Public JSON schemas and CLI contracts MUST use semantic versioning independent of the MCP protocol date version.

## Success criteria

- **SC-001:** At least 80% of five external pilot users complete `init → generate → test → run` without maintainer intervention.
- **SC-002:** Median time from empty directory to successful server start is below 10 minutes excluding dependency download time.
- **SC-003:** 100% of generated reference profiles pass their own generated CI in the release pipeline.
- **SC-004:** Re-running generation never silently overwrites a modified scaffold-once file in test scenarios.
- **SC-005:** The core builder can add a second target adapter in a spike without changes to manifest parsing or generation orchestration APIs.
- **SC-006:** Public README examples remain executable through automated documentation tests.

## Explicit non-goals for this feature

- runtime token or cost accounting;
- loop detection and execution budgets;
- auth providers, OAuth proxying, or authorization policy;
- OpenTelemetry setup beyond a future extension seam;
- audit receipts;
- MCP gateway or registry management;
- automatic quality evaluation of tool descriptions;
- generation from OpenAPI or arbitrary source repositories;
- TypeScript, Java, C#, or Go targets;
- A2A Agent Cards or task handling;
- agent contract standards;
- hosted SaaS or control plane.

## Dependencies and assumptions

- FastMCP 3.x remains a viable and maintained Python target.
- MCP `2025-11-25` remains the selected stable protocol profile during v0.1 implementation.
- The generated project can rely on FastMCP for protocol correctness while the builder validates project-level intent and compatibility.
- Docker and GitHub Actions are optional outputs, not required runtime platforms.

## Open decisions before implementation freeze

1. Final public license: Apache-2.0 recommended.
2. Canonical Python package import name: `mcp_builder` recommended.
3. Template rendering library: Jinja2 recommended.
4. Whether `doctor` enters v0.1 or v0.2 if schedule pressure emerges.
5. Whether the example tool is `echo`, `health`, or a more realistic read-only example.
