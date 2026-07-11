# Pilot feedback form (v0.1 alpha)

Use this form after a pilot session. Aggregate results map to success criteria
**SC-001** (completion without maintainer help) and **SC-002** (time to first run).

## Session metadata

| Field | Value |
|-------|-------|
| Date | |
| Pilot ID | |
| Participant role (app / platform / other) | |
| OS | |
| Python version | |
| Builder version (`mcp-builder --version`) | |

## Completion checklist

| Step | Completed? (Y/N) | Minutes | Notes / errors |
|------|------------------|---------|----------------|
| Install builder | | | |
| `mcp-builder init` | | | |
| `mcp-builder validate` | | | |
| `mcp-builder generate` | | | |
| `uv sync` in generated project | | | |
| Generated tests pass | | | |
| Server starts / client connects | | | |

**Total wall time empty dir → successful server start (exclude dependency download):** ___ minutes

**Maintainer intervention required?** Y/N — if Y, what blocked the pilot?

## Concepts clarity (1 = unclear, 5 = clear)

| Concept | Score | Comment |
|---------|-------|---------|
| Manifest vs generated code | | |
| managed vs scaffold-once ownership | | |
| Compatibility profile | | |
| Dry-run / conflict resolution | | |
| stdio vs Streamable HTTP | | |

## Free-form

1. What was the first confusing moment?
2. What error message (if any) was unhelpful?
3. What would you delete from the generated project?
4. Would you use this again for a real internal server? Why / why not?

## Evidence log

Attach or link:

- `mcp-builder doctor --format json` output
- Terminal transcript of the happy path
- Any conflict diagnostics from regenerate

## Scoring for SC-001 / SC-002

| Metric | Result |
|--------|--------|
| Completed init→generate→test→run without help | Y/N |
| Time excluding downloads (minutes) | |
