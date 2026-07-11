#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation helpers for contextd pack APIs and retrieval maps."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pack_loader
import task_context_engine
import context_security


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
    return context_security.root_relative_posix(path, root)


def _load_manifest(pack_dir: Path) -> Dict:
    try:
        path = context_security.confined_child(
            pack_dir, "pack.yaml", "pack manifest", allow_symlink=False
        )
        return pack_loader._parse_simple_yaml(path.read_text(encoding="utf-8"))  # noqa: SLF001
    except (OSError, UnicodeDecodeError, ValueError):
        return {}


def _list_pack_dirs(wiki_root: Path) -> tuple[List[Path], List[Dict]]:
    issues: List[Dict] = []
    try:
        packs_dir = context_security.confined_child(
            wiki_root, "packs", "packs root", allow_symlink=False
        )
    except ValueError as exc:
        return [], [_issue("error", "pack.root", str(exc), "packs")]
    if not packs_dir.exists():
        return [], issues
    if not packs_dir.is_dir():
        return [], [_issue("error", "pack.root", "packs must be a directory", "packs")]

    pack_dirs: List[Path] = []
    for candidate in sorted(packs_dir.iterdir()):
        if not candidate.is_dir():
            continue
        safe_name, name_error = context_security.validate_context_name(
            candidate.name, "pack"
        )
        if name_error or safe_name is None:
            issues.append(_issue(
                "error",
                "pack.name",
                f"Unsafe pack directory name `{candidate.name}`: {name_error}",
                "packs/<invalid>",
            ))
            continue
        try:
            safe_dir = context_security.pack_dir(wiki_root, safe_name)
        except ValueError as exc:
            issues.append(_issue(
                "error",
                "pack.path",
                f"Unsafe pack directory `{safe_name}`: {exc}",
                f"packs/{safe_name}",
            ))
            continue
        if safe_dir.is_dir():
            pack_dirs.append(safe_dir)
    return pack_dirs, issues


def _as_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _documented_validator_rule_ids(path: Path) -> List[str]:
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    ids = re.findall(r"`(pack-[a-z0-9-]+-[a-z0-9][a-z0-9-]*)`", text)
    seen = set()
    out = []
    for rule_id in ids:
        if rule_id in seen:
            continue
        seen.add(rule_id)
        out.append(rule_id)
    return out


