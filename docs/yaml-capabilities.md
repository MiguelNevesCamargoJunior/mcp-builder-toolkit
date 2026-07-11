# YAML capabilities and boundaries

The v0.1 manifest configures a generated MCP server project. It is not a
workflow engine and is not the runtime catalog of tools.

## Supported declarations

```yaml
apiVersion: mcpbuilder.dev/v1alpha1
kind: MCPServerProject
metadata:
  name: customer-api-mcp
  version: 0.1.0
spec:
  target:
    runtime: fastmcp-python
    profile: fastmcp-python-2026.07
    protocolVersion: "2025-11-25"
  project:
    python: ">=3.12,<3.15"
    packageName: customer_api_mcp
  transport:
    type: streamable-http
    host: 127.0.0.1
    port: 8000
    path: /mcp
  features:
    tests: true
    lint: true
    typing: true
    docker: true
    compose: true
    githubActions: true
    structuredLogging: true
  scaffolds:
    exampleTool: true
```

This produces readable Python source, tests, project packaging, a local HTTP
entry point, container assets, CI, and local generation state. Generated source
does not depend on MCP Builder Toolkit at runtime.

## Connecting an API

Add the API client dependency to the generated `pyproject.toml`, store the
credential in an environment variable, and implement a typed Python tool in the
scaffold-once source tree:

```python
import os

import httpx


def get_customer(customer_id: str) -> dict[str, object]:
    """Fetch one customer from the configured API."""
    response = httpx.get(
        f"https://api.example.com/customers/{customer_id}",
        headers={"Authorization": f"Bearer {os.environ['CUSTOMER_API_TOKEN']}"},
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()
```

Register it with the generated FastMCP server using `mcp.tool(get_customer)`.
The builder preserves these scaffold-once edits during regeneration.

Never put real API tokens in the manifest, generated source, `.env.example`, or
Git history.

## Not supported in v0.1

- declarative tool implementation in YAML;
- OpenAPI import or arbitrary API conversion;
- OAuth or authorization policy generation;
- gateways, hosted runtime, audit, budgets, A2A, or agent contracts;
- TypeScript, Go, Java, or C# targets.

These boundaries keep the alpha a transparent project generator rather than a
hidden production runtime.
