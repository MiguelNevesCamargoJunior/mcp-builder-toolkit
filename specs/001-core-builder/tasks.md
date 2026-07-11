# Tasks: Core MCP Project Builder

**Feature:** `001-core-builder`  
**MVP boundary:** Phases 1–5 produce a usable local builder with safe regeneration. HTTP/Docker and doctor follow in Phases 6–7.

## Phase 1 — Repository and quality foundation

- [x] T001 Create Python 3.12 package structure under `src/mcp_builder/` and test structure under `tests/`
- [x] T002 Configure `pyproject.toml` with Typer, Rich, Pydantic v2, safe YAML parser, Jinja2, pytest, Ruff, mypy, and coverage tooling
- [x] T003 [P] Configure Ruff, mypy, pytest, coverage thresholds, and pre-commit hooks
- [x] T004 [P] Add GitHub Actions test matrix for Linux, macOS, and Windows
- [x] T005 [P] Add Apache-2.0 license proposal, SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, and support policy
- [x] T006 Establish diagnostic code registry and exit-code constants from `contracts/cli-contract.md`

## Phase 2 — Manifest and domain foundation

- [x] T007 Implement Pydantic manifest models matching `contracts/manifest.schema.json`
- [x] T008 Implement safe YAML loading with file-size, custom-tag, and nesting controls
- [x] T009 Implement semantic validation for target/profile, transport combinations, feature dependencies, names, and paths
- [x] T010 Implement normalization into immutable `ProjectSpec`
- [x] T011 Implement canonical serialization and manifest SHA-256 hashing
- [x] T012 Export the runtime JSON Schema and verify it matches the committed public schema
- [x] T013 [P] Add unit tests for valid/invalid manifests and source-location diagnostics
- [x] T014 [P] Add property-based tests for project identifiers, package identifiers, and path normalization
- [x] T015 Implement compatibility-profile registry with the initial FastMCP/Python/MCP constraints

## Phase 3 — CLI vertical slice (User Story 1)

- [x] T016 Implement Typer application, global options, version command, output abstraction, and error boundary
- [x] T017 Implement `init` with minimal interactive and fully non-interactive paths
- [x] T018 Implement `validate` with text and JSON diagnostic renderers
- [x] T019 Implement internal `TargetAdapter` and `FeatureGenerator` interfaces
- [x] T020 Implement FastMCP Python adapter skeleton and package/project naming rules
- [x] T021 Implement strict Jinja renderer using package-owned templates only
- [x] T022 Implement generation planner and duplicate-destination validation
- [x] T023 Create FastMCP stdio templates for package, server, example tool, tests, pyproject, README, env example, and gitignore
- [x] T024 Implement `generate` for a clean directory without regeneration state
- [x] T025 [P] Add golden-tree test for minimal stdio manifest
- [x] T026 [P] Add CLI tests for help, init, validate, generate, JSON output, and exit codes
- [x] T027 Add generated-project test that installs dependencies and runs lint, type checks, and pytest in CI
- [x] T028 Add MCP smoke test using an official/supported client to initialize, list tools, and call the example tool

## Phase 4 — Safe regeneration foundation (User Story 2)

- [x] T029 Implement artifact ownership types: managed, scaffold-once, and derived
- [x] T030 Implement `.mcp-builder/state.json` model, serializer, versioning, and validation
- [x] T031 Implement current-file hashing and prior-state comparison
- [x] T032 Implement change classification: create, update, unchanged, preserve, conflict, remove-managed, orphan
- [x] T033 Implement `generate --dry-run` text and JSON change plans
- [x] T034 Implement explicit `--force-managed PATH` behavior
- [x] T035 Implement same-filesystem staging directory and transactional apply
- [x] T036 Implement cross-platform project generation lock
- [x] T037 Ensure state is written last and interrupted apply retains recoverable original files
- [x] T038 [P] Add tests proving scaffold-once files are never overwritten
- [x] T039 [P] Add tests for managed-file update, conflict, force-managed, removal, orphan, and rollback
- [x] T040 [P] Add deterministic generation test across two clean directories

