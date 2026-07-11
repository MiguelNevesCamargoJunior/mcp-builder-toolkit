"""Unit tests for the example tools."""

from __future__ import annotations

from http_docker_golden.tools.example import echo, health


def test_echo_tool() -> None:
    assert echo("hello") == "hello"


def test_health_tool() -> None:
    result = health()
    assert result["status"] == "ok"
    assert result["server"] == "http-docker-golden"
