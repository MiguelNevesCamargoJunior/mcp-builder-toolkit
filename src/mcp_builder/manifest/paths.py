"""Safe path normalization for generation destinations."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

_UNSAFE = re.compile(r"[\x00-\x1f]")
_WINDOWS_RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.I)


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
    if raw.startswith("/") or raw.startswith("//") or re.match(r"^[A-Za-z]:", raw):
        raise ValueError("path must be relative")
    parts = PurePosixPath(raw).parts
    stack: list[str] = []
    for part in parts:
        if part == ".":
            continue
        if part == "..":
            raise ValueError("path must not contain traversal segments")
        if part.endswith((" ", ".")) or _WINDOWS_RESERVED.match(part):
            raise ValueError(f"path contains unsupported platform name: {part!r}")
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


def safe_project_path(project_root: Path, relative_path: str) -> Path:
    """Return a contained destination after rejecting existing symlink components."""
    normalized = normalize_relative_path(relative_path)
    root = project_root.resolve()
    candidate = root.joinpath(*PurePosixPath(normalized).parts)
    current = root
    for part in PurePosixPath(normalized).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"path traverses a symbolic link: {current}")
    return candidate
