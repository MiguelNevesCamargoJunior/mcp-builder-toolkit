"""Distribution metadata and packaged-resource checks."""

from __future__ import annotations

from mcp_builder.generation.renderer import package_template_root


def test_installed_package_contains_generator_templates() -> None:
    root = package_template_root("mcp_builder.targets.fastmcp_python")
    expected = {
        "README.md.j2",
        "pyproject.toml.j2",
        "package/server.py.j2",
        "package/tools/example.py.j2",
        "tests/test_server_smoke.py.j2",
    }
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    assert expected <= actual


def test_package_declares_typing_marker() -> None:
    package_root = package_template_root("mcp_builder.targets.fastmcp_python").parents[2]
    assert (package_root / "py.typed").is_file()
