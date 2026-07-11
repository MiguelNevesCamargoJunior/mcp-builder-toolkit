# Threat Model: Builder v0.1

## Scope

This threat model covers the local builder CLI, its manifests/templates, generated project tree, and release supply chain. It does not claim to secure arbitrary tools implemented by users or autonomous agents invoking those tools.

## Assets

- developer source code and uncommitted work;
- project filesystem integrity;
- manifest and generation state integrity;
- builder release artifacts and embedded templates;
- generated dependency and CI configuration;
- credentials present in the developer environment;
- trust in generated server defaults.

## Trust boundaries

```text
untrusted manifest / CLI arguments
              │
              ▼
      parser and validation
              │
              ▼
 package-owned templates ── builder release supply chain
              │
              ▼
       generation planner
              │
              ▼
 developer filesystem / Git repository
              │
              ▼
 package registries, Docker, CI, MCP runtime
```

## Threats and required controls

### T1 — Path traversal and arbitrary overwrite

An attacker or malformed manifest supplies `../`, absolute paths, reserved names, symlink targets, or Unicode-confusable paths to write outside the project.

Controls:

- canonicalize every destination relative to a fixed project root;
- reject absolute paths, traversal segments, device paths, and unsupported reserved names;
- inspect parent path components for symlinks before writing;
- never delete or overwrite untracked files;
- stage changes and compare the final plan before apply;
- test Windows and POSIX path behavior.

### T2 — Destructive regeneration

The builder overwrites source or configuration modified by the user.

Controls:

- artifact ownership classes;
- previous generated hashes;
- dry-run as a first-class command;
- conflicts block all writes by default;
- force is path-scoped;
- state is written after successful apply;
- rollback/recovery tests.

### T3 — Unsafe YAML or parser denial of service

Custom YAML tags instantiate objects, aliases expand excessively, or deeply nested input consumes resources.

Controls:

- safe loader only;
- reject custom tags;
- limit manifest size and nesting/alias expansion where parser permits;
- do not interpolate environment variables implicitly;
- redact manifest snippets that may contain secret-like values in diagnostics.

### T4 — Template injection or arbitrary code execution

Manifest values influence template paths, filters, or expressions beyond ordinary string rendering.

Controls:

- templates are package-owned and selected by internal identifiers;
- strict Jinja environment with a minimal filter set;
- no dynamic import or evaluation from manifest values;
- validate generated Python/module identifiers before rendering;
- no shell command execution during plain generation.

### T5 — Secret exposure

Generated examples, diagnostic output, debug logs, or committed manifests expose credentials.

Controls:

- examples use placeholders that do not resemble real secrets;
- no automatic environment dump;
- debug logs redact common secret key names and token patterns;
- `.env` is ignored; only `.env.example` is generated;
- CI includes secret scanning.

### T6 — Insecure HTTP exposure

Generated Streamable HTTP servers bind to all interfaces or lack warnings about authentication and network exposure.

Controls:

- local default host is `127.0.0.1`;
- container bind behavior is explained separately from published host ports;
- generated README states that remote exposure requires authentication, TLS termination, and deployment review;
- no “secure” or “production-ready” claim based solely on scaffold output.

### T7 — Dependency and release compromise

A compromised builder, template, Python dependency, container base, or CI action affects generated projects.

Controls:

- constrained and tested compatibility profiles;
- dependency review and automated update tooling;
- pinned GitHub Actions by immutable reference where practical;
- SBOM and SLSA provenance for releases;
- Sigstore signing roadmap;
- OpenSSF Scorecard review;
- private vulnerability disclosure process.

### T8 — Concurrent or interrupted generation

Two processes or a failure mid-write leave inconsistent files/state.

Controls:

- project-scoped lock;
- same-filesystem staging;
- per-file atomic replacement where supported;
- state written last;
- best-effort rollback and fault-injection tests at each apply phase.

### T9 — False confidence in generated tool safety

Users assume project structure secures tool behavior, authorization, data access, or model use.

Controls:

- explicit security scope in README;
- generated example is read-only and low-risk;
- later auth/policy/audit packs remain explicit opt-ins;
- tool-specific threat modeling remains the application owner’s responsibility.

## Abuse tests required before v0.1

- traversal strings in all path/name fields;
- symlink parent and destination cases;
- very large and deeply nested YAML;
- malicious YAML tags and alias expansion;
- conflict and rollback fault injection;
- secret-like environment values in verbose mode;
- HTTP default binding assertion;
- tampered or incompatible build-state files;
- concurrent generator processes.

## Residual risk

The builder can reduce project-assembly mistakes but cannot guarantee the security of generated tools, upstream runtimes, deployment environments, or agent decisions. Security claims must remain scoped to specific tested controls.
