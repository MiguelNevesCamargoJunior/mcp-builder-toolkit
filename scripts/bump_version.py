"""Print and validate the package version derived from the latest git tag.

Usage:
    uv run python scripts/bump_version.py          # print current version
    uv run python scripts/bump_version.py validate  # check tag matches version
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_version() -> str:
    try:
        return subprocess.run(
            ["git", "describe", "--tags", "--dirty", "--match", "v*"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip().lstrip("v")
    except subprocess.CalledProcessError:
        return "0.0.0"


def main() -> None:
    version = git_version()
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        tag = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        ).stdout.strip()
        expected = f"v{version}"
        if tag != expected:
            print(f"error: tag {tag!r} does not match version {expected!r}")
            sys.exit(1)
        print(f"ok: tag {tag} matches version {version}")
    else:
        print(version)


if __name__ == "__main__":
    main()
