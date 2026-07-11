# Extending the builder

This guide covers **internal** extension points for v0.1. Third-party plugin
stability is **not** promised until a later release.

## Mental model

```text
Manifest → ProjectSpec → TargetAdapter + FeatureGenerators → ArtifactPlan → apply
```

- **Domain** (`domain/`) never imports FastMCP or other SDKs.
- **Adapters** map intent to templates for one runtime.
- **Features** add operational assets (Docker, CI) composably.

## Target adapters

Implement the protocol in `generation/interfaces.py`:

```python
class TargetAdapter(Protocol):
    id: str
    def validate(self, project: ProjectSpec) -> list[Diagnostic]: ...
    def plan(self, project: ProjectSpec) -> list[ArtifactSpec]: ...
    def compatibility_profile(self, project: ProjectSpec) -> CompatibilityProfile: ...
```

Checklist:

1. Create `src/mcp_builder/targets/<runtime>/adapter.py` + `templates/`.
2. Use `generation.renderer.make_env` with package-owned Jinja templates only.
3. Classify artifacts as `managed`, `scaffold-once`, or `derived`.
4. Register a `CompatibilityProfile` with tested dependency pins.
5. Wire into `service.build_planner()`.
6. Add golden + generated-project acceptance tests.

## Feature generators

```python
class FeatureGenerator(Protocol):
    id: str
    def supports(self, project: ProjectSpec) -> bool: ...
    def validate(self, project: ProjectSpec) -> list[Diagnostic]: ...
    def plan(self, project: ProjectSpec) -> list[ArtifactSpec]: ...
```

Checklist:

1. Gate on `project.features.*` (or transport) in `supports()`.
2. Validate feature dependencies (example: `compose` requires `docker`).
3. Emit only project-relative paths; never escape the project root.
4. Prefer managed ownership for files the builder owns long-term.

## Deferred seams (do not implement yet)

Namespaces reserved for later feature packs:

- `features.auth`, `features.telemetry`, `features.audit`
- `features.policy`, `features.budget`
- `adapters.a2a`, `contracts.agent`

Add a real second consumer before generalizing further abstractions.
