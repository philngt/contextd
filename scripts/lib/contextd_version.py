#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared version resolution for CLI, MCP, and packaged source builds."""

from __future__ import annotations

import importlib
import importlib.metadata
import re
from pathlib import Path
from typing import Optional


def _metadata_version(package_name: str) -> Optional[str]:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _generated_version() -> Optional[str]:
    for module_name in ("scripts._version", "_version"):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        version = getattr(module, "__version__", None)
        if isinstance(version, str) and version.strip():
            return version.strip()
    return None


def _version_file(start_path: Optional[Path]) -> Optional[str]:
    roots = []
    if start_path is not None:
        roots.append(Path(start_path).resolve())
    roots.append(Path(__file__).resolve())

    for start in roots:
        candidates = [start] if start.is_dir() else [start.parent]
        candidates.extend(candidates[0].parents)
        for directory in candidates:
            path = directory / "VERSION"
            if not path.is_file():
                continue
            try:
                first_line = path.read_text(encoding="utf-8").splitlines()[0].strip()
            except (OSError, IndexError, UnicodeDecodeError):
                continue
            if first_line:
                return first_line
    return None


def _pyproject_version(start_path: Optional[Path]) -> Optional[str]:
    if start_path is None:
        return None
    start = Path(start_path).resolve()
    direct = start / "pyproject.toml" if start.is_dir() else start.parent / "pyproject.toml"
    direct_candidates = [direct]
    candidates = [start] if start.is_dir() else [start.parent]
    candidates.extend(candidates[0].parents)
    for path in direct_candidates + [directory / "pyproject.toml" for directory in candidates]:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', text)
        if match:
            return match.group(1).strip()
    return None


def get_version(package_name: str = "contextd",
                start_path: Optional[Path] = None) -> str:
    """Return package metadata -> generated file -> VERSION -> dev fallback."""
    source_metadata = _pyproject_version(start_path)
    installed_metadata = _metadata_version(package_name)
    if installed_metadata:
        if source_metadata and installed_metadata != source_metadata:
            return source_metadata
        return installed_metadata
    generated_metadata = _generated_version()
    version_file = _version_file(start_path)
    if generated_metadata:
        if source_metadata and not version_file and generated_metadata != source_metadata:
            return source_metadata
        return generated_metadata
    return (
        source_metadata
        or version_file
        or "0.0.0-dev"
    )
