#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation helpers for contextd pack APIs and retrieval maps."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pack_loader
from . import task_context_engine
from .context_security import reject_unsafe_entry


PACK_NAME_RE = re.compile(r"^pack-[a-z0-9][a-z0-9-]*$")
COMPONENT_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
VALID_SEVERITIES = {"error", "warning", "info"}
PACK_MANIFEST_VERSION = 3
SUPPORTED_PACK_MANIFEST_VERSIONS = {1, 2, 3}
PACK_STATUSES = {"stable", "beta", "experimental", "deprecated"}
PACK_CATEGORIES = {
    "agent-runtime",
    "design",
    "developer-tooling",
    "enablement",
    "engineering",
    "operations",
    "product",
    "quality",
    "security",
}
PACK_AUDIENCES = {"engineering", "product", "ba", "qc", "security", "design", "ops", "domain"}
PACK_TASK_TYPES = {"implement_feature", "fix_bug", "design", "incident", "review"}
REQUIRED_PACK_FILES_V2 = {
    "constraints",
    "coding_rules",
    "validator_rules",
    "validator_script",
    "retrieval_map",
    "prompt_overrides",
    "common_pitfalls",
}
REQUIRED_PACK_FILES_V3 = {
    "knowledge",
    "validator_script",
}


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


def _documented_validator_rule_ids(path: Path) -> List[str]:
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    ids = re.findall(
        r"`(pack-[a-z0-9-]+-[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)`",
        text,
    )
    seen = set()
    out = []
    for rule_id in ids:
        if rule_id in seen:
            continue
        seen.add(rule_id)
        out.append(rule_id)
    return out


def _implemented_validator_rule_ids(path: Path, pack_name: str) -> List[str]:
    if not path.is_file():
        return []
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    ids = re.findall(
        r'''["'](pack-[a-z0-9-]+-[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)["']''',
        source,
    )
    return sorted({rule_id for rule_id in ids if rule_id.startswith(f"{pack_name}-")})


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.is_file() else ""
    except (OSError, UnicodeDecodeError):
        return ""


def _knowledge_sections(text: str) -> Dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    sections: Dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1).strip()] = text[match.start():end].strip()
    return sections


