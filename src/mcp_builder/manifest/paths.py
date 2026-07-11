"""Safe path normalization for generation destinations."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

_UNSAFE = re.compile(r"[\x00-\x1f]")


def normalize_relative_path(path: str) -> str:
    """Normalize a project-relative path to posix form.

    Raises:
        ValueError: if the path is absolute, empty, or escapes the project root.
    """
    if not path or path.strip() == "":
        raise ValueError("path must be non-empty")
    if _UNSAFE.search(path):
        raise ValueError("path contains control characters")
    raw = path.replace("\\", "/").strip()
    if raw.startswith("/") or re.match(r"^[A-Za-z]:/", raw):
        raise ValueError("path must be relative")
    parts = PurePosixPath(raw).parts
    if any(p in {"", "."} for p in parts if p == ""):
        raise ValueError("path is invalid")
    stack: list[str] = []
    for part in parts:
        if part == ".":
            continue
        if part == "..":
            if not stack:
                raise ValueError("path escapes project root")
            stack.pop()
            continue
        if part in {".", ".."}:
            raise ValueError("path is invalid")
        stack.append(part)
    if not stack:
        raise ValueError("path resolves to empty")
    return "/".join(stack)


def is_safe_relative_path(path: str) -> bool:
    try:
        normalize_relative_path(path)
        return True
    except ValueError:
        return False
