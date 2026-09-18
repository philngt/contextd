"""The ordered, deduplicated source view shared by hashing, budgets and output.

This module does not read files, classify tasks, or apply retrieval policy.
"""
from __future__ import annotations

import hashlib
import json
from typing import Dict, Iterable, List, Mapping, Optional


def compiled_sources(static_docs: Iterable[Dict], referenced_docs: Iterable[Dict]) -> List[Dict]:
    """Static guidance owns a duplicate path; preserve the actual output order."""
    result: List[Dict] = []
    seen: set[str] = set()
    for group in (static_docs, referenced_docs):
        for doc in group:
            path = doc.get("path")
            if not path or path in seen:
                continue
            seen.add(path)
            result.append(doc)
    return result


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_pack_ref(
    workspace: str,
    packs: List[str],
    docs: List[Dict],
    static_docs: Optional[List[Dict]] = None,
    decision_report: Optional[Mapping] = None,
) -> Dict:
    pack_sources = compiled_sources(static_docs or [], docs)
    sources = sorted(
        ({"path": doc["path"], "category": doc["category"],
          "source_hash": doc["source_hash"]} for doc in pack_sources),
        key=lambda item: item["path"],
    )
    payload = {
        "identity_version": 2,
        "workspace": workspace,
        "packs": list(packs),
        "sources": sources,
        # Do not sort this list: output order is part of the projection.
        "rendered_sources": [
            {"path": doc["path"], "sections": doc["sections"],
             "content_hash": _sha256_text(doc["content"])}
            for doc in pack_sources
        ],
        "decision_report": decision_report,
    }
    source_hash = _sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    return {
        "artifact_type": "context_pack_ref",
        "version": "1",
        "identity_version": 2,
        "packs": list(packs),
        "kind": "deterministic-static-context",
        "packKey": source_hash[:16],
        "ref": None,
        "compiledRef": None,
        "sourceHash": source_hash,
        "sources": sources,
        "status": "not_materialized",
    }


def synapse_state(node: Dict) -> Dict:
    return {
        "node_id": node["id"],
        "memory_class": node["memory_class"],
        "lifecycle": node["lifecycle"],
        "freshness": node["freshness"],
        "review_by": node.get("review_by"),
    }


def project_synapse(synapse: Dict, docs: List[Dict]) -> Dict:
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
