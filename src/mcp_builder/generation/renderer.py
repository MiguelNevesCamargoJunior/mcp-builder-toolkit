"""Strict Jinja2 rendering using package-owned templates only."""

from __future__ import annotations

import hashlib
from importlib import resources
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape


def content_hash(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def make_env(package: str, templates_package: str) -> Environment:
    """Create a strict environment bound to a package template directory."""
    return Environment(
        loader=PackageLoader(package, templates_package),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=()),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_template(env: Environment, template_name: str, context: dict[str, Any]) -> str:
    template = env.get_template(template_name)
    return template.render(**context)


def package_template_root(package: str, templates_package: str = "templates") -> Path:
    """Resolve template package path for inspection/tests."""
    root = resources.files(package).joinpath(templates_package)
    return Path(str(root))
