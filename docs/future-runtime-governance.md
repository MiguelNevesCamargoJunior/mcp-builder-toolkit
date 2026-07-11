# Future Runtime Governance Design Note

**Status:** Non-v1 exploration. This document preserves architectural intent without adding requirements to `001-core-builder`.

## Motivation

Autonomous systems can create unbounded or cyclic execution through repeated tool calls, retries, agent delegation, MCP-to-agent callbacks, or agent-to-agent interactions. A token ceiling alone is insufficient because the MCP server may not observe model tokens and harmful loops can consume time, calls, network capacity, or side effects without large token usage.

## Proposed concept: Execution Budget

A future runtime package may enforce a multidimensional budget associated with a trace/run/task context:

```yaml
executionBudget:
  mode: observe
  limits:
    wallClockMs: 60000
    totalCalls: 12
    callsPerTool:
      search_docs: 5
      create_ticket: 1
    retries: 2
    delegationDepth: 4
    exactRepeats: 2
    nearDuplicateRepeats: 3
    tokens:
      maxInput: 20000
      maxOutput: 8000
      source: provider-reported
    cost:
      maxUsd: 0.50
      source: estimated
```

## Measurement truth levels

Every budget dimension should declare how it is known:

- `measured` — directly observed by the enforcement runtime;
- `provider-reported` — returned by a model/provider API;
- `estimated` — calculated from a tokenizer or pricing table;
- `unavailable` — cannot be observed reliably.

Enforcement must not pretend estimated tokens or costs are exact.

## Loop and repetition controls

Potential layers:

1. exact canonical hash of operation and arguments;
2. normalized argument comparison that ignores volatile fields;
3. semantic similarity for near-duplicate calls;
4. output-delta or progress signal to distinguish repeated work from useful iteration;
5. graph-cycle detection across agent/tool/delegation identifiers;
6. side-effect-aware hard limits for destructive operations.

Semantic similarity should not be a default hard blocker in the first implementation. It can create false positives and adds model/embedding cost. Start with exact repetition, calls, retries, time, and depth; collect evidence before novelty enforcement.

## Propagation

A future budget context needs explicit propagation across boundaries:

- MCP request metadata or an official extension/interceptor mechanism where standardized;
- HTTP trace context and signed/validated budget claims when crossing trust domains;
- A2A task metadata/extension when agent-to-agent adapters exist;
- local context variables inside a single runtime.

A receiving system must be allowed to tighten a budget but not silently expand an upstream hard limit.

## Enforcement outcomes

- `observe`: record usage only;
- `warn`: emit a diagnostic/event near threshold;
- `deny`: block the next operation;
- `require-approval`: pause for explicit authorization;
- `degrade`: switch to a cheaper/safer operation where application semantics define it.

## Relationship to the builder

The builder may later:

- install/configure a runtime budget middleware package;
- generate budget policy schema and tests;
- create local observability dashboards or receipts;
- validate that configured limits are enforceable by the selected target.

The builder core must not implement per-request counters itself because it is absent from runtime.

## Research questions

- Which MCP interceptor/extension mechanisms become stable?
- How should run/task identity propagate between clients, servers, and A2A agents?
- Which token/cost sources are reliable enough for enforcement?
- How can loop detection measure progress without requiring another expensive model call?
- How are distributed counters made consistent without turning the system into a centralized gateway?
- What receipt format supports audit without leaking tool arguments or sensitive output?