## Phase 5 — MVP documentation and pilot readiness

- [x] T041 Generate profile-specific README commands and explain file ownership
- [x] T042 Add end-to-end quickstart test based on `quickstart.md`
- [x] T043 Add five example invalid manifests with expected diagnostics
- [x] T044 Add architecture and contribution guide for new target/feature modules
- [x] T045 Create pilot feedback form measuring completion, time-to-first-run, errors, and unclear concepts
- [x] T046 Publish path ready: release notes + release workflow + TestPyPI checklist (`docs/release-notes-0.1.0.md`) — actual token publish is maintainer-operated
- [x] T047 Pilot process ready: form + evidence log (`docs/pilot-feedback.md`, `docs/pilot-evidence.md`) — live pilot sessions are human-operated

## Phase 6 — Streamable HTTP and operational assets (User Story 3)

- [x] T048 Extend FastMCP adapter for the stable Streamable HTTP profile
- [x] T049 Implement conservative host/port/path defaults and exposure diagnostics
- [x] T050 Implement Docker feature generator with non-root runtime and reproducible dependency install
- [x] T051 Implement Compose feature generator with explicit port publishing
- [x] T052 Implement GitHub Actions feature generator matching selected lint/type/test options
- [x] T053 Add container build and HTTP MCP smoke test on Linux CI
- [x] T054 Add golden trees for HTTP, Docker, Compose, and CI feature combinations
- [x] T055 Validate unsupported feature/transport combinations before rendering

## Phase 7 — Doctor and machine diagnostics (User Story 4)

- [x] T056 Implement `doctor` manifest, profile, Python, state, expected-file, and drift checks
- [x] T057 Implement optional local executable checks for uv and Docker without network calls
- [x] T058 Validate JSON output against `contracts/diagnostics.schema.json`
- [x] T059 Add doctor fixtures for healthy, missing, drifted, incompatible, and corrupt-state projects
- [x] T060 Add remediation hints and documentation links for every doctor error code

## Phase 8 — Release hardening

- [x] T061 Add dependency review, secret scanning, and CodeQL/security analysis where applicable
- [x] T062 Add malicious manifest/path/symlink security tests
- [x] T063 Add template-origin and generated-artifact metadata to build state
- [x] T064 Add release SBOM and provenance generation (release workflow)
- [x] T065 Sign release artifacts using Sigstore (release workflow)
- [x] T066 Run OpenSSF Scorecard (security workflow)
- [x] T067 Freeze v1alpha1 manifest and diagnostics schemas for the alpha series
- [x] T068 Publish package notes + supported profile table + security/support scope (`docs/release-notes-0.1.0.md`, `SUPPORT.md`) — PyPI upload is maintainer-operated via release workflow

## Dependencies

- T007–T015 block generation work.
- T019–T023 block T024.
- T029–T037 block any claim of safe repeated generation.
- T048 depends on the stable FastMCP HTTP integration shape verified during implementation.
- T056 depends on build state and compatibility registry.

## Parallel work opportunities

- Quality/repository files (T003–T005) can proceed in parallel.
- Manifest tests and path properties (T013–T014) can proceed after models are sketched.
- Template creation, CLI shell, and schema work can proceed in separate branches once contracts are fixed.
- Docker, Compose, and GitHub Actions generators are independent after the feature interface stabilizes.

## Definition of done

The release is done only when every generated reference profile runs through its own generated test/lint/type workflow and at least one real MCP client smoke test. Snapshot equality alone is insufficient.

## Maintainer follow-ups (not blocked on engineering)

1. Configure GitHub secrets (`PYPI_TOKEN`, TestPyPI) and cut `v0.1.0a1`.
2. Run ≥3 live pilot sessions; fill `docs/pilot-evidence.md`.
3. Review Scorecard/CodeQL findings on the default branch after first CI green run.