def _validate_pack_dir(wiki_root: Path, pack_dir: Path,
                       all_pack_names: Iterable[str]) -> List[Dict]:
    issues: List[Dict] = []
    pack_name = pack_dir.name
    rel_pack = _rel(pack_dir, wiki_root)
    try:
        manifest_path = context_security.confined_child(
            pack_dir, "pack.yaml", "pack manifest", allow_symlink=False
        )
    except ValueError as exc:
        return [_issue(
            "error", "pack.manifest", f"Unsafe pack.yaml: {exc}", f"{rel_pack}/pack.yaml"
        )]
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
    if not PACK_NAME_RE.fullmatch(pack_name):
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
        try:
            declared_path = context_security.confined_child(
                pack_dir,
                rel_path,
                f"pack file `{key}`",
                allow_symlink=False,
            )
        except ValueError as exc:
            issues.append(_issue(
                "error",
                "pack.files",
                f"Unsafe file path for `{key}`: {rel_path} ({exc})",
                _rel(manifest_path, wiki_root),
            ))
            continue
        if key == "validator_script" and declared_path.suffix.lower() != ".py":
            issues.append(_issue(
                "error",
                "pack.validator_script",
                f"validator_script must be a .py file: {rel_path}",
                _rel(manifest_path, wiki_root),
            ))
            continue
        if not declared_path.is_file():
            issues.append(_issue("warning", "pack.files", f"Declared file missing for `{key}`: {rel_path}",
                                 _rel(manifest_path, wiki_root)))

    try:
        validator_rules_path = context_security.confined_child(
            pack_dir,
            "agents/pipeline/validator-rules.md",
            "validator rules documentation",
            allow_symlink=False,
        )
    except ValueError as exc:
        validator_rules_path = None
        issues.append(_issue(
            "error",
            "pack.validator_rules",
            f"Unsafe validator-rules.md: {exc}",
            f"{rel_pack}/agents/pipeline/validator-rules.md",
        ))
    if (
        validator_rules_path is not None
        and _documented_validator_rule_ids(validator_rules_path)
        and not files.get("validator_script")
    ):
        issues.append(_issue(
            "warning",
            "pack.validator_script",
            (
                "validator-rules.md documents layer-1 rule IDs but "
                "pack.yaml does not declare files.validator_script"
            ),
            _rel(manifest_path, wiki_root),
        ))

    all_pack_names = set(all_pack_names)
    for conflict in _as_list(manifest.get("conflicts_with")):
        if conflict not in all_pack_names:
            issues.append(_issue("warning", "pack.conflicts_with", f"Referenced pack not found: {conflict}",
                                 _rel(manifest_path, wiki_root)))

    try:
        map_path = context_security.confined_child(
            pack_dir,
            "agents/pipeline/retrieval-map.md",
            "retrieval map",
            allow_symlink=False,
        )
    except ValueError as exc:
        map_path = None
        issues.append(_issue(
            "error",
            "retrieval-map.path",
            f"Unsafe retrieval-map.md: {exc}",
            f"{rel_pack}/agents/pipeline/retrieval-map.md",
        ))
    if map_path is not None and map_path.is_file():
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
                unsafe = context_security.reject_unsafe_entry(entry)
                if unsafe:
                    issues.append(_issue("error", "retrieval-map.path",
                                         f"`{component}` has unsafe path `{entry}`: {unsafe}",
                                         _rel(map_path, wiki_root)))
                if entry.startswith("packs/") and not entry.startswith(f"packs/{pack_name}/"):
                    issues.append(_issue("error", "retrieval-map.cross-pack",
                                         f"`{component}` reads outside active pack: {entry}",
                                         _rel(map_path, wiki_root)))
    elif map_path is not None:
        issues.append(_issue("warning", "retrieval-map.missing",
                             "Missing agents/pipeline/retrieval-map.md", rel_pack))

    return issues


def validate_packs(wiki_root: Path, pack_names: Optional[List[str]] = None) -> Dict:
    root = Path(wiki_root).resolve()
    catalog_dirs, catalog_issues = _list_pack_dirs(root)
    all_pack_names = [path.name for path in catalog_dirs]
    issues: List[Dict] = list(catalog_issues if pack_names is None else [])
    by_pack: Dict[str, List[Dict]] = {}

    if pack_names is None:
        pack_dirs = catalog_dirs
    else:
        pack_dirs = []
        for raw_name in sorted(set(pack_names), key=str):
            safe_name, name_error = context_security.validate_context_name(
                raw_name, "pack"
            )
            if (
                name_error
                or safe_name is None
                or not PACK_NAME_RE.fullmatch(safe_name)
            ):
                requested_issue = _issue(
                    "error",
                    "pack.name",
                    f"Invalid requested pack `{raw_name}`: "
                    f"{name_error or 'must match `pack-{slug}`'}",
                    "packs/<invalid>",
                )
                key = str(raw_name)
                by_pack[key] = [requested_issue]
                issues.append(requested_issue)
                continue
            try:
                requested_dir = context_security.pack_dir(root, safe_name)
            except ValueError as exc:
                requested_issue = _issue(
                    "error",
                    "pack.path",
                    f"Unsafe requested pack `{safe_name}`: {exc}",
                    f"packs/{safe_name}",
                )
                by_pack[safe_name] = [requested_issue]
                issues.append(requested_issue)
                continue
            pack_dirs.append(requested_dir)

    for pack_dir in pack_dirs:
        pack_issues = _validate_pack_dir(root, pack_dir, all_pack_names)
        by_pack[pack_dir.name] = pack_issues
        issues.extend(pack_issues)

    errors = sum(1 for issue in issues if issue["severity"] == "error")
    warnings = sum(1 for issue in issues if issue["severity"] == "warning")
    status = "error" if errors else "warning" if warnings else "ok"
    return {
        "artifact_type": "contextd_pack_validation_report.v1",
        "status": status,
        "summary": {
            "packs_checked": len(by_pack),
            "issues": len(issues),
            "errors": errors,
            "warnings": warnings,
        },
        "issues": issues,
        "by_pack": by_pack,
    }
