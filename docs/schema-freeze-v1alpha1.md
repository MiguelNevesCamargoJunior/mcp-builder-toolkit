# Schema freeze: v1alpha1 (alpha series)

**Frozen:** 2026-07-10  
**Applies to:**

- `specs/001-core-builder/contracts/manifest.schema.json`  
  `$id`: `https://mcpbuilder.dev/schemas/manifest/v1alpha1.json`
- `specs/001-core-builder/contracts/diagnostics.schema.json`  
  `$id`: `https://mcpbuilder.dev/schemas/diagnostics/v1alpha1.json`
- CLI contract: `contracts/cli-contract.md` (1alpha1)

## Compatibility rules during alpha

1. **Additive optional fields** may be introduced with defaults if ignored by older builders.
2. **Removing or renaming fields**, changing enums, or tightening required sets requires a new API version (for example `v1alpha2` or `v1beta1`) and release notes.
3. Diagnostic **codes** once documented remain stable; message text may improve.
4. Exit code meanings remain stable for the alpha series.

## Runtime export

Pydantic models may export a richer JSON Schema (extra `$defs`). The committed
public schema under `contracts/` is the **normative** alpha contract for external tools.
