"""T014: property-based tests for identifiers and paths."""

from __future__ import annotations

import re

from hypothesis import given
from hypothesis import strategies as st

from mcp_builder.manifest.models import NAME_PATTERN, PACKAGE_PATTERN
from mcp_builder.manifest.normalize import name_to_package
from mcp_builder.manifest.paths import is_safe_relative_path, normalize_relative_path

_name_re = re.compile(NAME_PATTERN)
_pkg_re = re.compile(PACKAGE_PATTERN)


@given(
    st.from_regex(NAME_PATTERN, fullmatch=True).filter(lambda s: 1 <= len(s) <= 63),
)
def test_valid_names_derive_packages(name: str) -> None:
    assert _name_re.match(name)
    pkg = name_to_package(name)
    assert _pkg_re.match(pkg)


@given(st.text(min_size=1, max_size=40))
def test_path_normalization_never_escapes(raw: str) -> None:
    if is_safe_relative_path(raw):
        norm = normalize_relative_path(raw)
        assert ".." not in PureParts(norm)
        assert not norm.startswith("/")
    else:
        try:
            normalize_relative_path(raw)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


def PureParts(path: str) -> list[str]:
    return [p for p in path.split("/") if p]


@given(st.lists(st.sampled_from(["a", "b", "c", "pkg", "src", "tests"]), min_size=1, max_size=5))
def test_safe_relative_segments(parts: list[str]) -> None:
    path = "/".join(parts)
    assert normalize_relative_path(path) == path


def test_path_rejects_traversal() -> None:
    for bad in ("../x", "a/../../b", "/abs", "C:/windows", ""):
        assert not is_safe_relative_path(bad)
