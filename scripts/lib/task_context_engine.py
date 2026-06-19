#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic task-context artifact builder for contextd.

The JSON artifact is the source of truth. Markdown is a render target.
Retrieval is deterministic and file-backed; fuzzy search/RAG remains advisory.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import context_policy
from context_security import block_reason, is_relative_to, redact_text, reject_unsafe_entry


INTENT_KEYWORDS = {
    "implement_feature": [
        "add", "implement", "create", "build", "write", "support", "enable",
        "introduce", "new feature", "feature", "endpoint", "api", "consumer",
        "producer", "service", "handler", "controller",
    ],
    "fix_bug": [
        "fix", "bug", "broken", "breaks", "error", "crash", "fails", "failing",
        "not working", "doesn't work", "exception", "regression", "issue",
    ],
    "design": [
        "design", "architecture", "approach", "how should", "structure",
        "pattern", "refactor", "restructure", "organize", "strategy", "proposal",
    ],
    "incident": [
        "incident", "outage", "down", "spike", "latency", "error rate",
        "production", "live", "oncall", "alert", "paged",
    ],
    "review": [
        "review", "pr", "pull request", "audit", "check", "verify", "assess",
        "code review", "walkthrough", "sign-off",
    ],
}

WORKSTREAM_KEYWORDS = {
    "product": [
        "product", "brief", "prd", "okr", "roadmap", "persona", "journey",
        "metric", "customer", "feature request",
    ],
    "business_analysis": [
        "requirement", "business requirement", "acceptance criteria", "user story",
        "gherkin", "stakeholder", "process map", "workflow map", "brd",
    ],
    "quality": [
        "test case", "test plan", "qa", "qc", "quality", "defect", "bug triage",
        "regression", "release gate", "performance", "benchmark", "profiling",
    ],
    "security": [
        "security", "threat", "vulnerability", "pentest", "attack surface",
        "risk rating", "control", "authz", "secret",
    ],
    "design": [
        "design system", "accessibility", "a11y", "user flow", "wireframe",
        "ux", "ui", "prototype", "copy", "microcopy",
    ],
    "ops": [
        "incident", "runbook", "oncall", "outage", "alert", "rollback",
        "restore", "release", "deploy", "team sync",
    ],
    "domain_research": [
        "research", "interview", "regulation", "policy", "evidence", "source",
        "customer signal", "analytics", "support ticket",
    ],
}

PACK_WORKSTREAMS = {
    "pack-product": "product",
    "pack-ba": "business_analysis",
    "pack-qc": "quality",
    "pack-security": "security",
    "pack-ui-ux": "design",
    "pack-dba": "ops",
    "pack-solo-builder": "domain_research",
}

AUDIENCE_BY_WORKSTREAM = {
    "engineering": "engineering",
    "product": "product",
    "business_analysis": "ba",
    "quality": "qc",
    "security": "security",
    "design": "design",
    "ops": "ops",
    "domain_research": "domain",
}

SECTION_POLICY = {
    "contract": ["all"],
    "pattern": ["Flow", "Default Config", "Failure Strategy", "Implementation Rules", "Rules"],
    "project": ["Purpose", "Flow", "Config Overrides", "Failure"],
    "service": ["Purpose", "Flow", "Config Overrides", "Failure"],
    "domain": ["States", "Transitions", "Business Rules"],
    "workflow": ["States", "Transitions", "Business Rules"],
    "architecture": ["all"],
    "decision": ["Status", "Context", "Decision", "Consequences"],
    "runbook": ["Symptoms", "Diagnosis", "Mitigation", "Rollback"],
    "product": ["Problem", "Target User", "Success Metric", "Acceptance Criteria"],
    "requirement": ["Actor", "Trigger", "Business Outcome", "Acceptance Criteria"],
    "design": ["Flow", "Accessibility", "UX Writing", "Edge Cases"],
    "quality": ["Evidence", "Scope", "Risk", "Decision"],
    "evidence": ["Verified Facts", "Open Questions", "Source Summary"],
    "pitfalls": ["all"],
    "common-pitfalls": ["all"],
    "workspace-profile": ["all"],
    "engine-guidance": ["all"],
    "engine-rule": ["all"],
    "pack-rule": ["all"],
}

CATEGORY_BUDGETS = {
    "contract": 2,
    "pattern": 2,
    "project": 2,
    "service": 2,
    "domain": 1,
    "workflow": 1,
    "architecture": 1,
    "decision": 2,
    "runbook": 2,
    "product": 2,
    "requirement": 2,
    "design": 2,
    "quality": 2,
    "evidence": 2,
    "pitfalls": 3,
    "common-pitfalls": 3,
    "workspace-profile": 1,
    "engine-guidance": 1,
    "engine-rule": 2,
    "pack-rule": 3,
}

PRIORITY = {
    "contract": 0,
    "pattern": 1,
    "project": 2,
    "service": 2,
    "domain": 3,
    "workflow": 3,
    "architecture": 4,
    "decision": 4,
    "runbook": 2,
    "product": 2,
    "requirement": 2,
    "design": 2,
    "quality": 2,
    "evidence": 3,
    "pitfalls": 1,
    "common-pitfalls": 1,
    "workspace-profile": 2,
    "engine-guidance": 2,
    "engine-rule": 1,
    "pack-rule": 1,
}

