# Requirements Traceability

This matrix connects the feature specification to implementation tasks and required evidence. Exact test file names may change during planning, but the evidence category must remain.

| Scope | Requirements | Tasks | Required evidence |
|---|---|---|---|
| CLI contract | FR-001–FR-005 | T006, T016–T018, T026 | CLI unit/integration tests; JSON schema validation; exit-code tests |
| Manifest | FR-006–FR-010 | T007–T015 | valid/invalid fixtures; property tests; exported-schema parity |
| Minimal FastMCP generation | FR-011–FR-019 | T019–T028 | golden tree; generated lint/type/test; MCP initialize/list/call smoke test |
| Safe regeneration | FR-020–FR-025 | T029–T040 | conflict fixtures; rollback/fault tests; deterministic clean-tree comparison |
| Adapter architecture | FR-026–FR-030 | T019, T020, T044 | architecture tests/review; second-adapter spike before v1 stability claim |
| Security and quality | FR-031–FR-036 | T008, T009, T014, T035–T040, T061–T066 | abuse tests; cross-platform CI; coverage report; supply-chain artifacts |
| First-run usability | NFR-001, SC-001, SC-002 | T041–T047 | observed pilot sessions and timing data |
| Performance | NFR-002 | T024, T033, T040 | generation benchmark excluding install/build operations |
| Diagnostic quality | NFR-003, US4 | T056–T060 | healthy/error fixtures; human review; JSON contract validation |
| Generated code quality | NFR-004, SC-003 | T023, T027, T048–T055 | every reference profile runs its generated CI checks |
| Offline generation | NFR-005 | T021–T024, T056 | network-disabled generation/doctor test |
| Contract versioning | NFR-006 | T012, T058, T067 | committed schemas and release migration notes |
| No silent overwrite | SC-004 | T029–T040 | explicit preservation/conflict tests |
| Second-target feasibility | SC-005 | T019, T044 | disposable TypeScript or low-level Python adapter spike after v0.1 |
| Executable documentation | SC-006 | T041, T042 | documentation command tests |

## User story release gates

### US1 — Runnable local server

Cannot pass until an isolated generated project starts and completes a real MCP tool call.

### US2 — Safe regeneration

Cannot pass until modified scaffold files are preserved, managed conflicts block all writes, and interrupted apply is recoverable.

### US3 — Streamable HTTP

Cannot pass until the generated container performs an MCP smoke call over HTTP with conservative exposure defaults.

### US4 — Doctor

Cannot pass until text and JSON outputs report identical diagnostic semantics and JSON validates against the public schema.
