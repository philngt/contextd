#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation helpers for contextd pack APIs and retrieval maps."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pack_loader
import task_context_engine
from context_security import reject_unsafe_entry


PACK_NAME_RE = re.compile(r"^pack-[a-z0-9][a-z0-9-]*$")
VALID_SEVERITIES = {"error", "warning", "info"}


def _issue(severity: str, check: str, message: str, path: str) -> Dict:
    if severity not in VALID_SEVERITIES:
        severity = "error"
    return {
        "severity": severity,
        "check": check,
        "message": message,
        "path": path,
    }


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_manifest(pack_dir: Path) -> Dict:
    path = pack_dir / "pack.yaml"
    try:
        return pack_loader._parse_simple_yaml(path.read_text(encoding="utf-8"))  # noqa: SLF001
    except Exception:
        return {}


def _list_pack_dirs(wiki_root: Path) -> List[Path]:
    packs_dir = wiki_root / "packs"
    if not packs_dir.is_dir():
        return []
    return sorted(p for p in packs_dir.iterdir() if p.is_dir())


def _as_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _validate_pack_dir(wiki_root: Path, pack_dir: Path,
                       all_pack_names: Iterable[str]) -> List[Dict]:
    issues: List[Dict] = []
    pack_name = pack_dir.name
    rel_pack = _rel(pack_dir, wiki_root)
    manifest_path = pack_dir / "pack.yaml"
    if not manifest_path.is_file():
        return [_issue("error", "pack.manifest", "Missing pack.yaml", rel_pack)]

    manifest = _load_manifest(pack_dir)
    if not manifest:
        return [_issue("error", "pack.manifest", "Could not parse pack.yaml", _rel(manifest_path, wiki_root))]

    declared_name = str(manifest.get("name") or "")
    if declared_name != pack_name:
        issues.append(_issue(
            "error",
            "pack.name",
            f"pack.yaml name `{declared_name}` must match directory `{pack_name}`",
            _rel(manifest_path, wiki_root),
        ))
    if not PACK_NAME_RE.match(pack_name):
        issues.append(_issue("error", "pack.name", "Pack name must match `pack-{slug}`", rel_pack))
    if not manifest.get("version"):
        issues.append(_issue("warning", "pack.version", "Missing version", _rel(manifest_path, wiki_root)))
    if not manifest.get("description"):
        issues.append(_issue("warning", "pack.description", "Missing description", _rel(manifest_path, wiki_root)))

    components = _as_list(manifest.get("components"))
    if not components:
        issues.append(_issue("error", "pack.components", "Pack must declare at least one component",
                             _rel(manifest_path, wiki_root)))
    component_set = set(components)
    if len(component_set) != len(components):
        issues.append(_issue("error", "pack.components", "Duplicate components in pack",
                             _rel(manifest_path, wiki_root)))

    keywords = manifest.get("keywords") or {}
    if not isinstance(keywords, dict):
        issues.append(_issue("error", "pack.keywords", "keywords must be a mapping",
                             _rel(manifest_path, wiki_root)))
        keywords = {}
    for component in components:
        if component not in keywords:
            issues.append(_issue("warning", "pack.keywords", f"Missing keywords for component `{component}`",
                                 _rel(manifest_path, wiki_root)))
    for component in sorted(keywords):
        if component not in component_set:
            issues.append(_issue("error", "pack.keywords", f"Keyword component not declared: `{component}`",
                                 _rel(manifest_path, wiki_root)))

    files = manifest.get("files") or {}
    if not isinstance(files, dict):
        issues.append(_issue("error", "pack.files", "files must be a mapping",
                             _rel(manifest_path, wiki_root)))
        files = {}
    for key, rel_path in sorted(files.items()):
        if not isinstance(rel_path, str) or not rel_path:
            issues.append(_issue("error", "pack.files", f"Invalid file path for `{key}`",
                                 _rel(manifest_path, wiki_root)))
            continue
        if Path(rel_path).is_absolute() or ".." in Path(rel_path).parts:
            issues.append(_issue("error", "pack.files", f"Unsafe file path for `{key}`: {rel_path}",
                                 _rel(manifest_path, wiki_root)))
            continue
        if not (pack_dir / rel_path).is_file():
            issues.append(_issue("warning", "pack.files", f"Declared file missing for `{key}`: {rel_path}",
                                 _rel(manifest_path, wiki_root)))

    all_pack_names = set(all_pack_names)
    for conflict in _as_list(manifest.get("conflicts_with")):
        if conflict not in all_pack_names:
            issues.append(_issue("warning", "pack.conflicts_with", f"Referenced pack not found: {conflict}",
                                 _rel(manifest_path, wiki_root)))

    map_path = pack_dir / "agents" / "pipeline" / "retrieval-map.md"
    if map_path.is_file():
        rows = task_context_engine._parse_retrieval_map(map_path)  # noqa: SLF001
        for component in sorted(rows):
            if component not in component_set:
                issues.append(_issue("error", "retrieval-map.components",
                                     f"Retrieval-map component not declared in pack.yaml: `{component}`",
                                     _rel(map_path, wiki_root)))
        for component in components:
            if component not in rows:
                issues.append(_issue("warning", "retrieval-map.components",
                                     f"No retrieval-map row for component `{component}`",
                                     _rel(map_path, wiki_root)))
        for component, entries in rows.items():
            for entry in entries:
                unsafe = reject_unsafe_entry(entry)
                if unsafe:
                    issues.append(_issue("error", "retrieval-map.path",
                                         f"`{component}` has unsafe path `{entry}`: {unsafe}",
                                         _rel(map_path, wiki_root)))
                if entry.startswith("packs/") and not entry.startswith(f"packs/{pack_name}/"):
                    issues.append(_issue("error", "retrieval-map.cross-pack",
                                         f"`{component}` reads outside active pack: {entry}",
                                         _rel(map_path, wiki_root)))
    else:
        issues.append(_issue("warning", "retrieval-map.missing",
                             "Missing agents/pipeline/retrieval-map.md", rel_pack))

    return issues


def validate_packs(wiki_root: Path, pack_names: Optional[List[str]] = None) -> Dict:
    pack_dirs = _list_pack_dirs(wiki_root)
    all_pack_names = [p.name for p in pack_dirs]
    if pack_names is not None:
        requested = set(pack_names)
        pack_dirs = [p for p in pack_dirs if p.name in requested]
        for name in sorted(requested - set(all_pack_names)):
            pack_dirs.append(wiki_root / "packs" / name)

    issues: List[Dict] = []
    by_pack: Dict[str, List[Dict]] = {}
    for pack_dir in pack_dirs:
        pack_issues = _validate_pack_dir(wiki_root, pack_dir, all_pack_names)
        by_pack[pack_dir.name] = pack_issues
        issues.extend(pack_issues)

    errors = sum(1 for issue in issues if issue["severity"] == "error")
    warnings = sum(1 for issue in issues if issue["severity"] == "warning")
    status = "error" if errors else "warning" if warnings else "ok"
    return {
        "artifact_type": "contextd_pack_validation_report.v1",
        "status": status,
        "summary": {
            "packs_checked": len(pack_dirs),
            "issues": len(issues),
            "errors": errors,
            "warnings": warnings,
        },
        "issues": issues,
        "by_pack": by_pack,
    }