def _validate_pack_knowledge(wiki_root: Path, pack_dir: Path, manifest: Dict,
                             components: List[str], files: Dict) -> List[Dict]:
    issues: List[Dict] = []
    pack_name = pack_dir.name
    knowledge_rel = str(files.get("knowledge") or "knowledge.md")
    knowledge_path = pack_dir / knowledge_rel
    rel = _rel(knowledge_path, wiki_root)
    text = _read_text(knowledge_path)
    if not text:
        return [_issue("error", "pack.knowledge", "Manifest v3 requires a readable knowledge.md", rel)]

    heading_list = re.findall(r"^##\s+(.+?)\s*$", text, re.MULTILINE)
    heading_counts = {title: heading_list.count(title) for title in set(heading_list)}
    sections = _knowledge_sections(text)
    if heading_counts.get("Global Principles", 0) != 1:
        issues.append(_issue(
            "error", "pack.knowledge.global",
            "knowledge.md must define exactly one `## Global Principles`", rel,
        ))
    required_subsections = {
        "Mental Model",
        "Standards",
        "Failure Signals",
        "Evidence And Stop Conditions",
    }
    for component in components:
        title = f"Component: {component}"
        body = sections.get(title, "")
        if heading_counts.get(title, 0) != 1:
            issues.append(_issue(
                "error", "pack.knowledge.component",
                f"knowledge.md must define exactly one `## {title}`", rel,
            ))
            continue
        headings = set(re.findall(r"^###\s+(.+?)\s*$", body, re.MULTILINE))
        missing = sorted(required_subsections - headings)
        if missing:
            issues.append(_issue(
                "error", "pack.knowledge.component",
                f"`{component}` is missing subsections: {', '.join(missing)}", rel,
            ))

    declared_titles = {f"Component: {component}" for component in components}
    for title in sorted(
        item for item in heading_counts
        if item.startswith("Component:") and item not in declared_titles
    ):
        issues.append(_issue(
            "error", "pack.knowledge.component",
            f"knowledge.md component is not declared in pack.yaml: `{title}`", rel,
        ))

    stable_ids = set(re.findall(
        rf"`({re.escape(pack_name)}-[a-z0-9][a-z0-9-]*)`",
        text,
    ))
    if not stable_ids:
        issues.append(_issue(
            "error", "pack.knowledge.ids",
            f"knowledge.md must expose stable `{pack_name}-...` standard IDs", rel,
        ))
    legacy_ids: Dict[str, set] = {}
    legacy_agents = pack_dir / "agents"
    if legacy_agents.is_dir():
        for legacy_path in sorted(legacy_agents.rglob("*.md")):
            ids = set(re.findall(
                rf"`({re.escape(pack_name)}-[a-z0-9][a-z0-9-]*)`",
                _read_text(legacy_path),
            ))
            if ids:
                legacy_ids[_rel(legacy_path, wiki_root)] = ids
    for legacy_path, ids in legacy_ids.items():
        for rule_id in sorted(ids - stable_ids):
            issues.append(_issue(
                "error", "pack.knowledge.adapter-drift",
                f"Legacy adapter defines an ID absent from canonical knowledge: `{rule_id}`",
                legacy_path,
            ))
    validator_script = pack_dir / str(files.get("validator_script") or "scripts/rules.py")
    implemented = set(_implemented_validator_rule_ids(validator_script, pack_name))
    for rule_id in sorted(implemented - stable_ids):
        issues.append(_issue(
            "error", "pack.validator.parity",
            f"Implemented rule is not documented in knowledge.md: `{rule_id}`",
            _rel(validator_script, wiki_root),
        ))
    return issues


