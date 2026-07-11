"""Bump version in pyproject.toml, commit, tag, and push.

Usage:
    uv run python scripts/bump_version.py patch   # 0.1.0a1 -> 0.1.0a2
    uv run python scripts/bump_version.py minor   # 0.1.0a1 -> 0.2.0a1
    uv run python scripts/bump_version.py major   # 0.1.0a1 -> 1.0.0a1
    uv run python scripts/bump_version.py release # 0.1.0a1 -> 0.1.0
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
INIT_PY = ROOT / "src/mcp_builder/__init__.py"


def read_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"(.*)"', text, re.MULTILINE)
    if not m:
        print("error: version not found in pyproject.toml")
        sys.exit(1)
    return m.group(1)


def write_version(version: str) -> None:
    for path in (PYPROJECT, INIT_PY):
        text = path.read_text(encoding="utf-8")
        text = re.sub(r'^version\s*=\s*".*"', f'version = "{version}"', text, count=1, flags=re.MULTILINE)
        path.write_text(text, encoding="utf-8")
    print(f"version {version} written to pyproject.toml and __init__.py")


def bump(version: str, part: str) -> str:
    pre = re.search(r"(a|b|rc)\d+$", version)
    parts = [int(x) for x in re.split(r"[.abrc]", version) if x.isdigit()]

    if part == "release":
        if pre:
            return version[: version.index(pre.group())]
        print("error: no pre-release segment to remove")
        sys.exit(1)

    if part == "patch":
        parts[-1] += 1
    elif part == "minor":
        parts[-3] += 1
        parts[-2] = 0
        parts[-1] = 1 if pre else 0
    elif part == "major":
        parts[-4] += 1 if len(parts) >= 4 else 1
        parts[-3] = 0
        parts[-2] = 0
        parts[-1] = 1 if pre else 0
    else:
        print(f"error: unknown part {part!r}")
        sys.exit(1)

    if pre:
        base = ".".join(str(p) for p in parts[:3])
        pre_type = re.search(r"(a|b|rc)", pre.group()).group()
        pre_num = parts[3] if len(parts) > 3 else 1
        return f"{base}{pre_type}{pre_num}"
    return ".".join(str(p) for p in parts)


def git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    part = sys.argv[1]
    current = read_version()
    next_ver = bump(current, part)
    write_version(next_ver)

    subprocess.run(["uv", "lock"], cwd=ROOT, check=True)

    tag = f"v{next_ver}"
    git("add", str(PYPROJECT.relative_to(ROOT)), str(INIT_PY.relative_to(ROOT)), "uv.lock")
    git("commit", "-m", f"chore: bump version to {next_ver}")
    git("tag", tag)
    git("push")
    git("push", "origin", tag)
    print(f"\nrelease {tag} created and pushed")


if __name__ == "__main__":
    main()
