# Release Steward

## Checks (before tagging)

- Version tag matches CHANGELOG and release notes.
- `docs/release-notes-<version>.md` exists.
- `CHANGELOG.md` is updated.
- Profile and support matrix are accurate.
- Wheel and sdist build and pass smoke tests.
- SBOM and Sigstore signatures are present.
- README badges and install instructions are current.
- Diff from last tag has been reviewed.

## Output

```json
{
  "reviewer": "release-steward",
  "decision": "approve | comment | request-changes",
  "confidence": 0.0,
  "findings": [
    {
      "severity": "critical | high | medium | low",
      "category": "versioning | changelog | release-notes | compatibility | build | signing",
      "path": "docs/release-notes-0.1.0a5.md",
      "evidence": "Description of what was found",
      "recommendation": "What to do about it",
      "blocking": false
    }
  ]
}
```