WORKSTREAM_BUDGETS = {
    "engineering": CATEGORY_BUDGETS,
    "product": {
        **CATEGORY_BUDGETS,
        "product": 3,
        "requirement": 2,
        "domain": 1,
        "decision": 1,
        "contract": 1,
        "pattern": 1,
    },
    "business_analysis": {
        **CATEGORY_BUDGETS,
        "requirement": 3,
        "domain": 2,
        "product": 1,
        "contract": 1,
        "runbook": 1,
    },
    "quality": {
        **CATEGORY_BUDGETS,
        "quality": 2,
        "evidence": 2,
        "runbook": 2,
        "project": 1,
        "contract": 1,
    },
    "security": {
        **CATEGORY_BUDGETS,
        "contract": 2,
        "runbook": 2,
        "project": 1,
        "architecture": 1,
        "decision": 1,
    },
    "design": {
        **CATEGORY_BUDGETS,
        "design": 3,
        "product": 1,
        "requirement": 1,
        "domain": 1,
        "decision": 1,
    },
    "ops": {
        **CATEGORY_BUDGETS,
        "runbook": 3,
        "evidence": 2,
        "project": 1,
        "architecture": 1,
    },
    "domain_research": {
        **CATEGORY_BUDGETS,
        "evidence": 3,
        "domain": 2,
        "product": 1,
        "requirement": 1,
        "design": 1,
    },
}

