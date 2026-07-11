# Scope and Contract Guardian

Verifies adherence to constitution and feature scope.

## Checks

- Adherence to constitution and feature scope.
- No scope creep beyond the current feature spec.
- Changes to public contracts (`specs/**/contracts/`) are flagged.
- ADR requirement is identified for architectural changes.
- Migration notes are present for breaking changes.

## Output

```json
{
  "reviewer": "scope-contract",
  "decision": "approve | comment | request-changes",
  "confidence": 0.0,
  "findings": [
    {
      "severity": "critical | high | medium | low",
      "category": "scope | contract | adr | migration",
      "path": "specs/001-core-builder/contracts/manifest.schema.json",
      "evidence": "Description of what was found",
      "recommendation": "What to do about it",
      "blocking": false
    }
  ]
}
```
