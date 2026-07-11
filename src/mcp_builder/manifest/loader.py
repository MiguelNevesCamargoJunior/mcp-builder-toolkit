"""Safe YAML loading with size and nesting controls."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import ValidationError
from yaml import SafeLoader
from yaml.constructor import ConstructorError
from yaml.nodes import Node
from yaml.tokens import AliasToken, AnchorToken

from mcp_builder.domain.diagnostics import Codes, Diagnostic, Severity
from mcp_builder.manifest.models import ManifestModel

# Security limits (constitution: secure defaults)
MAX_MANIFEST_BYTES = 256 * 1024  # 256 KiB
MAX_NESTING_DEPTH = 32
MAX_COLLECTION_ITEMS = 1_000


class RestrictedSafeLoader(SafeLoader):
    """SafeLoader that rejects custom tags."""

    def construct_undefined(self, node: Node) -> Any:
        raise ConstructorError(
            None,
            None,
            f"unsupported YAML tag: {node.tag!r}",
            node.start_mark,
        )


# PyYAML uses None as the key for the default/undefined constructor.
RestrictedSafeLoader.add_constructor(
    cast(str, None),
    RestrictedSafeLoader.construct_undefined,
)


class LoadResult:
    __slots__ = ("diagnostics", "manifest", "raw")

    def __init__(
        self,
        manifest: ManifestModel | None,
        diagnostics: list[Diagnostic],
        raw: dict[str, Any] | None = None,
    ) -> None:
        self.manifest = manifest
        self.diagnostics = diagnostics
        self.raw = raw

    @property
    def ok(self) -> bool:
        return self.manifest is not None and not any(
            d.severity is Severity.ERROR for d in self.diagnostics
        )


def _depth_of(value: Any, depth: int = 0) -> int:
    if depth > MAX_NESTING_DEPTH:
        return depth
    if isinstance(value, dict):
        if not value:
            return depth
        return max(_depth_of(v, depth + 1) for v in value.values())
    if isinstance(value, list):
        if not value:
            return depth
        return max(_depth_of(v, depth + 1) for v in value)
    return depth


def _count_items(value: Any) -> int:
    if isinstance(value, dict):
        return len(value) + sum(_count_items(v) for v in value.values())
    if isinstance(value, list):
        return len(value) + sum(_count_items(v) for v in value)
    return 0


def _loc_from_validation_error(err: Mapping[str, Any]) -> str | None:
    loc = err.get("loc")
    if not loc:
        return None
    parts: list[str] = []
    for item in loc:
        if isinstance(item, int):
            parts.append(str(item))
        else:
            parts.append(str(item))
    return ".".join(parts)


def load_manifest_path(path: Path) -> LoadResult:
    diagnostics: list[Diagnostic] = []

    if not path.exists():
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_NOT_FOUND,
                severity=Severity.ERROR,
                message=f"Manifest not found: {path}",
                path=str(path),
                hint="Run `mcp-builder init` or pass --file PATH.",
            )
        )
        return LoadResult(None, diagnostics)

    if not path.is_file():
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_PARSE,
                severity=Severity.ERROR,
                message=f"Manifest path is not a file: {path}",
                path=str(path),
            )
        )
        return LoadResult(None, diagnostics)

    size = path.stat().st_size
    if size > MAX_MANIFEST_BYTES:
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_TOO_LARGE,
                severity=Severity.ERROR,
                message=f"Manifest exceeds size limit of {MAX_MANIFEST_BYTES} bytes",
                path=str(path),
                details={"size": size, "limit": MAX_MANIFEST_BYTES},
            )
        )
        return LoadResult(None, diagnostics)

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_PARSE,
                severity=Severity.ERROR,
                message=f"Failed to read manifest: {exc}",
                path=str(path),
            )
        )
        return LoadResult(None, diagnostics)

    return load_manifest_text(text, source=str(path))


def load_manifest_text(text: str, *, source: str = "<manifest>") -> LoadResult:
    diagnostics: list[Diagnostic] = []

    if len(text.encode("utf-8")) > MAX_MANIFEST_BYTES:
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_TOO_LARGE,
                severity=Severity.ERROR,
                message=f"Manifest exceeds size limit of {MAX_MANIFEST_BYTES} bytes",
                path=source,
            )
        )
        return LoadResult(None, diagnostics)

    try:
        for token in yaml.scan(text, Loader=RestrictedSafeLoader):
            if isinstance(token, (AnchorToken, AliasToken)):
                diagnostics.append(
                    Diagnostic(
                        code=Codes.MANIFEST_UNSAFE,
                        severity=Severity.ERROR,
                        message="YAML anchors and aliases are not supported",
                        path=source,
                        line=_yaml_line(token.start_mark),
                        column=_yaml_column(token.start_mark),
                        hint="Expand the value explicitly instead of using anchors or aliases.",
                    )
                )
                return LoadResult(None, diagnostics)
        raw = yaml.load(text, Loader=RestrictedSafeLoader)
    except ConstructorError as exc:
        mark = getattr(exc, "problem_mark", None)
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_UNSAFE,
                severity=Severity.ERROR,
                message=f"Unsafe or unsupported YAML: {exc.problem or exc}",
                path=source,
                line=_yaml_line(mark),
                column=_yaml_column(mark),
                hint="Use plain YAML maps/lists/scalars only; custom tags are rejected.",
            )
        )
        return LoadResult(None, diagnostics)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_PARSE,
                severity=Severity.ERROR,
                message=f"YAML parse error: {exc}",
                path=source,
                line=_yaml_line(mark),
                column=_yaml_column(mark),
                hint="Fix YAML syntax and try again.",
            )
        )
        return LoadResult(None, diagnostics)

    if raw is None:
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_PARSE,
                severity=Severity.ERROR,
                message="Manifest is empty",
                path=source,
            )
        )
        return LoadResult(None, diagnostics)

    if not isinstance(raw, dict):
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_SCHEMA,
                severity=Severity.ERROR,
                message="Manifest root must be a mapping",
                path=source,
            )
        )
        return LoadResult(None, diagnostics)

    depth = _depth_of(raw)
    if depth > MAX_NESTING_DEPTH:
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_UNSAFE,
                severity=Severity.ERROR,
                message=f"Manifest nesting depth {depth} exceeds limit {MAX_NESTING_DEPTH}",
                path=source,
            )
        )
        return LoadResult(None, diagnostics)

    items = _count_items(raw)
    if items > MAX_COLLECTION_ITEMS:
        diagnostics.append(
            Diagnostic(
                code=Codes.MANIFEST_UNSAFE,
                severity=Severity.ERROR,
                message=f"Manifest collection size {items} exceeds limit {MAX_COLLECTION_ITEMS}",
                path=source,
            )
        )
        return LoadResult(None, diagnostics)

    try:
        manifest = ManifestModel.model_validate(raw)
    except ValidationError as exc:
        for err in exc.errors():
            loc = _loc_from_validation_error(err)
            msg = err.get("msg", "validation error")
            diagnostics.append(
                Diagnostic(
                    code=Codes.MANIFEST_SCHEMA,
                    severity=Severity.ERROR,
                    message=msg,
                    path=loc,
                    hint="See contracts/manifest.schema.json for allowed fields.",
                    details={"type": err.get("type"), "input": _safe_input(err.get("input"))},
                )
            )
        return LoadResult(None, diagnostics, raw=raw)

    return LoadResult(manifest, diagnostics, raw=raw)


def _safe_input(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, dict)):
        return type(value).__name__
    return type(value).__name__


def _yaml_line(mark: Any) -> int | None:
    if mark is None or getattr(mark, "line", None) is None:
        return None
    return int(mark.line) + 1


def _yaml_column(mark: Any) -> int | None:
    if mark is None or getattr(mark, "column", None) is None:
        return None
    return int(mark.column) + 1
