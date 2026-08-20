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
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

import pack_loader
from . import context_policy, synapse_engine
from .atomic_write import atomic_write_text
from .context_security import block_reason, is_relative_to, redact_text, reject_unsafe_entry


INTENT_KEYWORDS = {
    "implement_feature": [
        "add", "implement", "create", "build", "write", "support", "enable",
        "introduce", "new feature", "feature", "endpoint", "api", "consumer",
        "producer", "service", "handler", "controller",
    ],
    "fix_bug": [
        "fix", "bug", "debug", "broken", "breaks", "error", "crash", "fails", "failing",
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
        "code review", "walkthrough", "sign-off", "drift", "remediation",
        "đánh giá", "danh gia", "kiểm tra", "kiem tra", "nghiệm thu", "nghiem thu",
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
        "audit", "drift", "remediation", "acceptance criteria", "verification method",
        "đánh giá", "danh gia", "nghiệm thu", "nghiem thu",
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
    "pack-operator-steering": "quality",
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
    "workspace-rule": ["all"],
    "pack-rule": ["all"],
    "pack-metadata": ["all"],
    "pack-knowledge": ["all"],
    "operator": ["all"],
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
    "workspace-rule": 3,
    "pack-rule": 3,
    "pack-metadata": 1,
    "pack-knowledge": 3,
    "operator": 3,
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
    "workspace-rule": 1,
    "pack-rule": 1,
    "pack-metadata": 1,
    "pack-knowledge": 1,
    "operator": 1,
}

SYNAPSE_SCORE_ADJUSTMENTS = {
    "draft": -6,
    "active": 0,
    "deprecated": -12,
    "superseded": -16,
    "stale": -4,
}

# A component-specific retrieval-map is an explicit ownership signal, stronger
# than incidental word overlap in generic intent candidates. Direct entries and
# earlier map entries receive a small deterministic tie-break while category and
# max-doc budgets still apply.
PACK_ROUTE_BASE_SCORE = 2
PACK_ROUTE_DIRECT_SCORE = 12
PACK_ROUTE_ORDER_SCORE = 4

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

# Deterministic tie-break order for detect_intent()/detect_workstream() when
# keyword scores are equal. Most specific/urgent first; generic fallback
# values (implement_feature, engineering) last so they only win by default.
INTENT_PRECEDENCE = ["incident", "fix_bug", "review", "design", "implement_feature"]
WORKSTREAM_PRECEDENCE = [
    "security", "ops", "quality", "business_analysis",
    "product", "design", "domain_research", "engineering",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_source_record(path: Path) -> Optional[synapse_engine.SourceRecord]:
    """Read exact source bytes once, then decode for context processing."""
    try:
        payload = path.read_bytes()
        text = payload.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return synapse_engine.SourceRecord(
        text=text,
        source_hash=hashlib.sha256(payload).hexdigest(),
    )


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _is_workspace_source_ref(relative_path: str) -> bool:
    parts = relative_path.split("/")
    return len(parts) >= 3 and parts[0] == "workspaces" and bool(parts[1])


_KEYWORD_PATTERN_CACHE: Dict[str, "re.Pattern"] = {}


def _keyword_pattern(keyword: str) -> "re.Pattern":
    """Compile (and cache) a word-boundary-aware pattern for `keyword`.

    Boundaries are added only where the keyword's edge character is itself
    a word character. This keeps substring-only keywords like `.proto` or
    `@RestController` matching (they'd never match with hard `\\b` anchors)
    while stopping plain-word keywords like `api`/`ui`/`check` from matching
    inside unrelated words (`rapid`, `build`, `checkout`). `\\w` is
    unicode-aware, so Vietnamese keywords (e.g. "đánh giá") keep correct
    boundaries too. Multi-word keywords also match hyphen/underscore/slash
    joins, e.g. "drift check" matches "drift-check".
    """
    pattern = _KEYWORD_PATTERN_CACHE.get(keyword)
    if pattern is None:
        tokens = keyword.split()
        body = r"[\s\-_/]+".join(re.escape(tok) for tok in tokens)
        prefix = r"(?<!\w)" if keyword[:1].isalnum() or keyword[:1] == "_" else ""
        suffix = r"(?!\w)" if keyword[-1:].isalnum() or keyword[-1:] == "_" else ""
        pattern = re.compile(prefix + body + suffix, re.IGNORECASE)
        _KEYWORD_PATTERN_CACHE[keyword] = pattern
    return pattern


def _matches(keyword: str, text: str) -> bool:
    return bool(keyword) and _keyword_pattern(keyword).search(text) is not None


def _pick_by_precedence(scores: Dict[str, int], precedence: List[str],
                        default: str) -> str:
    """Pick the highest-scoring key; ties broken by `precedence` order."""
    if not scores:
        return default
    order = {name: idx for idx, name in enumerate(precedence)}
    fallback_rank = len(precedence)
    return max(
        scores,
        key=lambda name: (scores[name], -order.get(name, fallback_rank)),
    )


def _classification_summary(scores: Dict[str, int], chosen: str) -> Dict:
    """Expose why `chosen` won, for `contextd explain` debugging."""
    ranked = sorted(scores.items(), key=lambda item: -item[1])
    top_score = scores.get(chosen)
    tie_broken = sum(1 for _, score in ranked if score == top_score) > 1
    runner_up = next((name for name, _ in ranked if name != chosen), None)
    return {
        "scores": dict(sorted(scores.items())),
        "runner_up": runner_up,
        "tie_broken": tie_broken,
    }


def _intent_scores(task: str) -> Dict[str, int]:
    scores: Dict[str, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if _matches(kw, task))
        if score:
            scores[intent] = score
    return scores


def detect_intent(task: str) -> str:
    return _pick_by_precedence(_intent_scores(task), INTENT_PRECEDENCE, "implement_feature")


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


def _load_pack_manifest(pack_yaml: Path) -> Dict:
    text = _read(pack_yaml)
    if text is None:
        return {}
    try:
        manifest = pack_loader._parse_simple_yaml(text)  # noqa: SLF001
    except (TypeError, ValueError):
        return {}
    return manifest if isinstance(manifest, dict) else {}


def _pack_manifest_version(manifest: Mapping) -> int:
    value = manifest.get("manifest_version", 1)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1


def _manifest_retrieval_rows(manifest: Mapping) -> Dict[str, List[str]]:
    raw = manifest.get("retrieval") or {}
    if not isinstance(raw, dict):
        return {}
    rows: Dict[str, List[str]] = {}
    for component, value in raw.items():
        if isinstance(value, list):
            entries = [str(item).strip() for item in value if str(item).strip()]
        elif isinstance(value, str) and value.strip():
            entries = [value.strip()]
        else:
            entries = []
        if entries:
            rows[str(component)] = entries
    return rows


def _pack_retrieval_rows(wiki_root: Path, pack_name: str) -> Dict[str, List[str]]:
    pack_dir = wiki_root / "packs" / pack_name
    manifest = _load_pack_manifest(pack_dir / "pack.yaml")
    if _pack_manifest_version(manifest) >= 3:
        # V3 has one routing authority. An invalid/empty canonical map must not
        # silently fall back to a stale v2 adapter.
        return _manifest_retrieval_rows(manifest)
    files = manifest.get("files") or {}
    declared = files.get("retrieval_map") if isinstance(files, dict) else None
    map_path = pack_dir / str(declared or "agents/pipeline/retrieval-map.md")
    return _parse_retrieval_map(map_path)


def _uses_canonical_pack_knowledge(manifest: Mapping) -> bool:
    # Never fall back to legacy prose for a malformed v3 pack. Validation
    # reports the missing canonical file; runtime simply omits unavailable v3
    # guidance instead of loading a competing source of truth.
    return _pack_manifest_version(manifest) >= 3


def detect_components(task: str, wiki_root: Path, packs: List[str]) -> List[str]:
    components: set[str] = set()
    for pack_name in packs:
        keywords = _parse_pack_keywords(wiki_root / "packs" / pack_name / "pack.yaml")
        for component, words in keywords.items():
            if any(_matches(word, task) for word in words):
                components.add(component)
    return sorted(components)


def detect_scope(task: str, wiki_root: Path, workspace: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect domain + project by matching directory names in task text."""
    ws_dir = wiki_root / "workspaces" / workspace

    def match_dir(parent: Path) -> Optional[str]:
        if not parent.is_dir():
            return None
        for path in sorted(p for p in parent.iterdir() if p.is_dir()):
            name = path.name.lower()
            variants = {name, name.replace("-", " "), name.replace("_", " ")}
            if any(v and _matches(v, task) for v in variants):
                return path.name
        return None

    return match_dir(ws_dir / "domains"), match_dir(ws_dir / "projects")


def _workstream_scores(task: str, packs: List[str], components: List[str]) -> Dict[str, int]:
    scores: Dict[str, int] = {}
    for workstream, keywords in WORKSTREAM_KEYWORDS.items():
        score = sum(1 for kw in keywords if _matches(kw, task))
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

    return scores


def detect_workstream(task: str, packs: List[str], components: List[str]) -> str:
    scores = _workstream_scores(task, packs, components)
    return _pick_by_precedence(scores, WORKSTREAM_PRECEDENCE, "engineering")


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
    if path_text.startswith("packs/") and "/templates/" in path_text:
        return "operator"
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
        paths = [
            p for p in paths
            if "evidence" not in p.parts or _is_safe_evidence_doc(p)
        ]
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
    source_records: Optional[Mapping[str, synapse_engine.SourceRecord]] = None,
) -> Tuple[List[Dict], List[Dict]]:
    ws_dir = wiki_root / "workspaces" / workspace
    candidates: List[Dict] = []
    gaps: List[Dict] = []
    for pack_name in packs:
        rows = _pack_retrieval_rows(wiki_root, pack_name)
        if not rows:
            continue
        for component in components:
            entries = rows.get(component)
            if not entries:
                continue
            for entry_index, entry in enumerate(entries):
                paths, gap = _expand_map_entry(entry, wiki_root, ws_dir, pack_name, domain, project)
                if gap:
                    gaps.append(gap)
                entry_path = entry.split("#", 1)[0].strip()
                direct_entry = bool(Path(entry_path).suffix)
                for path in paths:
                    rel = _rel(path, wiki_root)
                    category = _category_from_path(path, rel)
                    item = _doc(
                        path,
                        category,
                        wiki_root,
                        gaps=gaps,
                        warnings=warnings,
                        source_records=source_records,
                    )
                    if item is not None:
                        item["pack_retrieval_route"] = {
                            "pack": pack_name,
                            "component": component,
                            "entry": entry,
                            "entry_index": entry_index,
                            "direct_entry": direct_entry,
                        }
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
         warnings: Optional[List[str]] = None,
         source_records: Optional[Mapping[str, synapse_engine.SourceRecord]] = None,
         ) -> Optional[Dict]:
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
    source = source_records.get(rel) if source_records is not None else None
    if (
        source_records is not None
        and source is None
        and _is_workspace_source_ref(rel)
    ):
        # A workspace path discovered after the synapse scan belongs to a
        # different source generation. Keep this build coherent by deferring
        # it to the next invocation instead of rereading outside the snapshot.
        return None
    if source is None:
        source = _read_source_record(path)
    if source is None:
        return None
    text = source.text
    source_hash = source.source_hash
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


def _synapse_state(node: Dict) -> Dict:
    return {
        "node_id": node["id"],
        "memory_class": node["memory_class"],
        "lifecycle": node["lifecycle"],
        "freshness": node["freshness"],
        "review_by": node.get("review_by"),
    }


def _attach_synapse_metadata(
    docs: Iterable[Dict],
    lookups: synapse_engine.SynapseLookups,
) -> None:
    for doc in docs:
        node = lookups.nodes_by_path.get(doc["path"])
        if not node:
            continue
        doc["synapse"] = _synapse_state(node)


def _expand_replacement_candidates(
    candidates: List[Dict],
    lookups: synapse_engine.SynapseLookups,
    wiki_root: Path,
    gaps: List[Dict],
    warnings: List[str],
    source_records: Optional[Mapping[str, synapse_engine.SourceRecord]] = None,
) -> List[Dict]:
    """Add active one-hop replacements for superseded/deprecated candidates."""
    expanded = list(candidates)
    existing_paths = {doc["path"] for doc in expanded}
    for doc in list(expanded):
        state = doc.get("synapse") or {}
        if state.get("lifecycle") not in {"deprecated", "superseded"}:
            continue
        replacement_ids = lookups.replacements_by_target.get(
            state.get("node_id", ""),
            (),
        )
        for replacement_id in replacement_ids:
            replacement = lookups.nodes_by_id.get(replacement_id)
            if not replacement or replacement["path"] in existing_paths:
                continue
            path = wiki_root / replacement["path"]
            category = _category_from_path(path, replacement["path"], replacement["kind"])
            item = _doc(
                path,
                category,
                wiki_root,
                gaps=gaps,
                warnings=warnings,
                source_records=source_records,
            )
            if item is None:
                continue
            item["synapse"] = _synapse_state(replacement)
            item["synapse_expansion"] = {
                "reason": "active_replacement",
                "replaces": state.get("node_id"),
            }
            expanded.append(item)
            existing_paths.add(item["path"])
    return expanded


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


def _contract_files(
    directory: Path,
    wiki_root: Path,
    source_records: Optional[Mapping[str, synapse_engine.SourceRecord]] = None,
) -> Tuple[List[Path], List[Dict]]:
    """Return contract files plus blocking gaps from contract-index.json."""
    if not directory.is_dir():
        return [], []
    gaps: List[Dict] = []
    paths: List[Path] = []
    index_path = directory / "contract-index.json"
    index = _load_index(index_path, wiki_root, source_records)
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
    source_records: Optional[Mapping[str, synapse_engine.SourceRecord]] = None,
) -> Tuple[List[Dict], List[Dict]]:
    ws_dir = wiki_root / "workspaces" / workspace
    candidates: List[Dict] = []
    gaps: List[Dict] = []
    components = components or []

    def add_many(paths: List[Path], category: str) -> None:
        for path in paths:
            item = _doc(
                path,
                category,
                wiki_root,
                gaps=gaps,
                warnings=warnings,
                source_records=source_records,
            )
            if item is not None:
                candidates.append(item)

    contracts = ws_dir / "platform" / "contracts"
    patterns = ws_dir / "platform" / "patterns"
    projects = ws_dir / "projects"
    domains = ws_dir / "domains"
    runbooks = ws_dir / "runbooks"
    architecture = ws_dir / "platform" / "architecture"
    decisions = ws_dir / "decisions"

    contract_files, contract_gaps = _contract_files(
        contracts,
        wiki_root,
        source_records,
    )
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
        wiki_root,
        workspace,
        packs,
        components,
        domain,
        project,
        warnings=warnings,
        source_records=source_records,
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
        manifest = _load_pack_manifest(pack_dir / "pack.yaml")
        if _uses_canonical_pack_knowledge(manifest):
            # Manifest v3 folds failure signals into the selected component
            # section of knowledge.md. The legacy all-intent pitfalls document
            # remains on disk only as a compatibility adapter.
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
    raw = re.findall(r"[^\W_][\w\-]{2,}", task.lower(), flags=re.UNICODE)
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
        if _matches(word, name):
            score += 10
        if _matches(word, text[:800]):
            score += 3
        elif _matches(word, text):
            score += 1
    score += max(0, 5 - PRIORITY.get(doc["category"], 5))
    route = doc.get("pack_retrieval_route") or {}
    if route:
        score += PACK_ROUTE_BASE_SCORE
        if route.get("direct_entry"):
            score += PACK_ROUTE_DIRECT_SCORE
        score += max(
            0,
            PACK_ROUTE_ORDER_SCORE - int(route.get("entry_index", 0)),
        )
    score += _synapse_score_adjustment(doc)
    return score


def _synapse_score_adjustment(doc: Dict) -> int:
    state = doc.get("synapse") or {}
    adjustment = SYNAPSE_SCORE_ADJUSTMENTS.get(state.get("lifecycle"), 0)
    if state.get("freshness") == "stale":
        adjustment += SYNAPSE_SCORE_ADJUSTMENTS["stale"]
    return adjustment


def _estimate_tokens(text: str) -> int:
    """Deterministic rough budget estimate, intentionally not model-specific."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def _trace_doc(doc: Dict, score: int, reason: str) -> Dict:
    item = {
        "path": doc["path"],
        "category": doc["category"],
        "selection_score": score,
        "selection_reason": reason,
        "estimated_tokens": _estimate_tokens(doc.get("content_full", "")),
        "source_hash": doc["source_hash"],
        "redacted": bool(doc.get("redacted")),
    }
    if doc.get("synapse"):
        item["synapse"] = doc["synapse"]
        item["state_score_adjustment"] = _synapse_score_adjustment(doc)
    if doc.get("synapse_expansion"):
        item["synapse_expansion"] = doc["synapse_expansion"]
    if doc.get("pack_retrieval_route"):
        item["pack_retrieval_route"] = doc["pack_retrieval_route"]
    return item


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
    if doc.get("synapse"):
        out["synapse"] = doc["synapse"]
    if doc.get("synapse_expansion"):
        out["synapse_expansion"] = doc["synapse_expansion"]
    if doc.get("redacted"):
        out["redacted"] = True
        out["redaction_findings"] = doc.get("redaction_findings", [])
    return out


def _slice_pack_manifest(doc: Dict, manifest: Mapping,
                         selected_components: Iterable[str]) -> Dict:
    owned = {str(item) for item in (manifest.get("components") or [])}
    selected = sorted(owned & {str(item) for item in selected_components})
    lines = [
        f"# Pack Metadata — {manifest.get('name', Path(doc['path']).parent.name)}",
        "",
        f"- Version: `{manifest.get('version', 'unknown')}`",
        f"- Status: `{manifest.get('status', 'legacy')}`",
        f"- Category: `{manifest.get('category', 'unspecified')}`",
        "- Knowledge source: `"
        + str((manifest.get("files") or {}).get("knowledge") or "missing")
        + "`",
        "- Selected components: " + (
            ", ".join(f"`{item}`" for item in selected) if selected else "(global only)"
        ),
    ]
    return {
        "category": "pack-metadata",
        "path": doc["path"],
        "sections": ["metadata"],
        "content": "\n".join(lines),
        "source_hash": doc["source_hash"],
    }


def _slice_pack_knowledge(doc: Dict, owned_components: Iterable[str],
                          selected_components: Iterable[str]) -> Dict:
    text = doc["content_full"]
    sections = _split_sections(text)
    owned = {str(item) for item in owned_components}
    selected = owned & {str(item) for item in selected_components}
    chunks: List[str] = []
    selected_titles: List[str] = []
    for title, body in sections.items():
        normalized = title.strip().casefold()
        include = normalized == "global principles"
        if normalized.startswith("component:"):
            component = title.split(":", 1)[1].strip()
            include = component in selected
        if include:
            chunks.append(body)
            selected_titles.append(title)

    if not chunks:
        # Validation rejects malformed v3 knowledge, but runtime preserves the
        # full source instead of silently dropping all pack guidance.
        return _slice_doc({**doc, "category": "pack-knowledge"})

    h1 = next(
        (line.strip() for line in text.splitlines() if line.startswith("# ")),
        "# Pack Knowledge",
    )
    out = {
        "category": "pack-knowledge",
        "path": doc["path"],
        "sections": selected_titles,
        "content": h1 + "\n\n" + "\n\n".join(chunks).strip(),
        "source_hash": doc["source_hash"],
    }
    if doc.get("redacted"):
        out["redacted"] = True
        out["redaction_findings"] = doc.get("redaction_findings", [])
    return out


def _finalize_budget_report(budget_report: Dict, referenced_docs: List[Dict],
                            static_docs: List[Dict]) -> Dict:
    def summarize(docs: Iterable[Dict]) -> Tuple[int, Dict[str, int]]:
        total = 0
        by_category: Dict[str, int] = {}
        for doc in docs:
            tokens = _estimate_tokens(doc.get("content", ""))
            total += tokens
            category = str(doc.get("category", "unknown"))
            by_category[category] = by_category.get(category, 0) + tokens
        return total, dict(sorted(by_category.items()))

    referenced_tokens, referenced_by_category = summarize(referenced_docs)
    static_tokens, static_by_category = summarize(static_docs)
    compiled_docs: List[Dict] = []
    seen: set[str] = set()
    overlap = 0
    for doc in static_docs + referenced_docs:
        path = str(doc.get("path") or "")
        if path and path in seen:
            overlap += 1
            continue
        if path:
            seen.add(path)
        compiled_docs.append(doc)
    total_tokens, total_by_category = summarize(compiled_docs)

    out = dict(budget_report)
    out.update({
        # Preserve the v1 field while making it reflect the actual sliced
        # referenced payload rather than each candidate's full source file.
        "estimated_tokens_selected": referenced_tokens,
        "estimated_tokens_by_category": referenced_by_category,
        "static_docs": len(static_docs),
        "compiled_docs": len(compiled_docs),
        "deduplicated_overlap_docs": overlap,
        "estimated_tokens_referenced": referenced_tokens,
        "estimated_tokens_static": static_tokens,
        "estimated_tokens_total": total_tokens,
        "estimated_tokens_static_by_category": static_by_category,
        "estimated_tokens_total_by_category": total_by_category,
    })
    return out


def _selected_state_warnings(docs: List[Dict]) -> List[str]:
    warnings: List[str] = []
    for doc in docs:
        state = doc.get("synapse") or {}
        node_id = state.get("node_id")
        if not node_id:
            continue
        lifecycle = state.get("lifecycle")
        freshness = state.get("freshness")
        if lifecycle and lifecycle != "active":
            warnings.append(
                f"Selected {lifecycle} knowledge node {node_id} ({doc['path']})."
            )
        if freshness == "stale":
            review = f"; review_by={state['review_by']}" if state.get("review_by") else ""
            warnings.append(
                f"Selected stale knowledge node {node_id} ({doc['path']}{review})."
            )
    return warnings


def _context_projection(synapse: Dict, docs: List[Dict]) -> Dict:
    selected_states = [
        doc["synapse"] for doc in docs if doc.get("synapse")
    ]
    selected_ids = sorted({state["node_id"] for state in selected_states})
    selected_set = set(selected_ids)
    relevant_edges = [
        edge for edge in synapse.get("edges", [])
        if edge.get("source") in selected_set and edge.get("target") in selected_set
    ]
    return {
        "artifact_type": "contextd_context_projection.v1",
        "version": "1",
        "memory_class": "context",
        "source_synapse_hash": synapse["synapse_hash"],
        "policy_version": synapse["policy_version"],
        "selected_node_ids": selected_ids,
        "selected_states": sorted(selected_states, key=lambda item: item["node_id"]),
        "edges": relevant_edges,
    }


def _load_index(
    index_path: Path,
    wiki_root: Optional[Path] = None,
    source_records: Optional[Mapping[str, synapse_engine.SourceRecord]] = None,
) -> Dict[str, str]:
    source = None
    if wiki_root is not None and source_records is not None:
        relative = _rel(index_path, wiki_root)
        source = source_records.get(relative)
        if source is None and _is_workspace_source_ref(relative):
            return {}
    data = source.text if source is not None else _read(index_path)
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


def _collect_static_context(
    wiki_root: Path,
    workspace: str,
    packs: List[str],
    components: Optional[List[str]] = None,
    source_records: Optional[Mapping[str, synapse_engine.SourceRecord]] = None,
) -> List[Dict]:
    """Collect deterministic non-volatile sources for materialized packs."""
    components = components or []
    sources: List[Tuple[Path, str]] = [
        (wiki_root / "workspaces" / workspace / "workspace.md", "workspace-profile"),
        (wiki_root / "agents" / "system-prompt.md", "engine-guidance"),
        (wiki_root / "agents" / "constraints.md", "engine-rule"),
        (wiki_root / "agents" / "coding-rules.md", "engine-rule"),
        (wiki_root / "agents" / "pipeline" / "validator-rules.md", "engine-rule"),
        (
            wiki_root / "workspaces" / workspace / "agents" / "constraints.md",
            "workspace-rule",
        ),
        (
            wiki_root / "workspaces" / workspace / "agents" / "coding-rules.md",
            "workspace-rule",
        ),
        (
            wiki_root
            / "workspaces"
            / workspace
            / "agents"
            / "pipeline"
            / "validator-rules.md",
            "workspace-rule",
        ),
    ]

    docs: List[Dict] = []
    for path, category in sources:
        item = _doc(path, category, wiki_root, source_records=source_records)
        if item is not None:
            docs.append(_slice_doc(item))

    for pack_name in packs:
        pack_dir = wiki_root / "packs" / pack_name
        manifest_path = pack_dir / "pack.yaml"
        manifest = _load_pack_manifest(manifest_path)
        manifest_item = _doc(
            manifest_path,
            "pack-rule",
            wiki_root,
            source_records=source_records,
        )
        if _uses_canonical_pack_knowledge(manifest):
            if manifest_item is not None:
                docs.append(_slice_pack_manifest(manifest_item, manifest, components))
            files = manifest.get("files") or {}
            knowledge_rel = files.get("knowledge") if isinstance(files, dict) else None
            if (
                isinstance(knowledge_rel, str)
                and knowledge_rel
                and not Path(knowledge_rel).is_absolute()
                and ".." not in Path(knowledge_rel).parts
            ):
                knowledge_item = _doc(
                    pack_dir / knowledge_rel,
                    "pack-knowledge",
                    wiki_root,
                    source_records=source_records,
                )
                if knowledge_item is not None:
                    docs.append(_slice_pack_knowledge(
                        knowledge_item,
                        manifest.get("components") or [],
                        components,
                    ))
            continue

        legacy_sources = [
            (manifest_path, "pack-rule"),
            (pack_dir / "agents" / "constraints.md", "pack-rule"),
            (pack_dir / "agents" / "coding-rules.md", "pack-rule"),
            (pack_dir / "agents" / "common-pitfalls.md", "pack-rule"),
        ]
        for path, category in legacy_sources:
            item = _doc(path, category, wiki_root, source_records=source_records)
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
    pack_sources: List[Dict] = []
    seen_paths: set[str] = set()
    # Materialization uses the same order. Static guidance owns a duplicate
    # path so the source manifest, budget report, and compiled markdown agree.
    for doc in static_docs + docs:
        path = str(doc.get("path") or "")
        if not path or path in seen_paths:
            continue
        seen_paths.add(path)
        pack_sources.append(doc)
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
            "workspace-rule", "pack-metadata", "pack-knowledge",
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


def build_context_snapshot(
    task: str,
    wiki_root: Path,
    workspace: str,
    packs: List[str],
    project_dir: Optional[Path] = None,
    warnings: Optional[List[str]] = None,
    include_selection_trace: bool = False,
    synapse_as_of: Optional[date] = None,
) -> Tuple[Dict, Dict]:
    """Build one immutable context artifact + synapse snapshot pair.

    Both outputs share the same full-workspace synapse build. Callers that
    materialize should pass the returned synapse to ``materialize_context`` so
    writing artifacts never rescans or rehashes workspace source files.
    """
    workspace_dir = synapse_engine.resolve_workspace_dir(wiki_root, workspace)
    if workspace_dir is None or not workspace_dir.is_dir():
        raise ValueError(
            f"Invalid or missing workspace {workspace!r}; context build refused."
        )
    warnings_out = list(warnings or [])
    intent_scores = _intent_scores(task)
    intent_type = _pick_by_precedence(intent_scores, INTENT_PRECEDENCE, "implement_feature")
    components = detect_components(task, wiki_root, packs)
    domain, scope = detect_scope(task, wiki_root, workspace)
    workstream_scores = _workstream_scores(task, packs, components)
    workstream = _pick_by_precedence(workstream_scores, WORKSTREAM_PRECEDENCE, "engineering")
    meta = WORKSTREAM_PRIORITY.get(workstream, WORKSTREAM_PRIORITY["engineering"])
    synapse_build = synapse_engine.build_synapse_snapshot(
        wiki_root,
        workspace,
        as_of=synapse_as_of,
    )
    synapse = synapse_build.graph
    candidates, gaps = _collect_candidates(
        intent_type,
        wiki_root,
        workspace,
        packs,
        components=components,
        domain=domain,
        project=scope,
        warnings=warnings_out,
        source_records=synapse_build.sources_by_path,
    )
    _attach_synapse_metadata(candidates, synapse_build.lookups)
    candidates = _expand_replacement_candidates(
        candidates,
        synapse_build.lookups,
        wiki_root,
        gaps,
        warnings_out,
        source_records=synapse_build.sources_by_path,
    )
    selected, selection_trace, budget_report = _rank_budget_trace(
        candidates, task, components, workstream=workstream,
    )
    docs = [_slice_doc(doc) for doc in selected]
    static_docs = _collect_static_context(
        wiki_root,
        workspace,
        packs,
        components=components,
        source_records=synapse_build.sources_by_path,
    )
    _attach_synapse_metadata(static_docs, synapse_build.lookups)
    budget_report = _finalize_budget_report(budget_report, docs, static_docs)
    warnings_out.extend(_selected_state_warnings(docs))
    for diagnostic in synapse.get("diagnostics", []):
        if diagnostic.get("severity") == "error":
            warnings_out.append(
                f"Synapse {diagnostic['code']}: {diagnostic['message']}"
            )
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
            "classification": {
                "intent": _classification_summary(intent_scores, intent_type),
                "workstream": _classification_summary(workstream_scores, workstream),
            },
        },
        "referenced_docs": docs,
        "static_context": static_docs,
        "gaps": gaps,
        "warnings": warnings_out,
        "synapse": {
            "artifact_type": "contextd_synapse_ref.v1",
            "version": "1",
            "policy_version": synapse["policy_version"],
            "synapse_hash": synapse["synapse_hash"],
            "as_of": synapse["as_of"],
            "ref": None,
            "status": "not_materialized",
            "summary": synapse["summary"],
        },
        "context_projection": _context_projection(synapse, docs),
        "contextPack": context_pack,
        "retrieval_policy": {
            "mode": "deterministic-file-backed",
            "advisory_retrieval": False,
            "priority": meta["priority"],
            "max_docs": 7,
            "rag_policy": "advisory-only-disabled-by-default",
            "lifecycle_policy": {
                "version": synapse["policy_version"],
                "score_adjustments": dict(SYNAPSE_SCORE_ADJUSTMENTS),
                "replacement_traversal_depth": 1,
            },
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
    return artifact, synapse


def build_context_artifact(
    task: str,
    wiki_root: Path,
    workspace: str,
    packs: List[str],
    project_dir: Optional[Path] = None,
    warnings: Optional[List[str]] = None,
    include_selection_trace: bool = False,
    synapse_as_of: Optional[date] = None,
) -> Dict:
    """Build the canonical JSON context artifact without exposing build state."""
    artifact, _ = build_context_snapshot(
        task=task,
        wiki_root=wiki_root,
        workspace=workspace,
        packs=packs,
        project_dir=project_dir,
        warnings=warnings,
        include_selection_trace=include_selection_trace,
        synapse_as_of=synapse_as_of,
    )
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
        "synapse_hash": artifact["synapse"]["synapse_hash"],
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
    ]
    synapse_ref = artifact.get("synapse") or {}
    if synapse_ref.get("synapse_hash"):
        lines.append(
            f"- **Synapse**: `{synapse_ref['synapse_hash'][:16]}` "
            f"({synapse_ref.get('status', 'unknown')})"
        )
    budget = artifact.get("budget_report") or {}
    if budget:
        lines.append(
            "- **Estimated Context**: "
            f"~{budget.get('estimated_tokens_referenced', 0)} referenced + "
            f"~{budget.get('estimated_tokens_static', 0)} static = "
            f"~{budget.get('estimated_tokens_total', 0)} total tokens"
        )
    lines.extend(["", "## Relevant Knowledge", ""])
    for doc in artifact.get("referenced_docs", []):
        sections = ", ".join(doc.get("sections") or ["all"])
        lines.append(f"### [{doc['category']}] {doc['path']}")
        state = doc.get("synapse") or {}
        state_text = ""
        if state:
            state_text = (
                f"; node: {state['node_id']}; lifecycle: {state['lifecycle']}"
                f"; freshness: {state['freshness']}"
            )
        lines.append(
            f"_Sections: {sections}; sha256: {doc['source_hash'][:12]}{state_text}_"
        )
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


def _same_knowledge_root(artifact: Dict, synapse_snapshot: Dict) -> bool:
    artifact_root = artifact.get("knowledge_root")
    snapshot_root = synapse_snapshot.get("knowledge_root")
    if not isinstance(artifact_root, str) or not isinstance(snapshot_root, str):
        return False
    try:
        return Path(artifact_root).resolve() == Path(snapshot_root).resolve()
    except (OSError, RuntimeError):
        return False


def _artifact_sources_match_snapshot(artifact: Dict, synapse_snapshot: Dict) -> bool:
    """Verify workspace docs in the artifact came from the supplied graph."""
    workspace = artifact.get("workspace")
    if not isinstance(workspace, str) or not workspace:
        return False
    prefix = f"workspaces/{workspace}/"
    nodes = synapse_engine.nodes_by_path(synapse_snapshot)
    referenced_docs = artifact.get("referenced_docs") or []
    static_context = artifact.get("static_context") or []
    if not isinstance(referenced_docs, list) or not isinstance(static_context, list):
        return False
    docs = referenced_docs + static_context
    expected_source_hashes: Dict[str, str] = {}
    for doc in docs:
        if not isinstance(doc, dict):
            return False
        path = doc.get("path")
        source_hash = doc.get("source_hash")
        if not isinstance(path, str) or not isinstance(source_hash, str):
            return False
        expected_source_hashes[path] = source_hash
        if not path.startswith(prefix):
            continue
        node = nodes.get(path)
        if node is None or node.get("source_hash") != source_hash:
            return False
        if doc.get("synapse") != _synapse_state(node):
            return False
    return artifact.get("source_hashes") == expected_source_hashes


def _artifact_projection_matches_snapshot(artifact: Dict, synapse_snapshot: Dict) -> bool:
    referenced_docs = artifact.get("referenced_docs")
    if not isinstance(referenced_docs, list):
        return False
    try:
        expected = _context_projection(synapse_snapshot, referenced_docs)
    except (KeyError, TypeError):
        return False
    return artifact.get("context_projection") == expected


def materialize_context(
    artifact: Dict,
    project_dir: Path,
    *,
    synapse_snapshot: Optional[Dict] = None,
) -> Dict:
    """Write context outputs from an already-built immutable snapshot.

    Materialization is intentionally write-only: it never rescans canonical
    workspace sources. Callers that need ``synapse.json`` pass the graph
    returned by ``build_context_snapshot``. Without it, the task artifacts are
    still materialized and the synapse reference remains not_materialized.
    """
    context_dir = project_dir / ".contextd" / "context"
    packs_dir = context_dir / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    pack_path = packs_dir / f"{artifact['contextPack']['packKey']}.md"
    atomic_write_text(pack_path, _pack_markdown(artifact))

    artifact = json.loads(json.dumps(artifact, ensure_ascii=False))
    rel_pack = pack_path.relative_to(project_dir).as_posix()
    artifact["contextPack"]["ref"] = rel_pack
    artifact["contextPack"]["compiledRef"] = rel_pack
    artifact["contextPack"]["status"] = "materialized"

    synapse_ref = artifact.get("synapse") or {}
    synapse_path: Optional[Path] = None
    if synapse_snapshot is not None:
        snapshot_matches = (
            synapse_snapshot.get("artifact_type") == "contextd_synapse.v1"
            and synapse_snapshot.get("workspace") == artifact.get("workspace")
            and _same_knowledge_root(artifact, synapse_snapshot)
            and synapse_snapshot.get("synapse_hash") == synapse_ref.get("synapse_hash")
            and synapse_snapshot.get("as_of") == synapse_ref.get("as_of")
            and synapse_snapshot.get("policy_version") == synapse_ref.get("policy_version")
            and (artifact.get("context_projection") or {}).get("source_synapse_hash")
            == synapse_ref.get("synapse_hash")
            and synapse_engine.compute_synapse_hash(synapse_snapshot)
            == synapse_snapshot.get("synapse_hash")
            and _artifact_sources_match_snapshot(artifact, synapse_snapshot)
            and _artifact_projection_matches_snapshot(artifact, synapse_snapshot)
        )
        if snapshot_matches:
            synapse_path = synapse_engine.materialize_synapse(synapse_snapshot, project_dir)
            synapse_ref["ref"] = synapse_path.relative_to(project_dir).as_posix()
            synapse_ref["status"] = "materialized"
        else:
            synapse_ref["ref"] = None
            synapse_ref["status"] = "drifted"
            artifact.setdefault("warnings", []).append(
                "Synapse snapshot does not match the context artifact; "
                "materialization refused. Rerun contextd context."
            )
    else:
        synapse_ref["ref"] = None
        synapse_ref["status"] = "not_materialized"

    json_path = context_dir / "current-task.json"
    md_path = context_dir / "current-task.md"
    artifact["materialized"] = {
        "json": json_path.relative_to(project_dir).as_posix(),
        "markdown": md_path.relative_to(project_dir).as_posix(),
        "pack": rel_pack,
    }
    if synapse_path is not None:
        artifact["materialized"]["synapse"] = synapse_path.relative_to(project_dir).as_posix()
    atomic_write_text(json_path, json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")
    atomic_write_text(md_path, render_markdown(artifact))
    return artifact


def build_task_context(task: str, wiki_root: Path, workspace: str,
                       packs: List[str]) -> str:
    """Legacy API: return rendered Markdown."""
    artifact = build_context_artifact(task, wiki_root, workspace, packs)
    return render_markdown(artifact)
