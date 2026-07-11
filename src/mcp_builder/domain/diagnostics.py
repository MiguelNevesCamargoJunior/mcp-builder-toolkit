"""Structured diagnostics consumed by text and JSON renderers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Diagnostic(BaseModel):
    """A single user-facing diagnostic with a stable code."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(pattern=r"^MBT-[A-Z]+-[0-9]{3}$")
    severity: Severity
    message: str = Field(min_length=1)
    path: str | None = None
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    hint: str | None = None
    details: dict[str, Any] | None = None


class DiagnosticSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    errors: int = Field(ge=0)
    warnings: int = Field(ge=0)
    info: int = Field(ge=0)

    @classmethod
    def from_diagnostics(cls, diagnostics: Sequence[Diagnostic]) -> DiagnosticSummary:
        errors = sum(1 for d in diagnostics if d.severity is Severity.ERROR)
        warnings = sum(1 for d in diagnostics if d.severity is Severity.WARNING)
        info = sum(1 for d in diagnostics if d.severity is Severity.INFO)
        return cls(errors=errors, warnings=warnings, info=info)


class CommandStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


class PlannedChangeAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    UNCHANGED = "unchanged"
    PRESERVE = "preserve"
    CONFLICT = "conflict"
    REMOVE_MANAGED = "remove-managed"
    ORPHAN = "orphan"


class Ownership(StrEnum):
    MANAGED = "managed"
    SCAFFOLD_ONCE = "scaffold-once"
    DERIVED = "derived"


class PlannedChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    action: PlannedChangeAction
    ownership: Ownership


class CommandResult(BaseModel):
    """Machine-readable command result envelope."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    command: str
    status: CommandStatus
    builder_version: str = Field(alias="builderVersion")
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    summary: DiagnosticSummary
    changes: list[PlannedChange] | None = None

    def model_dump_json_envelope(self) -> str:
        return self.model_dump_json(by_alias=True, exclude_none=True)


def status_from_diagnostics(diagnostics: Sequence[Diagnostic]) -> CommandStatus:
    if any(d.severity is Severity.ERROR for d in diagnostics):
        return CommandStatus.ERROR
    if any(d.severity is Severity.WARNING for d in diagnostics):
        return CommandStatus.WARNING
    return CommandStatus.OK


def has_errors(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(d.severity is Severity.ERROR for d in diagnostics)


# ---------------------------------------------------------------------------
# Diagnostic code registry (stable once documented)
# ---------------------------------------------------------------------------


class Codes:
    """Central registry of diagnostic codes."""

    MANIFEST_NOT_FOUND = "MBT-MANIFEST-001"
    MANIFEST_PARSE = "MBT-MANIFEST-002"
    MANIFEST_SCHEMA = "MBT-MANIFEST-003"
    MANIFEST_SEMANTIC = "MBT-MANIFEST-004"
    MANIFEST_TOO_LARGE = "MBT-MANIFEST-005"
    MANIFEST_UNSAFE = "MBT-MANIFEST-006"
    MANIFEST_EXISTS = "MBT-MANIFEST-007"

    PROFILE_UNKNOWN = "MBT-COMPAT-001"
    PROFILE_PYTHON = "MBT-COMPAT-002"
    PROFILE_PROTOCOL = "MBT-COMPAT-003"

    PATH_TRAVERSAL = "MBT-PATH-001"
    PATH_INVALID = "MBT-PATH-002"

    GEN_CONFLICT = "MBT-GEN-001"
    GEN_DUPLICATE = "MBT-GEN-002"
    GEN_LOCK = "MBT-GEN-003"
    GEN_IO = "MBT-GEN-004"
    GEN_SUCCESS = "MBT-GEN-010"

    INIT_SUCCESS = "MBT-INIT-001"
    INIT_EXISTS = "MBT-INIT-002"

    USAGE = "MBT-USAGE-001"
    INTERNAL = "MBT-INTERNAL-001"
