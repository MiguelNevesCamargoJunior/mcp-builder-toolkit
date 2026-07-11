"""Bump the single package version source, commit, tag, and push.

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

from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
INIT_PY = ROOT / "src/mcp_builder/__init__.py"


def read_version() -> str:
    text = INIT_PY.read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*"(.*)"', text, re.MULTILINE)
    if not m:
        print("error: __version__ not found in src/mcp_builder/__init__.py")
        sys.exit(1)
    return m.group(1)


def write_version(version: str) -> None:
    text = INIT_PY.read_text(encoding="utf-8")
    text = re.sub(
        r'^__version__\s*=\s*".*"',
        f'__version__ = "{version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    INIT_PY.write_text(text, encoding="utf-8")
    print(f"version {version} written to src/mcp_builder/__init__.py")


def bump(version: str, part: str) -> str:
    parsed = Version(version)
    major, minor, patch = parsed.release[:3]
    pre = parsed.pre

    if part == "release":
        if pre:
            return f"{major}.{minor}.{patch}"
        print("error: no pre-release segment to remove")
        sys.exit(1)

    if part == "patch":
        if pre:
            return f"{major}.{minor}.{patch}{pre[0]}{pre[1] + 1}"
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        print(f"error: unknown part {part!r}")
        sys.exit(1)

    if pre:
        return f"{major}.{minor}.{patch}{pre[0]}1"
    return f"{major}.{minor}.{patch}"


def git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    part = sys.argv[1]
    no_tag = "--no-tag" in sys.argv
    current = read_version()
    next_ver = bump(current, part)
    write_version(next_ver)

    subprocess.run(["uv", "lock"], cwd=ROOT, check=True)

    tag = f"v{next_ver}"
    git("add", str(INIT_PY.relative_to(ROOT)), "uv.lock")
    git("commit", "-m", f"chore: bump version to {next_ver}")
    if no_tag:
        git("push")
        print(f"\nversion bumped to {next_ver} on main (no tag)")
    else:
        git("tag", tag)
        git("push")
        git("push", "origin", tag)
        print(f"\nrelease {tag} created and pushed")


if __name__ == "__main__":
    main()