def _validate_manifest_quality(wiki_root: Path, pack_dir: Path, manifest: Dict,
                               components: List[str], keywords: Dict,
                               files: Dict, manifest_version: int) -> List[Dict]:
    """Validate manifest v2/v3 authoring quality without weakening v2."""
    issues: List[Dict] = []
    manifest_path = pack_dir / "pack.yaml"
    rel_manifest = _rel(manifest_path, wiki_root)
    pack_name = pack_dir.name

    version = str(manifest.get("version") or "")
    if not SEMVER_RE.fullmatch(version):
        issues.append(_issue("error", "pack.version", "version must be semantic versioning (MAJOR.MINOR.PATCH)", rel_manifest))

    description = str(manifest.get("description") or "").strip()
    if len(description) < 40:
        issues.append(_issue("error", "pack.description", "description must state a concrete scope (at least 40 characters)", rel_manifest))

    status = str(manifest.get("status") or "")
    if status not in PACK_STATUSES:
        issues.append(_issue("error", "pack.status", f"status must be one of: {', '.join(sorted(PACK_STATUSES))}", rel_manifest))

    category = str(manifest.get("category") or "")
    if category not in PACK_CATEGORIES:
        issues.append(_issue("error", "pack.category", f"category must be one of: {', '.join(sorted(PACK_CATEGORIES))}", rel_manifest))

    reviewed_on = str(manifest.get("reviewed_on") or "")
    try:
        reviewed_date = date.fromisoformat(reviewed_on)
    except ValueError:
        issues.append(_issue("error", "pack.reviewed_on", "reviewed_on must be an ISO date (YYYY-MM-DD)", rel_manifest))
    else:
        if reviewed_date > date.today():
            issues.append(_issue("error", "pack.reviewed_on", "reviewed_on cannot be in the future", rel_manifest))

    for field, allowed in (("audiences", PACK_AUDIENCES), ("task_types", PACK_TASK_TYPES)):
        values = _as_list(manifest.get(field))
        if not values:
            issues.append(_issue("error", f"pack.{field}", f"{field} must contain at least one value", rel_manifest))
            continue
        if len(values) != len(set(values)):
            issues.append(_issue("error", f"pack.{field}", f"{field} contains duplicate values", rel_manifest))
        unknown = sorted(set(values) - allowed)
        if unknown:
            issues.append(_issue("error", f"pack.{field}", f"unsupported {field}: {', '.join(unknown)}", rel_manifest))

    scopes: Dict[str, List[str]] = {}
    for field in ("scope_includes", "scope_excludes"):
        values = [value.strip() for value in _as_list(manifest.get(field)) if value.strip()]
        scopes[field] = values
        if not values:
            issues.append(_issue("error", f"pack.{field}", f"{field} must define at least one boundary", rel_manifest))
        elif len(values) != len(set(value.casefold() for value in values)):
            issues.append(_issue("error", f"pack.{field}", f"{field} contains duplicate boundaries", rel_manifest))
    overlap = sorted(set(value.casefold() for value in scopes["scope_includes"]) &
                     set(value.casefold() for value in scopes["scope_excludes"]))
    if overlap:
        issues.append(_issue("error", "pack.scope", "scope_includes and scope_excludes overlap", rel_manifest))

    for component in components:
        if not COMPONENT_RE.fullmatch(component):
            issues.append(_issue("error", "pack.components", f"Invalid component slug: `{component}`", rel_manifest))
        values = [value.strip() for value in _as_list(keywords.get(component)) if value.strip()]
        normalized = [value.casefold() for value in values]
        if len(values) < 3:
            issues.append(_issue("error", "pack.keywords", f"Component `{component}` needs at least three routing keywords", rel_manifest))
        if len(normalized) != len(set(normalized)):
            issues.append(_issue("error", "pack.keywords", f"Component `{component}` has duplicate routing keywords", rel_manifest))

    keyword_owners: Dict[str, List[str]] = {}
    for component, values in keywords.items():
        for value in _as_list(values):
            normalized = value.strip().casefold()
            if normalized:
                keyword_owners.setdefault(normalized, []).append(str(component))
    for keyword, owners in sorted(keyword_owners.items()):
        if len(set(owners)) > 1:
            issues.append(_issue("error", "pack.keywords.ambiguous", f"Routing keyword `{keyword}` is owned by multiple components: {', '.join(sorted(set(owners)))}", rel_manifest))

    required_files = (
        REQUIRED_PACK_FILES_V3 if manifest_version == 3 else REQUIRED_PACK_FILES_V2
    )
    missing_file_keys = sorted(required_files - set(files))
    if missing_file_keys:
        issues.append(_issue(
            "error", "pack.files",
            f"manifest v{manifest_version} requires file declarations: {', '.join(missing_file_keys)}",
            rel_manifest,
        ))

    readme_path = pack_dir / "README.md"
    readme = _read_text(readme_path)
    required_sections = {
        "activation": r"^##\s+(?:when to enable|khi nào bật)",
        "boundary": r"^##\s+(?:when not to enable|scope boundary|pack này không phù hợp)",
        "retrieval": r"^##\s+.*retrieval",
        "verification": r"^##\s+(?:verification|kiểm chứng)",
    }
    if not readme:
        issues.append(_issue("error", "pack.readme", "README.md is required", _rel(readme_path, wiki_root)))
    else:
        for section, pattern in required_sections.items():
            if not re.search(pattern, readme, re.MULTILINE | re.IGNORECASE):
                issues.append(_issue("error", "pack.readme", f"README.md is missing the `{section}` section", _rel(readme_path, wiki_root)))

    if manifest_version == 3:
        issues.extend(_validate_pack_knowledge(
            wiki_root, pack_dir, manifest, components, files,
        ))
    else:
        constraints_path = pack_dir / "agents" / "constraints.md"
        constraints = _read_text(constraints_path)
        stable_ids = re.findall(rf"`({re.escape(pack_name)}-[a-z0-9][a-z0-9-]*)`", constraints)
        if not stable_ids:
            issues.append(_issue("error", "pack.constraints.ids", f"constraints.md must expose stable `{pack_name}-...` rule-group IDs", _rel(constraints_path, wiki_root)))

        pitfalls_path = pack_dir / "agents" / "common-pitfalls.md"
        pitfalls = _read_text(pitfalls_path)
        pitfall_count = len(re.findall(r"^##\s+P[0-9]{2}\b", pitfalls, re.MULTILINE))
        if pitfall_count < 5:
            issues.append(_issue("error", "pack.pitfalls", "common-pitfalls.md must document at least five numbered pitfalls", _rel(pitfalls_path, wiki_root)))

        validator_rules_path = pack_dir / "agents" / "pipeline" / "validator-rules.md"
        validator_script_path = pack_dir / str(files.get("validator_script") or "scripts/rules.py")
        documented = set(_documented_validator_rule_ids(validator_rules_path))
        implemented = set(_implemented_validator_rule_ids(validator_script_path, pack_name))
        for rule_id in sorted(documented - implemented):
            issues.append(_issue("error", "pack.validator.parity", f"Documented rule is not implemented: `{rule_id}`", _rel(validator_rules_path, wiki_root)))
        for rule_id in sorted(implemented - documented):
            issues.append(_issue("error", "pack.validator.parity", f"Implemented rule is not documented: `{rule_id}`", _rel(validator_script_path, wiki_root)))
        pitfall_rule_refs = set(_documented_validator_rule_ids(pitfalls_path))
        for rule_id in sorted(pitfall_rule_refs - implemented):
            issues.append(_issue(
                "error",
                "pack.pitfalls.rule_ref",
                f"Common pitfall references a non-existent Layer-1 rule: `{rule_id}`",
                _rel(pitfalls_path, wiki_root),
            ))

    return issues


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

    manifest_version = manifest.get("manifest_version")
    if manifest_version is None or manifest_version == 1:
        issues.append(_issue(
            "info",
            "pack.manifest_version",
            "Legacy pack manifest accepted; migrate to manifest_version 3 for canonical knowledge checks",
            _rel(manifest_path, wiki_root),
        ))
    elif manifest_version not in SUPPORTED_PACK_MANIFEST_VERSIONS:
        issues.append(_issue(
            "error",
            "pack.manifest_version",
            (
                f"Unsupported manifest_version `{manifest_version}`; runtime supports "
                + ", ".join(str(item) for item in sorted(SUPPORTED_PACK_MANIFEST_VERSIONS))
            ),
            _rel(manifest_path, wiki_root),
        ))

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

    validator_rules_path = pack_dir / "agents" / "pipeline" / "validator-rules.md"
    if _documented_validator_rule_ids(validator_rules_path) and not files.get("validator_script"):
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

    map_path = pack_dir / str(
        files.get("retrieval_map") or "agents/pipeline/retrieval-map.md"
    )
    if manifest_version == 3:
        rows = task_context_engine._manifest_retrieval_rows(manifest)  # noqa: SLF001
        retrieval_path = manifest_path
        if not rows:
            issues.append(_issue(
                "error", "pack.retrieval",
                "Manifest v3 requires a non-empty retrieval mapping",
                _rel(manifest_path, wiki_root),
            ))
        if map_path.is_file():
            compatibility_rows = task_context_engine._parse_retrieval_map(map_path)  # noqa: SLF001
            if compatibility_rows != rows:
                issues.append(_issue(
                    "error", "retrieval-map.compatibility-drift",
                    "Legacy retrieval-map.md diverges from canonical pack.yaml#retrieval",
                    _rel(map_path, wiki_root),
                ))
    elif map_path.is_file():
        rows = task_context_engine._parse_retrieval_map(map_path)  # noqa: SLF001
        retrieval_path = map_path
    else:
        rows = {}
        retrieval_path = map_path
        issues.append(_issue("warning", "retrieval-map.missing",
                             "Missing agents/pipeline/retrieval-map.md", rel_pack))

    if rows:
        for component in sorted(rows):
            if component not in component_set:
                issues.append(_issue("error", "retrieval-map.components",
                                     f"Retrieval-map component not declared in pack.yaml: `{component}`",
                                     _rel(retrieval_path, wiki_root)))
        for component in components:
            if component not in rows:
                issues.append(_issue("warning", "retrieval-map.components",
                                     f"No retrieval-map row for component `{component}`",
                                     _rel(retrieval_path, wiki_root)))
        for component, entries in rows.items():
            for entry in entries:
                unsafe = reject_unsafe_entry(entry)
                if unsafe:
                    issues.append(_issue("error", "retrieval-map.path",
                                         f"`{component}` has unsafe path `{entry}`: {unsafe}",
                                         _rel(retrieval_path, wiki_root)))
                if entry.startswith("packs/") and not entry.startswith(f"packs/{pack_name}/"):
                    issues.append(_issue("error", "retrieval-map.cross-pack",
                                         f"`{component}` reads outside active pack: {entry}",
                                         _rel(retrieval_path, wiki_root)))

    if manifest_version in {2, 3}:
        issues.extend(_validate_manifest_quality(
            wiki_root, pack_dir, manifest, components, keywords, files,
            manifest_version,
        ))

    return issues


