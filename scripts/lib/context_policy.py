#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Policy-as-code checks for contextd task artifacts."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional


VALID_SEVERITIES = {"error", "warning", "info"}


def _read_json(path: Path) -> Optional[Dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _rules_from_payload(payload: object) -> List[Dict]:
    if isinstance(payload, list):
        return [rule for rule in payload if isinstance(rule, dict)]
    if not isinstance(payload, dict):
        return []
    raw = payload.get("rules") or payload.get("policies") or []
    return [rule for rule in raw if isinstance(rule, dict)]


def load_policy_sources(wiki_root: Path, workspace: str, packs: Iterable[str]) -> List[Dict]:
    sources: List[Dict] = []
    candidates = [
        wiki_root / "workspaces" / workspace / "policy" / "context-policy.json",
    ]
    candidates.extend(
        wiki_root / "packs" / pack / "policy" / "context-policy.json"
        for pack in packs
    )
    for path in candidates:
        if not path.is_file():
            continue
        payload = _read_json(path)
        if payload is None:
            sources.append({
                "path": _rel(path, wiki_root),
                "error": "invalid-json",
                "rules": [],
            })
            continue
        sources.append({
            "path": _rel(path, wiki_root),
            "rules": _rules_from_payload(payload),
        })
    return sources


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _as_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _matches_any(value: Optional[str], expected: object) -> bool:
    expected_values = _as_list(expected)
    if not expected_values:
        return True
    return value in expected_values


def _rule_applies(rule: Dict, artifact: Dict) -> bool:
    when = rule.get("when") or {}
    if not isinstance(when, dict):
        return True
    intent = artifact.get("intent") or {}
    if not _matches_any(intent.get("type"), when.get("intent_type") or when.get("type")):
        return False
    if not _matches_any(intent.get("workstream"), when.get("workstream")):
        return False
    components = set(intent.get("components") or [])
    expected_components = set(_as_list(when.get("components")))
    if expected_components and not components.intersection(expected_components):
        return False
    return True


def _selected_docs(artifact: Dict) -> List[Dict]:
    return [doc for doc in artifact.get("referenced_docs") or [] if isinstance(doc, dict)]


def _doc_paths(artifact: Dict) -> List[str]:
    return [str(doc.get("path") or "") for doc in _selected_docs(artifact)]


def _doc_categories(artifact: Dict) -> List[str]:
    return [str(doc.get("category") or "") for doc in _selected_docs(artifact)]


def _contracts(artifact: Dict) -> List[str]:
    contracts = set((artifact.get("intent") or {}).get("contracts_touched") or [])
    for path in _doc_paths(artifact):
        if "/contracts/" not in path:
            continue
        stem = Path(path).stem
        if stem.endswith(".contract"):
            stem = stem[:-len(".contract")]
        contracts.add(stem)
    return sorted(contracts)


def _path_matches(paths: Iterable[str], pattern: str) -> bool:
    return any(path == pattern or fnmatch.fnmatch(path, pattern) for path in paths)


def _violation(rule: Dict, source_path: str, check: str, detail: str) -> Dict:
    severity = str(rule.get("severity") or "error")
    if severity not in VALID_SEVERITIES:
        severity = "error"
    return {
        "rule_id": str(rule.get("id") or "unnamed-policy"),
        "severity": severity,
        "check": check,
        "message": str(rule.get("message") or detail),
        "detail": detail,
        "source": source_path,
    }


def _evaluate_require(rule: Dict, source_path: str, artifact: Dict) -> List[Dict]:
    require = rule.get("require") or {}
    if not isinstance(require, dict):
        return []
    out: List[Dict] = []
    categories = set(_doc_categories(artifact))
    for category in _as_list(require.get("categories")):
        if category not in categories:
            out.append(_violation(rule, source_path, "require.categories",
                                  f"Required category not selected: {category}"))
    contracts = set(_contracts(artifact))
    for contract in _as_list(require.get("contracts")):
        if contract not in contracts:
            out.append(_violation(rule, source_path, "require.contracts",
                                  f"Required contract not selected: {contract}"))
    paths = _doc_paths(artifact)
    for pattern in _as_list(require.get("docs") or require.get("path_globs")):
        if not _path_matches(paths, pattern):
            out.append(_violation(rule, source_path, "require.docs",
                                  f"Required doc not selected: {pattern}"))
    return out


def _evaluate_deny(rule: Dict, source_path: str, artifact: Dict) -> List[Dict]:
    deny = rule.get("deny") or {}
    if not isinstance(deny, dict):
        return []
    out: List[Dict] = []
    categories = set(_doc_categories(artifact))
    for category in _as_list(deny.get("categories")):
        if category in categories:
            out.append(_violation(rule, source_path, "deny.categories",
                                  f"Forbidden category selected: {category}"))
    paths = _doc_paths(artifact)
    for pattern in _as_list(deny.get("docs") or deny.get("path_globs")):
        if _path_matches(paths, pattern):
            out.append(_violation(rule, source_path, "deny.docs",
                                  f"Forbidden doc selected: {pattern}"))

    selected_docs = len(paths)
    max_selected = deny.get("max_selected_docs")
    if isinstance(max_selected, int) and selected_docs > max_selected:
        out.append(_violation(rule, source_path, "deny.max_selected_docs",
                              f"Selected docs {selected_docs} exceeds max {max_selected}"))

    max_tokens = deny.get("max_estimated_tokens")
    budget = artifact.get("budget_report") or {}
    estimated_tokens = budget.get("estimated_tokens_selected")
    if isinstance(max_tokens, int) and isinstance(estimated_tokens, int):
        if estimated_tokens > max_tokens:
            out.append(_violation(rule, source_path, "deny.max_estimated_tokens",
                                  f"Estimated tokens {estimated_tokens} exceeds max {max_tokens}"))
    return out


def evaluate_artifact(artifact: Dict, wiki_root: Path, workspace: str,
                      packs: Iterable[str]) -> Dict:
    sources = load_policy_sources(wiki_root, workspace, packs)
    violations: List[Dict] = []
    load_errors: List[Dict] = []
    evaluated_rules = 0
    skipped_rules = 0

    for source in sources:
        source_path = source.get("path") or "<unknown>"
        if source.get("error"):
            load_errors.append({
                "source": source_path,
                "severity": "error",
                "message": source["error"],
            })
            continue
        for rule in source.get("rules") or []:
            if not _rule_applies(rule, artifact):
                skipped_rules += 1
                continue
            evaluated_rules += 1
            violations.extend(_evaluate_require(rule, source_path, artifact))
            violations.extend(_evaluate_deny(rule, source_path, artifact))

    all_errors = load_errors + [v for v in violations if v["severity"] == "error"]
    warnings = [v for v in violations if v["severity"] == "warning"]
    status = "error" if all_errors else "warning" if warnings else "ok"
    return {
        "artifact_type": "contextd_governance_report.v1",
        "status": status,
        "policy_sources": [
            {"path": source.get("path"), "rule_count": len(source.get("rules") or [])}
            for source in sources
        ],
        "summary": {
            "sources": len(sources),
            "rules_evaluated": evaluated_rules,
            "rules_skipped": skipped_rules,
            "violations": len(violations),
            "errors": len(all_errors),
            "warnings": len(warnings),
            "load_errors": len(load_errors),
        },
        "violations": violations,
        "load_errors": load_errors,
    }
