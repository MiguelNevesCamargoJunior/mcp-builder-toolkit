"""MCP server entry point.

This file is scaffold-once: the builder will not overwrite your changes.
Replace the example tool with your real implementations.
"""

from __future__ import annotations

import os
import json
import logging

from fastmcp import FastMCP

from http_docker_golden.tools.example import register_example_tools


class JsonFormatter(logging.Formatter):
    """Format generated server logs as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """Install the generated structured logger without adding dependencies."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


configure_logging()

mcp = FastMCP(name="http-docker-golden")

register_example_tools(mcp)


def main() -> None:
    """Run the MCP server."""
    mcp.run(
        transport="http",
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_PORT", "8000")),
        path=os.getenv("MCP_PATH", "/mcp"),
    )


if __name__ == "__main__":
    main()
