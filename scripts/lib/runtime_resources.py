"""Locate runtime resources in a checkout, installed wheel, or frozen binary."""

from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def source_root() -> Path | None:
    """Return the engine checkout root, never the configured knowledge root."""
    root = PACKAGE_ROOT.parent
    if PACKAGE_ROOT.name == "scripts" and (root / "pyproject.toml").is_file():
        return root
    return None


def resource_path(relative: str) -> Path:
    """Resolve a trusted engine resource name relative to its distribution."""
    root = source_root()
    if root is not None:
        return root / relative
    return PACKAGE_ROOT / "_resources" / relative