def _cross_pack_routing_issues(wiki_root: Path, all_pack_dirs: Iterable[Path],
                               selected_names: Iterable[str]) -> Dict[str, List[Dict]]:
    selected = set(selected_names)
    keyword_owners: Dict[str, set] = {}
    component_owners: Dict[str, set] = {}
    for pack_dir in all_pack_dirs:
        manifest = _load_manifest(pack_dir)
        if not manifest:
            continue
        for component in _as_list(manifest.get("components")):
            component_owners.setdefault(component, set()).add(pack_dir.name)
        keywords = manifest.get("keywords") or {}
        if not isinstance(keywords, dict):
            continue
        for component, values in keywords.items():
            for value in _as_list(values):
                normalized = value.strip().casefold()
                if normalized:
                    keyword_owners.setdefault(normalized, set()).add(
                        (pack_dir.name, str(component))
                    )

    by_pack: Dict[str, List[Dict]] = {name: [] for name in selected}
    for component, owners in sorted(component_owners.items()):
        if len(owners) < 2:
            continue
        rendered = ", ".join(sorted(owners))
        for pack_name in sorted(owners & selected):
            by_pack[pack_name].append(_issue(
                "error", "pack.components.cross_pack_ambiguous",
                f"Component `{component}` is declared by multiple packs: {rendered}",
                f"packs/{pack_name}/pack.yaml",
            ))
    for keyword, owners in sorted(keyword_owners.items()):
        owner_packs = {pack_name for pack_name, _ in owners}
        if len(owner_packs) < 2:
            continue
        rendered = ", ".join(
            f"{pack_name}:{component}" for pack_name, component in sorted(owners)
        )
        for pack_name in sorted(owner_packs & selected):
            by_pack[pack_name].append(_issue(
                "error", "pack.keywords.cross_pack_ambiguous",
                f"Routing keyword `{keyword}` is owned across packs: {rendered}",
                f"packs/{pack_name}/pack.yaml",
            ))
    return by_pack


def validate_packs(wiki_root: Path, pack_names: Optional[List[str]] = None) -> Dict:
    all_pack_dirs = _list_pack_dirs(wiki_root)
    pack_dirs = list(all_pack_dirs)
    all_pack_names = [p.name for p in all_pack_dirs]
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

    cross_pack = _cross_pack_routing_issues(
        wiki_root,
        all_pack_dirs,
        [pack_dir.name for pack_dir in pack_dirs],
    )
    for pack_name, pack_issues in cross_pack.items():
        by_pack.setdefault(pack_name, []).extend(pack_issues)
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
