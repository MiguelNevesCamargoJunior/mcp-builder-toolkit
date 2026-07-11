"""Compatibility profile registry for generation targets."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PROFILE_ID = "fastmcp-python-2026.07"
DEFAULT_RUNTIME = "fastmcp-python"
DEFAULT_PROTOCOL = "2025-11-25"
DEFAULT_PYTHON = ">=3.12,<3.15"
DEFAULT_FASTMCP = ">=3.4.4,<3.5"


@dataclass(frozen=True, slots=True)
class CompatibilityProfile:
    id: str
    runtime: str
    protocol: str
    python: str
    fastmcp: str
    description: str = ""

    def python_versions(self) -> list[tuple[int, int]]:
        """Return explicit (major, minor) versions from the python specifier.

        Handles the ``>=X.Y,<A.B`` form used by the current profile.
        """
        spec = self.python.strip()
        lo = 0, 0
        hi = 99, 99
        for part in spec.split(","):
            part = part.strip()
            if part.startswith(">="):
                parts = part[2:].strip().split(".")
                lo = int(parts[0]), int(parts[1])
            elif part.startswith(">"):
                parts = part[1:].strip().split(".")
                lo = int(parts[0]), int(parts[1]) + 1
            elif part.startswith("<="):
                parts = part[2:].strip().split(".")
                hi = int(parts[0]), int(parts[1]) + 1
            elif part.startswith("<"):
                parts = part[1:].strip().split(".")
                hi = int(parts[0]), int(parts[1])
        versions: list[tuple[int, int]] = []
        major, minor = lo
        while (major, minor) < hi:
            versions.append((major, minor))
            minor += 1
            if minor > 15:
                major += 1
                minor = 0
        return versions


class CompatibilityRegistry:
    """In-process registry of tested builder profiles."""

    def __init__(self, profiles: dict[str, CompatibilityProfile]) -> None:
        self._profiles = profiles

    @classmethod
    def default(cls) -> CompatibilityRegistry:
        profile = CompatibilityProfile(
            id=DEFAULT_PROFILE_ID,
            runtime=DEFAULT_RUNTIME,
            protocol=DEFAULT_PROTOCOL,
            python=DEFAULT_PYTHON,
            fastmcp=DEFAULT_FASTMCP,
            description="FastMCP 3.4.x on Python 3.12-3.14, MCP 2025-11-25",
        )
        return cls({profile.id: profile})

    def get(self, profile_id: str) -> CompatibilityProfile | None:
        return self._profiles.get(profile_id)

    def ids(self) -> list[str]:
        return sorted(self._profiles)

    def require(self, profile_id: str) -> CompatibilityProfile:
        profile = self.get(profile_id)
        if profile is None:
            raise KeyError(profile_id)
        return profile
