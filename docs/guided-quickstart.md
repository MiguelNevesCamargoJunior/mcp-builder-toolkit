# Guided Quickstart: Build a Working MCP Server

This walkthrough takes you from an empty directory to a **functional Python MCP server** you can call with a real client. You will:

1. Install the builder  
2. Generate a project  
3. Replace the sample tools with a small but useful toolset  
4. Test and run the server  
5. Connect with FastMCP’s client (and optionally Claude Desktop / MCP Inspector)  
6. Optionally switch to Streamable HTTP  

**Time:** about 15–20 minutes (plus dependency download).  
**Requirements:** Python 3.12 or 3.13, [uv](https://docs.astral.sh/uv/), and a clone of this repository (alpha install path).

---

## What you will build

A local MCP server named **task-notes-mcp** that exposes three tools:

| Tool | Purpose |
|------|---------|
| `health` | Report that the server is up |
| `add_note` | Store a short note in memory |
| `list_notes` | List notes (optionally filter by tag) |

This is enough to prove the full path: **generate → implement → test → call over MCP**.

---

## Step 0 — Prerequisites

Check versions:

```bash
python3 --version   # 3.12.x or 3.13.x
uv --version
```

If `uv` is missing:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Set a shell variable to the toolkit clone (adjust the path):

```bash
export MBT_ROOT="$HOME/dev/mcp-builder-toolkit-spec-kit"
```

Install the builder into that project environment (one-time per clone):

```bash
cd "$MBT_ROOT"
uv sync --all-extras
uv run mcp-builder --version
# Expected: mcp-builder 0.1.0a1 (or similar)
```

Helper for the rest of this guide:

```bash
alias mcp-builder='uv run --project "$MBT_ROOT" mcp-builder'
```

---

## Step 1 — Create a project directory

```bash
mkdir -p ~/dev/task-notes-mcp
cd ~/dev/task-notes-mcp
```

---

## Step 2 — Initialize the manifest

```bash
mcp-builder init --name task-notes-mcp --transport stdio --no-interactive
```

**What this does:** writes only `mcp-builder.yaml` — the declaration of *how* the project should look. It does **not** generate source yet.

**Expected output:**

```text
Created mcp-builder.yaml
Next: mcp-builder validate && mcp-builder generate
```

Open the file if you want to see the defaults:

```bash
cat mcp-builder.yaml
```

You should see:

- `apiVersion: mcpbuilder.dev/v1alpha1`
- target `fastmcp-python` / profile `fastmcp-python-2026.07`
- `transport.type: stdio`
- features for tests, lint, typing, and GitHub Actions

---

## Step 3 — Validate the manifest

```bash
mcp-builder validate
```

**Expected:** exit code `0` and `validate: ok`.

If validation fails, fix the fields named in the diagnostics (`path:` and `hint:`) and re-run.

Optional machine-readable form:

```bash
mcp-builder validate --format json | head
```

---

## Step 4 — Preview generation (dry-run)

```bash
mcp-builder generate --dry-run
```

You should see a table of planned files (`create` + ownership). Typical paths:

- `src/task_notes_mcp/server.py` (scaffold-once)
- `src/task_notes_mcp/tools/example.py` (scaffold-once)
- `pyproject.toml`, `README.md`, `.github/workflows/ci.yml` (managed)
- tests under `tests/`

Nothing is written yet.

---

## Step 5 — Generate the project

```bash
mcp-builder generate
```

**Expected tree (abridged):**

```text
.
├── mcp-builder.yaml
├── pyproject.toml
├── README.md
├── src/task_notes_mcp/
│   ├── server.py
│   └── tools/
│       └── example.py
├── tests/
└── .mcp-builder/state.json
```

### File ownership (important)

| Kind | Behavior |
|------|----------|
| **scaffold-once** | Created once; **your edits are kept** on regenerate |
| **managed** | Builder may update if the file still matches the last generated hash |
| **derived** | `.mcp-builder/state.json` — do not hand-edit |

You own `src/task_notes_mcp/**` and the tests by default.

---

## Step 6 — Install dependencies and run the scaffold tests

```bash
uv sync --all-extras
uv run ruff check .
uv run mypy src
uv run pytest -q
```

All generated tests should pass. That confirms the FastMCP skeleton is healthy before you change tools.

---

## Step 7 — Implement real tools

Replace the sample tools with a small in-memory notes API.

### 7.1 Edit the tools module

Open `src/task_notes_mcp/tools/example.py` and replace its contents with:

```python
"""Task notes tools — scaffold-once (safe to edit)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from fastmcp import FastMCP


@dataclass
class NoteStore:
    """In-memory note store for the lifetime of the server process."""

    notes: list[dict[str, str]] = field(default_factory=list)

    def add(self, text: str, tag: str = "general") -> dict[str, str]:
        note = {
            "id": uuid4().hex[:8],
            "text": text.strip(),
            "tag": tag.strip() or "general",
        }
        self.notes.append(note)
        return note

    def list(self, tag: str | None = None) -> list[dict[str, str]]:
        if not tag:
            return list(self.notes)
        needle = tag.strip().lower()
        return [n for n in self.notes if n["tag"].lower() == needle]


_store = NoteStore()


def health() -> dict[str, str]:
    """Return a simple health status for the server."""
    return {"status": "ok", "server": "task-notes-mcp"}


def add_note(text: str, tag: str = "general") -> dict[str, str]:
    """Add a short note to the in-memory store.

    Args:
        text: Note body (required).
        tag: Optional label for filtering later.

    Returns:
        The created note with id, text, and tag.
    """
    if not text or not text.strip():
        raise ValueError("text must be non-empty")
    return _store.add(text, tag=tag)


def list_notes(tag: str | None = None) -> list[dict[str, str]]:
    """List notes, optionally filtered by tag.

    Args:
        tag: If set, only notes with this tag are returned.
    """
    return _store.list(tag=tag)


def register_example_tools(mcp: FastMCP) -> None:
    """Register tools on the FastMCP server instance."""
    mcp.tool(health)
    mcp.tool(add_note)
    mcp.tool(list_notes)
```

> The function is still named `register_example_tools` so `server.py` keeps working without edits. You can rename it later and update the import in `server.py`.

### 7.2 Update unit tests

Replace `tests/test_example_tool.py` with:

```python
"""Unit tests for notes tools."""

from __future__ import annotations

from task_notes_mcp.tools.example import add_note, health, list_notes


def test_health() -> None:
    assert health()["status"] == "ok"


def test_add_and_list_notes() -> None:
    note = add_note("Buy milk", tag="errands")
    assert note["text"] == "Buy milk"
    assert note["tag"] == "errands"
    assert "id" in note

    all_notes = list_notes()
    assert any(n["id"] == note["id"] for n in all_notes)

    filtered = list_notes(tag="errands")
    assert all(n["tag"] == "errands" for n in filtered)
```

Replace `tests/test_server_smoke.py` with:

```python
"""Smoke tests for the MCP server module."""

from __future__ import annotations

import asyncio

from task_notes_mcp import server


def test_server_exports_mcp() -> None:
    assert server.mcp is not None


def test_server_registers_notes_tools() -> None:
    tools = asyncio.run(server.mcp.list_tools())
    names = {t.name for t in tools}
    assert {"health", "add_note", "list_notes"} <= names
```

### 7.3 Re-run quality gates

```bash
uv run ruff check .
uv run mypy src
uv run pytest -q
```

All tests should pass.

---

## Step 8 — Call the server with an MCP client (in-process)

This uses FastMCP’s supported client against your server object (no extra process).

```bash
uv run python - <<'PY'
import asyncio
from fastmcp import Client
from task_notes_mcp.server import mcp

async def main() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("tools:", sorted(t.name for t in tools))

        h = await client.call_tool("health", {})
        print("health:", h.data)

        created = await client.call_tool(
            "add_note",
            {"text": "Ship guided quickstart", "tag": "docs"},
        )
        print("added:", created.data)

        listed = await client.call_tool("list_notes", {"tag": "docs"})
        print("listed:", listed.data)

asyncio.run(main())
PY
```

**Expected (shape may vary slightly):**

```text
tools: ['add_note', 'health', 'list_notes']
health: {'status': 'ok', 'server': 'task-notes-mcp'}
added: {'id': '...', 'text': 'Ship guided quickstart', 'tag': 'docs'}
listed: [{'id': '...', 'text': 'Ship guided quickstart', 'tag': 'docs'}]
```

You now have a **functional MCP server** with tools that round-trip through the protocol layer.

---

## Step 9 — Call over real stdio transport

Same tools, but the client spawns your module as a subprocess (stdio MCP):

```bash
uv run python - <<'PY'
import asyncio
import sys
from pathlib import Path
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

async def main() -> None:
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "task_notes_mcp.server"],
        cwd=str(Path.cwd()),
    )
    async with Client(transport) as client:
        tools = await client.list_tools()
        print("stdio tools:", sorted(t.name for t in tools))
        result = await client.call_tool("add_note", {"text": "via stdio", "tag": "demo"})
        print("stdio add_note:", result.data)

asyncio.run(main())
PY
```

You may see FastMCP’s startup banner on stderr; that is normal. Tool results on stdout of this script confirm the handshake worked.

---

## Step 10 — Run the server as a long-lived process

For hosts that expect a stdio MCP server (Claude Desktop, Cursor, MCP Inspector):

```bash
uv run python -m task_notes_mcp.server
```

The process waits on stdin/stdout. Stop it with `Ctrl+C`.

### Example Claude Desktop config (local)

Add a server entry pointing at your project (paths are examples):

```json
{
  "mcpServers": {
    "task-notes": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/YOU/dev/task-notes-mcp",
        "run",
        "python",
        "-m",
        "task_notes_mcp.server"
      ]
    }
  }
}
```

Restart the host app, then try: “Add a note tagged docs: finish quickstart” and “List my docs notes.”

### MCP Inspector (optional)

If you use [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector uv --directory "$PWD" run python -m task_notes_mcp.server
```

---

## Step 11 — Safe regeneration after you edit tools

Change something in the **manifest** (for example, description), then:

```bash
mcp-builder generate --dry-run
mcp-builder generate
```

- Your `tools/example.py` and tests stay as you left them (**scaffold-once**).  
- Managed files (README, CI, …) update only if you did not modify them.

If you edited a managed file and templates also changed:

```bash
mcp-builder generate --force-managed README.md
```

Check project health anytime:

```bash
mcp-builder doctor
```

---

## Step 12 — Optional: Streamable HTTP + Docker

Useful when a remote or containerized MCP endpoint is needed.

### 12.1 Edit `mcp-builder.yaml`

Under `spec`, set:

```yaml
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
```

### 12.2 Preview and generate

```bash
mcp-builder generate --dry-run
mcp-builder generate
```

`server.py` is **scaffold-once**: if it already exists, the HTTP `mcp.run(...)` wiring is **not** auto-rewritten. Either:

- delete `src/task_notes_mcp/server.py` once and regenerate, then re-apply your tool registration, or  
- edit `main()` yourself to:

```python
def main() -> None:
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp",
    )
```

### 12.3 Run HTTP locally

```bash
uv run python -m task_notes_mcp.server
```

### 12.4 Or with Compose

```bash
docker compose up --build
```

**Security:** keep `host: 127.0.0.1` for local work. Do not publish `0.0.0.0` without authentication and TLS at the edge.

---

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| `mcp-builder: command not found` | Use `uv run --project "$MBT_ROOT" mcp-builder` or the alias from Step 0 |
| `validate` fails on profile | Keep `profile: fastmcp-python-2026.07` and `python: ">=3.12,<3.15"` |
| `ModuleNotFoundError: task_notes_mcp` | Run commands from the project root after `uv sync` |
| Tests fail after tool renames | Update imports in `server.py` and test files to match |
| Generation conflict on README | Review the file, then `mcp-builder generate --force-managed README.md` |
| stdio client “connection closed” | Ensure package installs (`uv sync`); run from project root |
| Doctor reports drift | Expected if you edited managed files; restore or force-managed |

```bash
mcp-builder doctor --format json
```

---

## What you learned

| Concept | Meaning |
|---------|---------|
| **Manifest** | Project *intent* (target, transport, features) — not the full tool catalog |
| **Generate** | Creates a conventional FastMCP project you own |
| **scaffold-once** | Tool code is yours; regenerate won’t clobber it |
| **managed** | Ops files (CI, Docker, README) can be refreshed safely |
| **stdio vs HTTP** | Local host tools vs remote/containerized MCP |

---

## Next steps

1. Persist notes to a file or SQLite instead of memory.  
2. Add input validation and clearer tool descriptions for models.  
3. Add resources or prompts via FastMCP APIs.  
4. Read `docs/extending.md` if you want another generation target or feature.  
5. For pilots, use `docs/pilot-feedback.md`.

---

## Command cheat sheet

```bash
# Builder (from any directory, with alias configured)
mcp-builder init --name NAME --transport stdio --no-interactive
mcp-builder validate
mcp-builder generate --dry-run
mcp-builder generate
mcp-builder doctor

# Generated project
uv sync --all-extras
uv run ruff check .
uv run mypy src
uv run pytest
uv run python -m task_notes_mcp.server
```

You should now have a **working MCP server** with custom tools, tests, and a proven client path—built with MCP Builder Toolkit.
