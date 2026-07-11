"""Stable CLI exit codes from contracts/cli-contract.md."""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Documented process exit codes for ``mcp-builder``."""

    SUCCESS = 0
    INTERNAL_ERROR = 1
    USAGE_OR_VALIDATION = 2
    GENERATION_CONFLICT = 3
    UNSUPPORTED_ENVIRONMENT = 4
    FILESYSTEM_FAILURE = 5
    DOCTOR_UNHEALTHY = 6
