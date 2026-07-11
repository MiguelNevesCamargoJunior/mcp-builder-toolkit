"""MCP Builder Toolkit — manifest-driven MCP project generation."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mcp-builder-toolkit")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__"]
