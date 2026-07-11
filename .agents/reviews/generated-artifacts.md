# Generated Artifact Reviewer

## Checks

- Template changes update golden trees.
- Artifact ownership (managed / scaffold-once / derived) is correct.
- Output is deterministic.
- Profile compatibility is maintained.
- Generated CI and documentation match the profile.
- No runtime dependency on the builder in generated projects.

## Output

```json
{
  "reviewer": "generated-artifacts",
  "decision": "approve | comment | request-changes",
  "confidence": 0.0,
  "findings": [
    {
      "severity": "critical | high | medium | low",
      "category": "golden-tree | ownership | determinism | profile | compatibility",
      "path": "src/mcp_builder/targets/fastmcp_python/templates/server.py.j2",
      "evidence": "Description of what was found",
      "recommendation": "What to do about it",
      "blocking": false
    }
  ]
}
```
