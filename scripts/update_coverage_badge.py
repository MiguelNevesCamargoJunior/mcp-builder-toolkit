"""Update coverage badge in README.md after test run.

Called from CI release workflow after pytest --cov.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def get_coverage() -> float:
    result = subprocess.run(
        ["coverage", "report", "--format=total"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    raw = result.stdout.strip().rstrip("%")
    try:
        return round(float(raw), 1)
    except (ValueError, OSError):
        print(f"warning: could not parse coverage: {raw!r}", file=sys.stderr)
        return 0.0


def color_for(pct: float) -> str:
    if pct >= 90:
        return "brightgreen"
    if pct >= 80:
        return "yellow"
    return "red"


def update_badge(pct: float, color: str) -> bool:
    text = README.read_text(encoding="utf-8")
    new = f"coverage-{pct}%25-{color}"
    updated = re.sub(
        r"coverage-\d+\.?\d*%25-(?:brightgreen|yellow|red)",
        new,
        text,
    )
    if updated == text:
        return False
    README.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    pct = get_coverage()
    color = color_for(pct)
    changed = update_badge(pct, color)
    print(f"Coverage badge: {pct}% ({color}){' → updated' if changed else ' → unchanged'}")


if __name__ == "__main__":
    main()
