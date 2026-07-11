# Quickstart: Expected v0.1 User Journey

This document defines the intended user experience. Commands are acceptance targets, not proof that implementation already exists.

## 1. Install

```bash
uv tool install mcp-builder-toolkit
mcp-builder --version
```

## 2. Initialize a project

```bash
mkdir customer-ops-mcp
cd customer-ops-mcp
mcp-builder init --name customer-ops-mcp --transport stdio --no-interactive
```

Expected output:

```text
Created mcp-builder.yaml
Next: mcp-builder validate && mcp-builder generate
```

## 3. Validate and preview

```bash
mcp-builder validate
mcp-builder generate --dry-run
```

Expected change plan includes a source package, example tool, tests, project metadata, README, CI, and local builder state.

## 4. Generate

```bash
mcp-builder generate
```

Expected tree:

```text
.
├── .github/workflows/ci.yml
├── .mcp-builder/state.json
├── .env.example
├── .gitignore
├── README.md
├── mcp-builder.yaml
├── pyproject.toml
├── src/customer_ops_mcp/
│   ├── __init__.py
│   ├── server.py
│   └── tools/
│       ├── __init__.py
│       └── example.py
└── tests/
    ├── test_example_tool.py
    └── test_server_smoke.py
```

## 5. Install and test generated project

```bash
uv sync
uv run ruff check .
uv run mypy src
uv run pytest
```

## 6. Run locally

The generated README contains the exact target-profile command. The expected stdio experience is equivalent to:

```bash
uv run python -m customer_ops_mcp.server
```

The server must also be testable through MCP Inspector or a supported MCP client.

## 7. Switch to Streamable HTTP

Edit the manifest:

```yaml
spec:
  transport:
    type: streamable-http
    host: 127.0.0.1
    port: 8000
    path: /mcp
  features:
    docker: true
    compose: true
```

Preview and apply:

```bash
mcp-builder generate --dry-run
mcp-builder generate
```

Then use the generated run command or:

```bash
docker compose up --build
```

## 8. Safe regeneration behavior

Modify `src/customer_ops_mcp/tools/example.py`, then regenerate. The tool file must be preserved because it is scaffold-once.

Modify a managed file such as `Dockerfile`, then change the generation profile. Dry-run must report a conflict. No overwrite occurs until the user explicitly targets that managed path:

```bash
mcp-builder generate --force-managed Dockerfile
```

## 9. Diagnose

```bash
mcp-builder doctor
mcp-builder doctor --format json
```

Doctor reports manifest health, compatibility, state, managed-file drift, expected generated assets, and local environment readiness without network access.
