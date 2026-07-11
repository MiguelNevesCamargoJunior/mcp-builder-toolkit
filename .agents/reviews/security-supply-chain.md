# Security and Supply Chain Reviewer

## Checks

- Path safety and symlink handling.
- YAML parsing and serialization safety.
- HTTP host/port/path validation.
- New runtime dependencies are justified.
- Workflow permissions follow least privilege.
- All actions pinned by commit hash.
- No secrets or sensitive data in output.
- Threat model updated if applicable.

## Output

```json
{
  "reviewer": "security-supply-chain",
  "decision": "approve | comment | request-changes",
  "confidence": 0.0,
  "findings": [
    {
      "severity": "critical | high | medium | low",
      "category": "path-safety | yaml | http | dependency | permissions | secrets | threat-model",
      "path": "src/mcp_builder/generation/lock.py",
      "evidence": "Description of what was found",
      "recommendation": "What to do about it",
      "blocking": false
    }
  ]
}
```