WORKSTREAM_PRIORITY = {
    "engineering": {
        "priority": ["contracts", "patterns", "project_docs", "domain_knowledge"],
        "context_goal": "prepare_code_change",
    },
    "product": {
        "priority": [
            "product_context", "requirements", "domain_knowledge",
            "source_evidence", "contracts", "patterns",
        ],
        "context_goal": "shape_product_decision",
    },
    "business_analysis": {
        "priority": [
            "requirements", "domain_knowledge", "product_context",
            "contracts", "operational_runbooks",
        ],
        "context_goal": "clarify_testable_requirements",
    },
    "quality": {
        "priority": [
            "quality_evidence", "operational_runbooks", "requirements",
            "project_docs", "contracts",
        ],
        "context_goal": "support_quality_decision",
    },
    "security": {
        "priority": [
            "contracts", "operational_runbooks", "source_evidence",
            "project_docs", "architecture",
        ],
        "context_goal": "support_security_review",
    },
    "design": {
        "priority": [
            "design_context", "product_context", "requirements",
            "domain_knowledge", "source_evidence",
        ],
        "context_goal": "shape_user_experience",
    },
    "ops": {
        "priority": [
            "operational_runbooks", "source_evidence", "project_docs",
            "architecture", "contracts",
        ],
        "context_goal": "support_operational_response",
    },
    "domain_research": {
        "priority": [
            "source_evidence", "domain_knowledge", "requirements",
            "product_context", "design_context",
        ],
        "context_goal": "ground_domain_understanding",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> Optional[str]:
    text = _read(path)
    return _sha256_text(text) if text is not None else None


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def detect_intent(task: str) -> str:
    task_lower = task.lower()
    scores: Dict[str, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in task_lower)
        if score:
            scores[intent] = score
    if not scores:
        return "implement_feature"
    return max(scores, key=scores.get)


def _parse_pack_keywords(pack_yaml: Path) -> Dict[str, List[str]]:
    text = _read(pack_yaml)
    if text is None:
        return {}
    out: Dict[str, List[str]] = {}
    in_keywords = False
    for raw in text.splitlines():
        if re.match(r"^keywords\s*:\s*$", raw):
            in_keywords = True
            continue
        if in_keywords and raw and not raw.startswith((" ", "\t")):
            break
        if not in_keywords:
            continue
        m = re.match(r"^\s+([a-z][\w\-]*)\s*:\s*\[(.*?)\]", raw)
        if not m:
            continue
        items = [x.strip().strip("'\"") for x in m.group(2).split(",")]
        out[m.group(1)] = [x for x in items if x]
    return out


def detect_components(task: str, wiki_root: Path, packs: List[str]) -> List[str]:
    task_lower = task.lower()
    components: set[str] = set()
    for pack_name in packs:
        keywords = _parse_pack_keywords(wiki_root / "packs" / pack_name / "pack.yaml")
        for component, words in keywords.items():
            if any(word.lower() in task_lower for word in words):
                components.add(component)
    return sorted(components)


def detect_scope(task: str, wiki_root: Path, workspace: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect domain + project by matching directory names in task text."""
    task_lower = task.lower()
    ws_dir = wiki_root / "workspaces" / workspace

    def match_dir(parent: Path) -> Optional[str]:
        if not parent.is_dir():
            return None
        for path in sorted(p for p in parent.iterdir() if p.is_dir()):
            name = path.name.lower()
            variants = {name, name.replace("-", " "), name.replace("_", " ")}
            if any(v and v in task_lower for v in variants):
                return path.name
        return None

    return match_dir(ws_dir / "domains"), match_dir(ws_dir / "projects")


def detect_workstream(task: str, packs: List[str], components: List[str]) -> str:
    task_lower = task.lower()
    scores: Dict[str, int] = {}
    for workstream, keywords in WORKSTREAM_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in task_lower)
        if score:
            scores[workstream] = scores.get(workstream, 0) + score

    for pack_name in packs:
        workstream = PACK_WORKSTREAMS.get(pack_name)
        if not workstream:
            continue
        if components:
            scores[workstream] = scores.get(workstream, 0) + 2
        else:
            scores[workstream] = scores.get(workstream, 0) + 1

    if not scores:
        return "engineering"
    return max(scores, key=scores.get)


def _strip_inline_note(value: str) -> str:
    return re.sub(r"\s+\([^)]*\)\s*$", "", value).strip()


def _parse_retrieval_map(path: Path) -> Dict[str, List[str]]:
    text = _read(path)
    if text is None:
        return {}
    rows: Dict[str, List[str]] = {}
    in_component_table = False
    seen_data = False
    for raw in text.splitlines():
        line = raw.strip()
        if not in_component_table:
            if line.startswith("|") and "Component" in line:
                in_component_table = True
            continue
        if not line.startswith("|"):
            if seen_data:
                break
            continue
        if "Component" in line or re.match(r"^\|[-:\s|]+$", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        component = re.sub(r"`", "", cells[0]).strip()
        component = re.sub(r"\s+\(.*?\)$", "", component)
        docs_cell = cells[1]
        docs = []
        for item in re.split(r"\s*,\s*|\s*;\s*", docs_cell):
            item = _strip_inline_note(item.strip().strip("`"))
            if item:
                docs.append(item)
        if component and docs:
            seen_data = True
            rows[component] = docs
    return rows


def _category_from_path(path: Path, rel: str, fallback: str = "project") -> str:
    parts = rel.split("/")
    path_text = rel.lower()
    if "/platform/contracts/" in path_text or "/contracts/" in path_text:
        return "contract"
    if "/platform/patterns/" in path_text or "/patterns/" in path_text:
        return "pattern"
    if "/runbooks/" in path_text:
        return "runbook"
    if "/product/" in path_text or path_text.startswith("product/"):
        return "product"
    if "/requirements/" in path_text or any(
        token in path.name.lower() for token in ("requirement", "brd", "story", "acceptance")
    ):
        return "requirement"
    if "/platform/design/" in path_text or "/design/" in path_text or path_text.startswith("design/"):
        return "design"
    if any(seg in parts for seg in ("quality", "test", "tests", "release")):
        return "quality"
    if "/evidence/" in path_text:
        return "evidence"
    if "/domains/" in path_text:
        return "domain"
    if "/platform/architecture/" in path_text:
        return "architecture"
    if "/decisions/" in path_text:
        return "decision"
    if "/services/" in path_text:
        return "service"
    return fallback


def _safe_evidence_files(path: Path) -> List[Path]:
    if path.is_file():
        return [path] if _is_safe_evidence_doc(path) else []
    if not path.is_dir():
        return []
    candidates = []
    for rel in [
        "_index.md",
        "analysis/**/*.md",
        "qa/**/verified-facts.md",
        "qa/**/recommendations.md",
        "qa/**/pending-external.md",
        "applied/**/diff-summary.md",
        "applied/**/manifest.yaml",
    ]:
        candidates.extend(sorted(path.glob(rel)))
    return [p for p in candidates if p.is_file() and _is_safe_evidence_doc(p)]


def _is_safe_evidence_doc(path: Path) -> bool:
    parts = path.parts
    if "sources" in parts:
        return False
    name = path.name
    return (
        name in {"_index.md", "verified-facts.md", "recommendations.md", "pending-external.md",
                 "diff-summary.md", "manifest.yaml"}
        or "/analysis/" in path.as_posix()
    )


def _expand_map_entry(
    entry: str,
    wiki_root: Path,
    ws_dir: Path,
    pack_name: str,
    domain: Optional[str],
    project: Optional[str],
) -> Tuple[List[Path], Optional[Dict]]:
    raw = entry.strip()
    if not raw:
        return [], None
    unsafe = reject_unsafe_entry(raw)
    if unsafe:
        return [], {
            "category": "security-policy",
            "missing": f"Unsafe pack retrieval path `{raw}`: {unsafe}",
            "blocking_hint": True,
        }
    if "{domain}" in raw and not domain:
        return [], {
            "category": "pack-retrieval",
            "missing": f"Cannot expand {raw}: domain not detected",
            "blocking_hint": False,
        }
    if "{project}" in raw and not project:
        return [], {
            "category": "pack-retrieval",
            "missing": f"Cannot expand {raw}: project not detected",
            "blocking_hint": False,
        }
    expanded = raw.replace("{domain}", domain or "").replace("{project}", project or "")
    allowed_root = ws_dir
    if expanded.startswith("{ws}/"):
        base_path = ws_dir / expanded[len("{ws}/"):]
    elif expanded.startswith("packs/"):
        base_path = wiki_root / expanded
        allowed_root = wiki_root / "packs" / pack_name
    elif expanded.startswith("templates/"):
        base_path = wiki_root / expanded
        allowed_root = wiki_root / "templates"
    else:
        base_path = ws_dir / expanded

    paths: List[Path] = []
    if any(ch in base_path.as_posix() for ch in "*?["):
        paths = sorted(
            p for p in wiki_root.glob(_rel(base_path, wiki_root))
            if p.is_file() and is_relative_to(p, allowed_root)
        )
    elif "/evidence/" in base_path.as_posix() or base_path.name == "evidence":
        paths = [p for p in _safe_evidence_files(base_path) if is_relative_to(p, allowed_root)]
    elif base_path.is_dir():
        paths = sorted(
            p for p in base_path.rglob("*.md")
            if p.is_file() and is_relative_to(p, allowed_root)
        )
    elif base_path.is_file():
        paths = [base_path] if is_relative_to(base_path, allowed_root) else []
    if not paths:
        return [], {
            "category": "pack-retrieval",
            "missing": f"Pack retrieval path not found or empty: {expanded}",
            "blocking_hint": False,
        }
    return _dedupe_paths(paths), None


def _collect_pack_retrieval_candidates(
    wiki_root: Path,
    workspace: str,
    packs: List[str],
    components: List[str],
    domain: Optional[str],
    project: Optional[str],
    warnings: Optional[List[str]] = None,
) -> Tuple[List[Dict], List[Dict]]:
    ws_dir = wiki_root / "workspaces" / workspace
    candidates: List[Dict] = []
    gaps: List[Dict] = []
    for pack_name in packs:
        map_path = wiki_root / "packs" / pack_name / "agents" / "pipeline" / "retrieval-map.md"
        rows = _parse_retrieval_map(map_path)
        if not rows:
            continue
        for component in components:
            entries = rows.get(component)
            if not entries:
                continue
            for entry in entries:
                paths, gap = _expand_map_entry(entry, wiki_root, ws_dir, pack_name, domain, project)
                if gap:
                    gaps.append(gap)
                for path in paths:
                    rel = _rel(path, wiki_root)
                    category = _category_from_path(path, rel)
                    item = _doc(path, category, wiki_root, gaps=gaps, warnings=warnings)
                    if item is not None:
                        candidates.append(item)
    return candidates, gaps


def _iter_files(base: Path, patterns: Iterable[str]) -> List[Path]:
    if not base.exists():
        return []
    out: List[Path] = []
    for pattern in patterns:
        out.extend(sorted(p for p in base.glob(pattern) if p.is_file()))
    return out


def _doc(path: Path, category: str, wiki_root: Path,
         gaps: Optional[List[Dict]] = None,
         warnings: Optional[List[str]] = None) -> Optional[Dict]:
    rel = _rel(path, wiki_root)
    reason = block_reason(path)
    if reason:
        if gaps is not None:
            gaps.append({
                "category": "security-policy",
                "missing": f"Blocked secret-like path: {rel} ({reason})",
                "blocking_hint": False,
            })
        return None
    text = _read(path)
    if text is None:
        return None
    source_hash = _sha256_text(text)
    safe_text, findings = redact_text(text)
    if findings and warnings is not None:
        warnings.append(f"Redacted sensitive-looking content in {rel}")
    doc = {
        "category": category,
        "path": rel,
        "abs_path": path,
        "content_full": safe_text,
        "source_hash": source_hash,
    }
    if findings:
        doc["redacted"] = True
        doc["redaction_findings"] = findings
    return doc


def _dedupe_paths(paths: Iterable[Path]) -> List[Path]:
    seen: set[Path] = set()
    out: List[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(path)
    return sorted(out)


def _contract_files(directory: Path, wiki_root: Path) -> Tuple[List[Path], List[Dict]]:
    """Return contract files plus blocking gaps from contract-index.json."""
    if not directory.is_dir():
        return [], []
    gaps: List[Dict] = []
    paths: List[Path] = []
    index_path = directory / "contract-index.json"
    index = _load_index(index_path)
    for contract_id, rel_path in sorted(index.items()):
        target = directory / rel_path
        if target.is_file():
            paths.append(target)
        else:
            gaps.append({
                "category": "contract-index",
                "missing": (
                    f"{_rel(index_path, wiki_root)} maps {contract_id} "
                    f"to missing file {rel_path}"
                ),
                "blocking_hint": True,
            })
    loose = [
        p for p in _iter_files(directory, ["*.md", "*.json"])
        if p.name != "contract-index.json"
    ]
    paths.extend(loose)
    return _dedupe_paths(paths), gaps


def _collect_candidates(
    intent: str,
    wiki_root: Path,
    workspace: str,
    packs: List[str],
    components: Optional[List[str]] = None,
    domain: Optional[str] = None,
    project: Optional[str] = None,
    warnings: Optional[List[str]] = None,
) -> Tuple[List[Dict], List[Dict]]:
    ws_dir = wiki_root / "workspaces" / workspace
    candidates: List[Dict] = []
    gaps: List[Dict] = []
    components = components or []

    def add_many(paths: List[Path], category: str) -> None:
        for path in paths:
            item = _doc(path, category, wiki_root, gaps=gaps, warnings=warnings)
            if item is not None:
                candidates.append(item)

    contracts = ws_dir / "platform" / "contracts"
    patterns = ws_dir / "platform" / "patterns"
    projects = ws_dir / "projects"
    domains = ws_dir / "domains"
    runbooks = ws_dir / "runbooks"
    architecture = ws_dir / "platform" / "architecture"
    decisions = ws_dir / "decisions"

    contract_files, contract_gaps = _contract_files(contracts, wiki_root)
    gaps.extend(contract_gaps)

    if intent == "implement_feature":
        add_many(contract_files, "contract")
        add_many(_iter_files(patterns, ["*.md"]), "pattern")
        add_many(_iter_files(projects, ["*/knowledge-map.md", "*/services/*.md"]), "project")
        add_many(_iter_files(domains, ["*/workflow.md"]), "domain")
    elif intent == "fix_bug":
        add_many(_iter_files(runbooks, ["*.md"]), "runbook")
        add_many(_iter_files(projects, ["*/services/*.md", "*/knowledge-map.md"]), "project")
        add_many(_iter_files(patterns, ["*.md"]), "pattern")
    elif intent == "design":
        add_many(_iter_files(architecture, ["*.md"]), "architecture")
        add_many(_iter_files(decisions, ["*.md"]), "decision")
        add_many(_iter_files(patterns, ["*.md"]), "pattern")
        add_many(contract_files, "contract")
    elif intent == "incident":
        add_many(_iter_files(runbooks, ["*.md"]), "runbook")
        add_many(_iter_files(projects, ["*/services/*.md"]), "project")
    elif intent == "review":
        add_many(contract_files, "contract")
        add_many(_iter_files(patterns, ["*.md"]), "pattern")
        add_many(_iter_files(domains, ["*/workflow.md"]), "domain")

    pack_candidates, pack_gaps = _collect_pack_retrieval_candidates(
        wiki_root, workspace, packs, components, domain, project, warnings=warnings,
    )
    candidates.extend(pack_candidates)
    gaps.extend(pack_gaps)

    for pack_name in packs:
        pack_dir = wiki_root / "packs" / pack_name
        if not pack_dir.is_dir():
            gaps.append({
                "category": "pack",
                "missing": f"packs/{pack_name}",
                "blocking_hint": False,
            })
            continue
        add_many(_iter_files(pack_dir, ["agents/common-pitfalls.md"]), "pitfalls")

    if not candidates:
        gaps.append({
            "category": "retrieval",
            "missing": f"No candidate docs for intent={intent} workspace={workspace}",
            "blocking_hint": True,
        })

    return candidates, gaps


def _keywords(task: str, components: List[str]) -> List[str]:
    raw = re.findall(r"[A-Za-z0-9_\-]{3,}", task.lower())
    stop = {
        "the", "and", "for", "with", "this", "that", "into", "from", "contextd",
        "implement", "create", "build", "design", "review",
    }
    words = [w for w in raw if w not in stop]
    return sorted(set(words + [c.lower() for c in components]))


def _score(doc: Dict, words: List[str]) -> int:
    text = doc["content_full"].lower()
    name = Path(doc["path"]).stem.lower()
    score = 0
    for word in words:
        if word in name:
            score += 10
        if word in text[:800]:
            score += 3
        elif word in text:
            score += 1
    score += max(0, 5 - PRIORITY.get(doc["category"], 5))
    return score


def _estimate_tokens(text: str) -> int:
    """Deterministic rough budget estimate, intentionally not model-specific."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def _trace_doc(doc: Dict, score: int, reason: str) -> Dict:
    return {
        "path": doc["path"],
        "category": doc["category"],
        "selection_score": score,
        "selection_reason": reason,
        "estimated_tokens": _estimate_tokens(doc.get("content_full", "")),
        "source_hash": doc["source_hash"],
        "redacted": bool(doc.get("redacted")),
    }


def _rank_budget_trace(candidates: List[Dict], task: str, components: List[str],
                       workstream: str = "engineering",
                       max_docs: int = 7) -> Tuple[List[Dict], Dict, Dict]:
    words = _keywords(task, components)
    scored = [(doc, _score(doc, words)) for doc in candidates]
    ranked = sorted(
        scored,
        key=lambda item: (-item[1], PRIORITY.get(item[0]["category"], 9), item[0]["path"]),
    )

    budgets = WORKSTREAM_BUDGETS.get(workstream, CATEGORY_BUDGETS)
    used_by_category: Dict[str, int] = {}
    selected: List[Dict] = []
    selected_trace: List[Dict] = []
    dropped_trace: List[Dict] = []
    considered_trace: List[Dict] = []
    seen: set[str] = set()

    for doc, score in ranked:
        category = doc["category"]
        reason = "selected"
        if doc["path"] in seen:
            reason = "duplicate_path"
        elif len(selected) >= max_docs:
            reason = "max_docs_exhausted"
        elif used_by_category.get(category, 0) >= budgets.get(category, 1):
            reason = "category_budget_exhausted"

        trace_item = _trace_doc(doc, score, reason)
        considered_trace.append(trace_item)
        if reason == "selected":
            selected.append(doc)
            selected_trace.append(trace_item)
            seen.add(doc["path"])
            used_by_category[category] = used_by_category.get(category, 0) + 1
        else:
            dropped_trace.append(trace_item)

    tokens_by_category: Dict[str, int] = {}
    selected_tokens = 0
    for doc in selected:
        tokens = _estimate_tokens(doc.get("content_full", ""))
        selected_tokens += tokens
        category = doc["category"]
        tokens_by_category[category] = tokens_by_category.get(category, 0) + tokens

    drops_by_reason: Dict[str, int] = {}
    for item in dropped_trace:
        reason = item["selection_reason"]
        drops_by_reason[reason] = drops_by_reason.get(reason, 0) + 1

    budget_report = {
        "estimator": "chars_div_4",
        "max_docs": max_docs,
        "considered_docs": len(ranked),
        "selected_docs": len(selected),
        "dropped_docs": len(dropped_trace),
        "estimated_tokens_selected": selected_tokens,
        "estimated_tokens_by_category": dict(sorted(tokens_by_category.items())),
        "category_budgets": {
            key: budgets[key] for key in sorted(budgets)
            if key in used_by_category or key in {doc["category"] for doc in candidates}
        },
        "used_by_category": dict(sorted(used_by_category.items())),
        "drops_by_reason": dict(sorted(drops_by_reason.items())),
    }
    trace = {
        "workstream": workstream,
        "considered_docs": considered_trace,
        "selected_docs": selected_trace,
        "dropped_docs": dropped_trace,
    }
    return selected, trace, budget_report


def _rank_and_budget(candidates: List[Dict], task: str, components: List[str],
                     workstream: str = "engineering", max_docs: int = 7) -> List[Dict]:
    selected, _, _ = _rank_budget_trace(candidates, task, components, workstream, max_docs)
    return selected


def _split_sections(text: str) -> Dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE))
    if not matches:
        return {}
    sections: Dict[str, str] = {}
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        sections[title] = text[start:end].strip()
    return sections


def _slice_doc(doc: Dict) -> Dict:
    category = doc["category"]
    policy = SECTION_POLICY.get(category, ["all"])
    text = doc["content_full"]
    if policy == ["all"]:
        selected_sections = ["all"]
        sliced = text.strip()
    else:
        by_section = _split_sections(text)
        chunks: List[str] = []
        selected_sections = []
        for wanted in policy:
            for title, body in by_section.items():
                if title.lower() == wanted.lower():
                    chunks.append(body)
                    selected_sections.append(title)
                    break
        if not chunks:
            selected_sections = ["all"]
            sliced = text.strip()
        else:
            sliced = "\n\n".join(chunks).strip()
    out = {
        "category": category,
        "path": doc["path"],
        "sections": selected_sections,
        "content": sliced,
        "source_hash": doc["source_hash"],
    }
    if doc.get("redacted"):
        out["redacted"] = True
        out["redaction_findings"] = doc.get("redaction_findings", [])
    return out


def _load_index(index_path: Path) -> Dict[str, str]:
    data = _read(index_path)
    if data is None:
        return {}
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return {}
    contracts = parsed.get("contracts")
    return contracts if isinstance(contracts, dict) else {}


def _contract_dirs(wiki_root: Path, workspace: str, packs: List[str]) -> List[Path]:
    ws_dir = wiki_root / "workspaces" / workspace
    dirs = [
        ws_dir / "platform" / "contracts",
        ws_dir / "contracts",
    ]
    domains = ws_dir / "domains"
    if domains.is_dir():
        dirs.extend(sorted(p / "contracts" for p in domains.iterdir() if p.is_dir()))
    dirs.extend(wiki_root / "packs" / p / "contracts" for p in packs)
    return dirs


def resolve_contract_path(contract_id: str, wiki_root: Path, workspace: str,
                          packs: Optional[List[str]] = None) -> Tuple[Optional[Path], List[str]]:
    """Resolve a contract id via contract-index.json, then filename fallback."""
    packs = packs or []
    warnings: List[str] = []
    contract_id = (contract_id or "").strip()
    if not contract_id:
        warnings.append("Invalid contract id: id must not be empty")
        return None, warnings
    if (
        "/" in contract_id
        or "\\" in contract_id
        or ".." in contract_id
        or Path(contract_id).is_absolute()
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", contract_id)
    ):
        warnings.append(
            "Invalid contract id: use only alphanumeric characters, '.', '_', and '-'; "
            "path separators and '..' are not allowed"
        )
        return None, warnings
    for directory in _contract_dirs(wiki_root, workspace, packs):
        if not directory.is_dir():
            continue
        index = _load_index(directory / "contract-index.json")
        if contract_id in index:
            path = directory / index[contract_id]
            if path.is_file():
                return path, warnings
            warnings.append(f"contract-index maps {contract_id} to missing file: {path}")
            return None, warnings
        for ext in (".md", ".json"):
            for candidate in (
                directory / f"{contract_id}{ext}",
                directory / f"{contract_id}.contract{ext}",
            ):
                if candidate.is_file():
                    return candidate, warnings
        for candidate in directory.glob("*"):
            if candidate.is_file() and candidate.stem == contract_id:
                return candidate, warnings
    return None, warnings


def _contracts_touched(docs: List[Dict]) -> List[str]:
    out: List[str] = []
    for doc in docs:
        if doc["category"] != "contract":
            continue
        stem = Path(doc["path"]).stem
        if stem.endswith(".contract"):
            stem = stem[:-len(".contract")]
        out.append(stem)
    return sorted(set(out))


def _collect_static_context(wiki_root: Path, workspace: str, packs: List[str]) -> List[Dict]:
    """Collect deterministic non-volatile sources for materialized packs."""
    sources: List[Tuple[Path, str]] = [
        (wiki_root / "workspaces" / workspace / "workspace.md", "workspace-profile"),
        (wiki_root / "agents" / "system-prompt.md", "engine-guidance"),
        (wiki_root / "agents" / "constraints.md", "engine-rule"),
        (wiki_root / "agents" / "pipeline" / "validator-rules.md", "engine-rule"),
    ]
    for pack_name in packs:
        pack_dir = wiki_root / "packs" / pack_name
        sources.extend([
            (pack_dir / "pack.yaml", "pack-rule"),
            (pack_dir / "agents" / "constraints.md", "pack-rule"),
            (pack_dir / "agents" / "coding-rules.md", "pack-rule"),
            (pack_dir / "agents" / "common-pitfalls.md", "pack-rule"),
        ])

    docs: List[Dict] = []
    for path, category in sources:
        item = _doc(path, category, wiki_root)
        if item is not None:
            docs.append(_slice_doc(item))
    return docs


def _build_context_pack(
    workspace: str,
    packs: List[str],
    docs: List[Dict],
    static_docs: Optional[List[Dict]] = None,
) -> Dict:
    static_docs = static_docs or []
    pack_sources = docs + static_docs
    static = [
        {
            "path": doc["path"],
            "category": doc["category"],
            "source_hash": doc["source_hash"],
        }
        for doc in pack_sources
        if doc["category"] in {
            "contract", "pattern", "project", "service", "domain", "workflow",
            "architecture", "decision", "runbook", "product", "requirement",
            "design", "quality", "evidence", "pitfalls", "common-pitfalls",
            "workspace-profile", "engine-guidance", "engine-rule", "pack-rule",
        }
    ]
    payload = {
        "workspace": workspace,
        "packs": packs,
        "sources": sorted(static, key=lambda x: x["path"]),
    }
    source_hash = _sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    return {
        "artifact_type": "context_pack_ref",
        "version": "1",
        "kind": "deterministic-static-context",
        "packKey": source_hash[:16],
        "ref": None,
        "compiledRef": None,
        "sourceHash": source_hash,
        "sources": payload["sources"],
        "status": "not_materialized",
    }


def build_context_artifact(
    task: str,
    wiki_root: Path,
    workspace: str,
    packs: List[str],
    project_dir: Optional[Path] = None,
    warnings: Optional[List[str]] = None,
    include_selection_trace: bool = False,
) -> Dict:
    """Build the canonical JSON context artifact."""
    warnings_out = list(warnings or [])
    intent_type = detect_intent(task)
    components = detect_components(task, wiki_root, packs)
    domain, scope = detect_scope(task, wiki_root, workspace)
    workstream = detect_workstream(task, packs, components)
    meta = WORKSTREAM_PRIORITY.get(workstream, WORKSTREAM_PRIORITY["engineering"])
    candidates, gaps = _collect_candidates(
        intent_type,
        wiki_root,
        workspace,
        packs,
        components=components,
        domain=domain,
        project=scope,
        warnings=warnings_out,
    )
    selected, selection_trace, budget_report = _rank_budget_trace(
        candidates, task, components, workstream=workstream,
    )
    docs = [_slice_doc(doc) for doc in selected]
    static_docs = _collect_static_context(wiki_root, workspace, packs)
    context_pack = _build_context_pack(workspace, packs, docs, static_docs)
    source_hashes = {
        doc["path"]: doc["source_hash"]
        for doc in docs + static_docs
    }

    artifact = {
        "artifact_type": "contextd_task_context.v1",
        "version": "1",
        "generated_at": _now(),
        "task": task,
        "workspace": workspace,
        "project_dir": str(project_dir.resolve()) if project_dir else None,
        "knowledge_root": str(wiki_root.resolve()),
        "intent": {
            "type": intent_type,
            "components": components,
            "domain": domain,
            "scope": scope,
            "workstream": workstream,
            "audience": AUDIENCE_BY_WORKSTREAM.get(workstream, "engineering"),
            "context_goal": meta["context_goal"],
            "patterns_needed": [
                Path(doc["path"]).stem for doc in docs if doc["category"] == "pattern"
            ],
            "contracts_touched": _contracts_touched(docs),
        },
        "referenced_docs": docs,
        "static_context": static_docs,
        "gaps": gaps,
        "warnings": warnings_out,
        "contextPack": context_pack,
        "retrieval_policy": {
            "mode": "deterministic-file-backed",
            "advisory_retrieval": False,
            "priority": meta["priority"],
            "max_docs": 7,
            "rag_policy": "advisory-only-disabled-by-default",
        },
        "budget_report": budget_report,
        "source_hashes": source_hashes,
    }
    artifact["governance_report"] = context_policy.evaluate_artifact(
        artifact,
        wiki_root,
        workspace,
        packs,
    )
    if include_selection_trace:
        artifact["_selection_trace"] = selection_trace
    return artifact


def build_context_explanation(
    task: str,
    wiki_root: Path,
    workspace: str,
    packs: List[str],
    project_dir: Optional[Path] = None,
    warnings: Optional[List[str]] = None,
) -> Dict:
    """Build a human/debug-oriented explanation around the canonical artifact."""
    artifact = build_context_artifact(
        task=task,
        wiki_root=wiki_root,
        workspace=workspace,
        packs=packs,
        project_dir=project_dir,
        warnings=warnings,
        include_selection_trace=True,
    )
    trace = artifact.pop("_selection_trace", {})
    summary = {
        "artifact_type": artifact["artifact_type"],
        "workspace": artifact["workspace"],
        "intent": artifact["intent"],
        "referenced_doc_count": len(artifact["referenced_docs"]),
        "gap_count": len(artifact["gaps"]),
        "warning_count": len(artifact["warnings"]),
        "context_pack_key": artifact["contextPack"]["packKey"],
        "budget_report": artifact.get("budget_report", {}),
    }
    return {
        "artifact_type": "contextd_context_explanation.v1",
        "version": "1",
        "task": task,
        "summary": summary,
        "artifact": artifact,
        "selection_trace": trace,
    }


def render_markdown(artifact: Dict) -> str:
    lines: List[str] = [
        "# Task Context",
        "",
        "## Task",
        f"> {artifact['task']}",
        "",
        "## Detected Intent",
        f"- **Type**: `{artifact['intent']['type']}`",
        f"- **Workstream**: `{artifact['intent'].get('workstream', 'engineering')}`",
        f"- **Audience**: `{artifact['intent'].get('audience', 'engineering')}`",
        f"- **Context Goal**: `{artifact['intent'].get('context_goal', 'prepare_code_change')}`",
        "- **Components**: "
        + (", ".join(artifact["intent"].get("components") or []) or "(none detected)"),
        f"- **Workspace**: `{artifact['workspace']}`",
        f"- **Context Pack**: `{artifact['contextPack']['packKey']}` "
        f"({artifact['contextPack']['status']})",
        "",
        "## Relevant Knowledge",
        "",
    ]
    for doc in artifact.get("referenced_docs", []):
        sections = ", ".join(doc.get("sections") or ["all"])
        lines.append(f"### [{doc['category']}] {doc['path']}")
        lines.append(f"_Sections: {sections}; sha256: {doc['source_hash'][:12]}_")
        lines.append("")
        lines.append(doc.get("content", "").strip())
        lines.append("")

    if artifact.get("gaps"):
        lines.append("## Knowledge Gaps")
        lines.append("")
        for gap in artifact["gaps"]:
            marker = "blocking" if gap.get("blocking_hint") else "non-blocking"
            lines.append(f"- [{marker}] {gap['category']}: {gap['missing']}")
        lines.append("")

    if artifact.get("warnings"):
        lines.append("## Warnings")
        lines.append("")
        for warning in artifact["warnings"]:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("---")
    lines.append("_Generated by contextd context (deterministic, file-backed)._")
    return "\n".join(lines)


def _pack_markdown(artifact: Dict) -> str:
    lines = [
        f"# Context Pack {artifact['contextPack']['packKey']}",
        "",
        f"Workspace: {artifact['workspace']}",
        f"Source hash: {artifact['contextPack']['sourceHash']}",
        "",
    ]
    docs: List[Dict] = []
    seen: set[str] = set()
    for doc in artifact.get("static_context", []) + artifact.get("referenced_docs", []):
        path = doc.get("path")
        if not path or path in seen:
            continue
        seen.add(path)
        docs.append(doc)
    for doc in docs:
        lines.append("---")
        lines.append(f"## Source: {doc['path']}")
        lines.append("")
        lines.append(doc.get("content", "").strip())
        lines.append("")
    return "\n".join(lines)


def materialize_context(artifact: Dict, project_dir: Path) -> Dict:
    """Write current-task JSON/Markdown and compiled static context pack."""
    context_dir = project_dir / ".contextd" / "context"
    packs_dir = context_dir / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    pack_path = packs_dir / f"{artifact['contextPack']['packKey']}.md"
    pack_path.write_text(_pack_markdown(artifact), encoding="utf-8")

    artifact = json.loads(json.dumps(artifact, ensure_ascii=False))
    rel_pack = pack_path.relative_to(project_dir).as_posix()
    artifact["contextPack"]["ref"] = rel_pack
    artifact["contextPack"]["compiledRef"] = rel_pack
    artifact["contextPack"]["status"] = "materialized"

    json_path = context_dir / "current-task.json"
    md_path = context_dir / "current-task.md"
    json_path.write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(artifact), encoding="utf-8")
    artifact["materialized"] = {
        "json": json_path.relative_to(project_dir).as_posix(),
        "markdown": md_path.relative_to(project_dir).as_posix(),
        "pack": rel_pack,
    }
    return artifact


def build_task_context(task: str, wiki_root: Path, workspace: str,
                       packs: List[str]) -> str:
    """Legacy API: return rendered Markdown."""
    artifact = build_context_artifact(task, wiki_root, workspace, packs)
    return render_markdown(artifact)
