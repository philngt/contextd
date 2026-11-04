"""Report retrieval support without claiming closed-world knowledge coverage.

The report describes the context actually selected, not whether a task is
answerable. Literal matches, declared routes and checked evidence are distinct.
"""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Callable, Dict, List, Mapping, Optional

from .context_payload import compiled_sources


def assess(
    words: List[str], referenced: List[Dict], static: List[Dict],
    trace: Mapping, oes: Optional[Mapping], matches: Callable[[str, str], bool],
) -> tuple[Dict, List[Dict]]:
    referenced_by_path = {doc["path"]: doc for doc in referenced}
    support = []
    matched = set()
    basis = set()
    for doc in compiled_sources(static, referenced):
        # General workspace/engine guidance does not support a particular task.
        scoped_pack = doc.get("category") == "pack-knowledge" and any(
            title.startswith("Component:") for title in doc.get("sections", [])
        )
        if doc["path"] not in referenced_by_path and not scoped_pack:
            continue
        terms = {word for word in words if matches(
            word, PurePosixPath(doc["path"]).stem + "\n" + doc.get("content", ""),
        )}
        routes = set((doc.get("relevance") or {}).get("basis", [])) - {"lexical"}
        # Static content owns duplicates, but an explicit selected route still
        # explains why that path supports this task. Recheck literal matches
        # only against the emitted copy so omitted sections cannot close a gap.
        selected = referenced_by_path.get(doc["path"], {})
        routes.update(set((selected.get("relevance") or {}).get("basis", [])) - {"lexical"})
        if scoped_pack:
            routes.add("pack_route")
        if doc.get("oes_evidence"):
            routes.add("oes")
        if terms or routes:
            support.append(doc)
            matched.update(terms)
            basis.update(routes)
            if terms:
                basis.add("lexical")

    if "oes" in basis:
        status = "evidence_match"
    elif basis & {"pack_route", "replacement"}:
        status = "declared_route"
    elif "lexical" in basis:
        status = "lexical_match"
    else:
        status = "no_match" if words else "unassessed"

    graph_status = "not_requested"
    if oes is not None:
        graph_status = (
            "matched" if "oes" in basis else
            "not_selected" if oes.get("matched_edge_ids") else "no_match"
        )
    report = {
        "status": status,
        "query_terms": list(words),
        "matched_terms": sorted(matched),
        "unmatched_terms": sorted(set(words) - matched),
        "selected_paths": sorted(doc["path"] for doc in support),
        "graph": {
            "status": graph_status,
            "matched_node_ids": list((oes or {}).get("matched_node_ids", [])),
            "matched_edge_ids": list((oes or {}).get("matched_edge_ids", [])),
        },
        "complete": False,
    }
    gaps = []
    if not support:
        eligible = any(
            (doc.get("relevance") or {}).get("basis")
            for doc in trace.get("considered_docs", [])
        )
        if eligible:
            missing = (
                "Task-specific candidates were found but no supporting content "
                "entered the selected context; inspect budget and section filters."
            )
        elif words:
            missing = (
                "No task-specific document matched the configured retrieval routes "
                "for this task. Add relevant governed sources or an evidenced graph route."
            )
        else:
            missing = (
                "Task-specific coverage could not be assessed: no specific query "
                "terms or declared routes were found. Name a system, topic or requirement."
            )
        gaps.append({"category": "knowledge-coverage", "missing": missing,
                     "blocking_hint": True})
    if graph_status in {"no_match", "not_selected"}:
        missing = (
            "The supplied OES graph has no matching evidenced assertion for this task. "
            "This is a gap in this graph's retrieval routes, not proof that the "
            "workspace has no relevant knowledge."
            if graph_status == "no_match" else
            "Matching OES evidence routes were found but none entered the selected "
            "context; inspect document budgets and selection filters."
        )
        gaps.append({"category": "oes-coverage", "missing": missing,
                     "blocking_hint": True})
    return report, gaps


def render(coverage: Optional[Mapping], gaps: List[Dict]) -> str:
    """One diagnostic payload shared by agent output, budgeting and identity."""
    lines = []
    if coverage:
        lines.extend([
            "## Retrieval Coverage", "",
            f"- Support: `{coverage['status']}`",
            f"- Graph routes: `{coverage['graph']['status']}`",
            "- Matched literal terms: " + (", ".join(coverage["matched_terms"]) or "(none)"),
            "- Unmatched literal terms: " + (", ".join(coverage["unmatched_terms"]) or "(none)"),
            "", "Coverage is incomplete. Matches indicate retrieval support, not "
            "answerability or semantic proof. Unmatched terms may have synonyms; "
            "general guidance does not establish task-specific knowledge.", "",
        ])
    if gaps:
        lines.extend(["## Knowledge Gaps", ""])
        for gap in gaps:
            marker = "blocking" if gap.get("blocking_hint") else "non-blocking"
            lines.append(f"- [{marker}] {gap['category']}: {gap['missing']}")
        lines.append("")
    elif coverage:
        lines.extend(["## Knowledge Gaps", "", "No retrieval gap detected; task coverage is not proven complete.", ""])
    return "\n".join(lines).strip()
