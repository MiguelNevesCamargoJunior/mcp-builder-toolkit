# CLI Contract: `mcp-builder`

**Contract version:** 1alpha1

## General behavior

```text
mcp-builder [GLOBAL_OPTIONS] COMMAND [ARGS]
```

Global options:

- `--version`
- `--no-color`
- `--verbose`
- `--quiet`
- `--help`

Commands MUST NOT emit stack traces unless `--verbose` is enabled. Human output goes to stdout for successful results and stderr for errors. JSON mode emits one JSON document to stdout; operational errors still use the diagnostic schema.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | success; no blocking diagnostics |
| 1 | unexpected internal error |
| 2 | usage or manifest validation error |
| 3 | generation conflict; no changes applied |
| 4 | unsupported environment or compatibility profile |
| 5 | filesystem/transaction failure |
| 6 | doctor detected unhealthy project state |

## `init`

```text
mcp-builder init [DIRECTORY]
  [--name NAME]
  [--transport stdio|streamable-http]
  [--profile PROFILE]
  [--no-interactive]
```

Behavior:

- defaults to current directory;
- interactive mode asks only unresolved required choices;
- non-interactive mode requires enough flags or uses documented defaults;
- creates `mcp-builder.yaml` only;
- does not install dependencies or generate the project unless a future explicit `--generate` option is added;
- refuses to overwrite an existing manifest without explicit confirmation/flag.

## `validate`

```text
mcp-builder validate
  [-f|--file PATH]
  [--format text|json]
```

Behavior:

- performs syntax, schema, semantic, and compatibility validation;
- does not inspect generated files;
- default manifest path is `mcp-builder.yaml` in current directory.

## `generate`

```text
mcp-builder generate
  [-f|--file PATH]
  [-o|--output DIRECTORY]
  [--dry-run]
  [--format text|json]
  [--force-managed PATH ...]
```

Behavior:

- always validates before planning;
- `--dry-run` performs no writes and returns non-zero if blocking conflicts exist;
- `--force-managed` applies only to named managed paths;
- broad `--force` is intentionally absent from the first contract;
- interactive conflict resolution is not required in v0.1; explicit commands are safer;
- successful output summarizes created, updated, preserved, removed, and unchanged artifacts.

## `doctor`

```text
mcp-builder doctor [DIRECTORY]
  [-f|--file PATH]
  [--format text|json]
```

When `--file PATH` is supplied, the manifest's parent directory is the project
root used for state and drift checks.

Checks:

- manifest validity;
- supported builder/profile/protocol combination;
- Python executable compatibility;
- state-file readability and version;
- managed file drift;
- missing expected files;
- scaffold files are reported but never treated as drift;
- optional presence of Docker/uv commands when relevant;
- no network calls by default.

## Machine-readable result envelope

```json
{
  "command": "validate",
  "status": "error",
  "builderVersion": "0.1.0",
  "diagnostics": [
    {
      "code": "MBT-MANIFEST-004",
      "severity": "error",
      "message": "Unsupported transport type.",
      "path": "spec.transport.type",
      "hint": "Use 'stdio' or 'streamable-http'."
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 0,
    "info": 0
  }
}
```

## Stability policy

- Command names and exit-code meanings become stable at v1.0.
- Before v1.0, breaking changes require release notes and a migration entry.
- Diagnostic codes are stable once documented; message wording may improve without a major version.
- JSON output is versioned by the diagnostics schema `$id`.
