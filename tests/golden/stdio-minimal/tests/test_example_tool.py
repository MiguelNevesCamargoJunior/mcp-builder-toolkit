"""Unit tests for the example tools."""

from __future__ import annotations

from golden_stdio.tools.example import echo, health


def test_echo_tool() -> None:
    assert echo("hello") == "hello"


def test_health_tool() -> None:
    result = health()
    assert result["status"] == "ok"
    assert result["server"] == "golden-stdio"
