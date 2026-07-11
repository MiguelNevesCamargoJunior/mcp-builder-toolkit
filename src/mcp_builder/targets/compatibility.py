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
