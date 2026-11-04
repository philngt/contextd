#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared version resolution for CLI, MCP, and packaged source builds."""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import re
from pathlib import Path
from typing import Optional

from .runtime_resources import source_root


DISTRIBUTION_NAME = "philngt-contextd"


def _metadata_version(package_name: str) -> Optional[str]:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _generated_version() -> Optional[str]:
    package = __package__.rpartition(".")[0]
    if package:
        try:
            module = importlib.import_module(f"{package}._version")
        except ImportError:
            return None
    else:
        # Legacy source imports use `lib`; load only their sibling release file.
        # Do not import an unrelated top-level `_version` or `scripts` package.
        path = Path(__file__).resolve().parents[1] / "_version.py"
        if not path.is_file():
            return None
        spec = importlib.util.spec_from_file_location("_contextd_source_version", path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    version = getattr(module, "__version__", None)
    return version.strip() if isinstance(version, str) and version.strip() else None


def _version_file(start_path: Optional[Path]) -> Optional[str]:
    if source_root() is None:
        return None
    roots = []
    if start_path is not None:
        roots.append(Path(start_path).resolve())
    roots.append(Path(__file__).resolve())

    for start in roots:
        candidates = [start] if start.is_dir() else [start.parent]
        candidates.extend(candidates[0].parents)
        for directory in candidates:
            if not (directory / "scripts" / "lib" / "contextd_version.py").is_file():
                continue
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
    if start_path is None or source_root() is None:
        return None
    start = Path(start_path).resolve()
    direct = start / "pyproject.toml" if start.is_dir() else start.parent / "pyproject.toml"
    direct_candidates = [direct]
    candidates = [start] if start.is_dir() else [start.parent]
    candidates.extend(candidates[0].parents)
    for path in direct_candidates + [directory / "pyproject.toml" for directory in candidates]:
        if not path.is_file() or not (path.parent / "scripts" / "lib" / "contextd_version.py").is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', text)
        if match:
            return match.group(1).strip()
    return None


def get_version(package_name: str = DISTRIBUTION_NAME,
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
