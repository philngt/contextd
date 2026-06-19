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
    "pitfalls": 1,
    "common-pitfalls": 1,
    "workspace-profile": 2,
    "engine-guidance": 2,
    "engine-rule": 1,
    "pack-rule": 1,
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


def _iter_files(base: Path, patterns: Iterable[str]) -> List[Path]:
    if not base.exists():
        return []
    out: List[Path] = []
    for pattern in patterns:
        out.extend(sorted(p for p in base.glob(pattern) if p.is_file()))
    return out


def _doc(path: Path, category: str, wiki_root: Path) -> Optional[Dict]:
    text = _read(path)
    if text is None:
        return None
    return {
        "category": category,
        "path": _rel(path, wiki_root),
        "abs_path": path,
        "content_full": text,
        "source_hash": _sha256_text(text),
    }


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


def _collect_candidates(intent: str, wiki_root: Path, workspace: str,
                        packs: List[str]) -> Tuple[List[Dict], List[Dict]]:
    ws_dir = wiki_root / "workspaces" / workspace
    candidates: List[Dict] = []
    gaps: List[Dict] = []

    def add_many(paths: List[Path], category: str) -> None:
        for path in paths:
            item = _doc(path, category, wiki_root)
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


def _rank_and_budget(candidates: List[Dict], task: str,
                     components: List[str], max_docs: int = 7) -> List[Dict]:
    words = _keywords(task, components)
    ranked = sorted(
        candidates,
        key=lambda d: (-_score(d, words), PRIORITY.get(d["category"], 9), d["path"]),
    )
    used_by_category: Dict[str, int] = {}
    out: List[Dict] = []
    seen: set[str] = set()
    for doc in ranked:
        if doc["path"] in seen:
            continue
        category = doc["category"]
        budget = CATEGORY_BUDGETS.get(category, 1)
        if used_by_category.get(category, 0) >= budget:
            continue
        out.append(doc)
        seen.add(doc["path"])
        used_by_category[category] = used_by_category.get(category, 0) + 1
        if len(out) >= max_docs:
            break
    return out


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
    return {
        "category": category,
        "path": doc["path"],
        "sections": selected_sections,
        "content": sliced,
        "source_hash": doc["source_hash"],
    }


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
            "architecture", "decision", "runbook", "pitfalls", "common-pitfalls",
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
) -> Dict:
    """Build the canonical JSON context artifact."""
    warnings_out = list(warnings or [])
    intent_type = detect_intent(task)
    components = detect_components(task, wiki_root, packs)
    candidates, gaps = _collect_candidates(intent_type, wiki_root, workspace, packs)
    selected = _rank_and_budget(candidates, task, components)
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
            "domain": None,
            "scope": None,
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
            "priority": ["contracts", "patterns", "project_docs", "domain_knowledge"],
            "max_docs": 7,
            "rag_policy": "advisory-only-disabled-by-default",
        },
        "source_hashes": source_hashes,
    }
    return artifact


def render_markdown(artifact: Dict) -> str:
    lines: List[str] = [
        "# Task Context",
        "",
        "## Task",
        f"> {artifact['task']}",
        "",
        "## Detected Intent",
        f"- **Type**: `{artifact['intent']['type']}`",
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
