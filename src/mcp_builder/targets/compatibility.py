"""Compatibility profile registry for generation targets."""

from __future__ import annotations

from dataclasses import dataclass


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
            id="fastmcp-python-2026.07",
            runtime="fastmcp-python",
            protocol="2025-11-25",
            python=">=3.12,<3.15",
            fastmcp=">=3.4.4,<3.5",
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
