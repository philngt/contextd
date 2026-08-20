#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic, file-backed lifecycle graph for workspace knowledge."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .atomic_write import atomic_write_text
from .contextd_resolver import (
    is_valid_workspace_name as _is_valid_workspace_name,
    resolve_workspace_dir as _resolve_workspace_dir,
)
from .context_security import block_reason
from .frontmatter import split_frontmatter


ARTIFACT_TYPE = "contextd_synapse.v1"
VERSION = "1"
POLICY_VERSION = "synapse-lifecycle.v1"

LIFECYCLES = frozenset({"draft", "active", "deprecated", "superseded"})
FRESHNESS_STATES = frozenset({"fresh", "stale", "unknown"})
EDGE_TYPES = frozenset({
    "supersedes",
    "supports",
    "contradicts",
    "implements",
    "depends_on",
    "derived_from",
    "related_to",
})

_NODE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_RUNTIME_NAMES = frozenset({"checkpoint.json", "todo.json"})
_EXCLUDED_TOP_LEVEL = frozenset({".observations", "reports", "eval"})


@dataclass(frozen=True)
class SourceRecord:
    """Raw-hash + decoded text captured during one workspace scan."""

    text: str
    source_hash: str


@dataclass(frozen=True)
class SynapseLookups:
    """Precomputed graph indexes reused during one context build."""

    nodes_by_path: Dict[str, Dict]
    nodes_by_id: Dict[str, Dict]
    replacements_by_target: Dict[str, Tuple[str, ...]]


@dataclass(frozen=True)
class SynapseBuildSnapshot:
    """Public graph plus transient source records from the same scan."""

    graph: Dict
    sources_by_path: Dict[str, SourceRecord]
    lookups: SynapseLookups


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def compute_synapse_hash(synapse: Dict) -> str:
    """Return the deterministic content hash for an in-memory snapshot."""
    payload = {
        "version": synapse.get("version"),
        "policy_version": synapse.get("policy_version"),
        "workspace": synapse.get("workspace"),
        "as_of": synapse.get("as_of"),
        "nodes": synapse.get("nodes"),
        "edges": synapse.get("edges"),
    }
    return _sha256(json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ))


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _diagnostic(
    severity: str,
    code: str,
    message: str,
    path: Optional[str] = None,
    **details,
) -> Dict:
    item = {"severity": severity, "code": code, "message": message}
    if path:
        item["path"] = path
    item.update({key: value for key, value in details.items() if value is not None})
    return item


def _is_governed_source(path: Path, workspace_dir: Path) -> bool:
    relative = path.relative_to(workspace_dir)
    parts = relative.parts
    if not parts or parts[0] in _EXCLUDED_TOP_LEVEL:
        return False
    if any(part.startswith(".") for part in parts):
        return False
    if len(parts) >= 2 and parts[0] == "evidence" and parts[1] == "sources":
        return False
    if path.name in _RUNTIME_NAMES:
        return False
    if path.suffix.lower() == ".md":
        return True
    return (
        path.suffix.lower() in {".json", ".yaml", ".yml"}
        and "contracts" in parts
    )


def _source_paths(workspace_dir: Path) -> List[Path]:
    if not workspace_dir.is_dir():
        return []
    return sorted(
        path for path in workspace_dir.rglob("*")
        if path.is_file() and _is_governed_source(path, workspace_dir)
    )


def _kind(path: Path, workspace_dir: Path, metadata: Dict) -> str:
    declared = metadata.get("type")
    if isinstance(declared, str) and declared.strip():
        return declared.strip().lower().replace(" ", "-")
    relative = path.relative_to(workspace_dir)
    parts = relative.parts
    path_text = relative.as_posix().lower()
    if "contracts" in parts:
        return "contract"
    if "patterns" in parts:
        return "pattern"
    if "decisions" in parts:
        return "decision"
    if "runbooks" in parts:
        return "runbook"
    if "requirements" in parts:
        return "requirement"
    if "product" in parts:
        return "product"
    if "design" in parts:
        return "design"
    if "domains" in parts:
        return "domain"
    if "services" in parts:
        return "service"
    if "projects" in parts:
        return "project"
    if "evidence" in parts:
        return "evidence"
    if path_text.endswith("workspace.md"):
        return "workspace-profile"
    return "doc"


def _fallback_node_id(workspace: str, path: Path, workspace_dir: Path) -> str:
    relative = path.relative_to(workspace_dir).as_posix()
    normalized = re.sub(r"[^A-Za-z0-9._:-]+", ".", relative.replace("/", "."))
    normalized = normalized.strip(".") or "root"
    # Normalization alone is not injective (for example, ``a b.md`` and
    # ``a.b.md``). Keep the readable path slug and bind it to the exact path.
    return f"{workspace}:{normalized}:{_sha256(relative)[:10]}"


def is_valid_workspace_name(workspace: str) -> bool:
    return _is_valid_workspace_name(workspace)


def resolve_workspace_dir(wiki_root: Path, workspace: str) -> Optional[Path]:
    """Resolve a direct child workspace without allowing traversal/symlink escape."""
    return _resolve_workspace_dir(wiki_root, workspace)


def _title(path: Path, metadata: Dict, body: str) -> str:
    declared = metadata.get("title")
    if isinstance(declared, str) and declared.strip():
        return declared.strip()
    heading = _H1_RE.search(body)
    return heading.group(1).strip() if heading else path.stem


def _parse_date(value: object) -> Optional[date]:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            return None


def _lifecycle(metadata: Dict, path: str, diagnostics: List[Dict]) -> str:
    explicit = metadata.get("lifecycle")
    if isinstance(explicit, str) and explicit.strip():
        normalized = explicit.strip().lower()
        if normalized in LIFECYCLES:
            return normalized
        diagnostics.append(_diagnostic(
            "warning",
            "invalid-lifecycle",
            f"Unsupported lifecycle {explicit!r}; using status/default mapping.",
            path,
        ))
    status = metadata.get("status")
    if not isinstance(status, str) or not status.strip() or status.strip().lower() == "stable":
        return "active"
    normalized = status.strip().lower()
    if normalized in LIFECYCLES:
        return normalized
    diagnostics.append(_diagnostic(
        "warning",
        "invalid-status",
        f"Unsupported status {status!r}; defaulting lifecycle to active.",
        path,
    ))
    return "active"


def _freshness(
    metadata: Dict,
    as_of: date,
    path: str,
    diagnostics: List[Dict],
) -> tuple[str, Optional[str]]:
    explicit = metadata.get("freshness")
    normalized: Optional[str] = None
    if isinstance(explicit, str) and explicit.strip():
        candidate = explicit.strip().lower()
        if candidate in FRESHNESS_STATES:
            normalized = candidate
        else:
            diagnostics.append(_diagnostic(
                "warning",
                "invalid-freshness",
                f"Unsupported freshness {explicit!r}; defaulting to unknown.",
                path,
            ))

    raw_review_by = metadata.get("review_by")
    review_by = _parse_date(raw_review_by)
    if raw_review_by and review_by is None:
        diagnostics.append(_diagnostic(
            "warning",
            "invalid-review-by",
            f"Invalid review_by date {raw_review_by!r}; freshness cannot use it.",
            path,
        ))

    if normalized == "stale":
        state = "stale"
    elif review_by is not None and review_by < as_of:
        state = "stale"
    elif normalized is not None:
        state = normalized
    elif review_by is not None:
        state = "fresh"
    else:
        state = "unknown"
    return state, review_by.isoformat() if review_by else None


def _requested_relations(metadata: Dict, path: str, diagnostics: List[Dict]) -> List[Dict]:
    raw = metadata.get("relations")
    if raw in (None, ""):
        return []
    if not isinstance(raw, list):
        diagnostics.append(_diagnostic(
            "warning",
            "invalid-relations",
            "relations must be a YAML list of {type, target} mappings.",
            path,
        ))
        return []
    relations: List[Dict] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            diagnostics.append(_diagnostic(
                "warning",
                "invalid-relation",
                f"Relation at index {index} is not a mapping.",
                path,
            ))
            continue
        edge_type = item.get("type")
        target = item.get("target")
        if not isinstance(edge_type, str) or edge_type.strip() not in EDGE_TYPES:
            diagnostics.append(_diagnostic(
                "warning",
                "invalid-edge-type",
                f"Relation at index {index} has unsupported type {edge_type!r}.",
                path,
            ))
            continue
        if not isinstance(target, str) or not target.strip():
            diagnostics.append(_diagnostic(
                "warning",
                "invalid-edge-target",
                f"Relation at index {index} has no target node ID.",
                path,
            ))
            continue
        relations.append({"type": edge_type.strip(), "target": target.strip()})
    return relations


def _normalize_cross_workspace_target(
    target: str,
    workspace: str,
) -> tuple[Optional[str], Optional[str]]:
    if not target.startswith("workspace://"):
        return target, None
    remainder = target[len("workspace://"):]
    target_workspace, separator, node_id = remainder.partition("/")
    if not separator or not target_workspace or not node_id:
        return None, "invalid"
    if target_workspace != workspace:
        return None, target_workspace
    return node_id, None


def _cyclic_supersede_edges(edges: List[Dict]) -> set[str]:
    supersedes = [edge for edge in edges if edge["type"] == "supersedes"]
    adjacency: Dict[str, List[tuple[str, str]]] = defaultdict(list)
    for edge in supersedes:
        adjacency[edge["source"]].append((edge["target"], edge["id"]))

    next_index = 0
    indexes: Dict[str, int] = {}
    lowlinks: Dict[str, int] = {}
    stack: List[str] = []
    on_stack: set[str] = set()
    components: List[set[str]] = []

    def strongconnect(node: str) -> None:
        nonlocal next_index
        indexes[node] = next_index
        lowlinks[node] = next_index
        next_index += 1
        stack.append(node)
        on_stack.add(node)

        for target, _ in adjacency.get(node, []):
            if target not in indexes:
                strongconnect(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[target])

        if lowlinks[node] != indexes[node]:
            return
        component: set[str] = set()
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.add(member)
            if member == node:
                break
        components.append(component)

    all_nodes = sorted({
        node_id
        for edge in supersedes
        for node_id in (edge["source"], edge["target"])
    })
    for node in all_nodes:
        if node not in indexes:
            strongconnect(node)

    cyclic: set[str] = set()
    cyclic_components = [component for component in components if len(component) > 1]
    for component in cyclic_components:
        cyclic.update(
            edge["id"] for edge in supersedes
            if edge["source"] in component and edge["target"] in component
        )
    return cyclic


def build_synapse_snapshot(
    wiki_root: Path,
    workspace: str,
    *,
    as_of: Optional[date] = None,
) -> SynapseBuildSnapshot:
    """Build a graph and retain decoded sources from the exact same scan."""
    wiki_root = wiki_root.resolve()
    workspace_dir = resolve_workspace_dir(wiki_root, workspace)
    evaluation_date = as_of or datetime.now(timezone.utc).date()
    diagnostics: List[Dict] = []
    provisional: List[Dict] = []
    sources_by_path: Dict[str, SourceRecord] = {}

    workspace_safe = workspace_dir is not None
    if not workspace_safe:
        diagnostics.append(_diagnostic(
            "error",
            "invalid-workspace",
            f"Invalid workspace name {workspace!r}; synapse build refused.",
        ))
    elif not workspace_dir.is_dir():
        diagnostics.append(_diagnostic(
            "error",
            "missing-workspace",
            f"Workspace directory does not exist: {workspace_dir}",
        ))

    for path in _source_paths(workspace_dir) if workspace_dir is not None else []:
        relative = _rel(path, wiki_root)
        resolved_path = path.resolve()
        if not resolved_path.is_relative_to(workspace_dir):
            diagnostics.append(_diagnostic(
                "error",
                "source-outside-workspace",
                "Source resolves outside the active workspace and was omitted.",
                relative,
            ))
            continue
        reason = block_reason(path) or block_reason(resolved_path)
        if reason:
            diagnostics.append(_diagnostic(
                "warning",
                "blocked-source",
                f"Source omitted by security policy: {reason}",
                relative,
            ))
            continue
        try:
            raw_source = path.read_bytes()
            text = raw_source.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            diagnostics.append(_diagnostic(
                "warning",
                "unreadable-source",
                f"Could not read source: {exc}",
                relative,
            ))
            continue
        source_hash = _sha256_bytes(raw_source)
        sources_by_path[relative] = SourceRecord(
            text=text,
            source_hash=source_hash,
        )

        metadata, body = split_frontmatter(text)
        metadata = metadata or {}
        requested_id = metadata.get("node_id")
        fallback_id = _fallback_node_id(workspace, path, workspace_dir)
        if isinstance(requested_id, str) and _NODE_ID_RE.fullmatch(requested_id.strip()):
            node_id = requested_id.strip()
            id_source = "frontmatter"
        else:
            node_id = fallback_id
            id_source = "path"
            if requested_id not in (None, ""):
                diagnostics.append(_diagnostic(
                    "warning",
                    "invalid-node-id",
                    f"Invalid node_id {requested_id!r}; using path-derived ID.",
                    relative,
                ))

        lifecycle = _lifecycle(metadata, relative, diagnostics)
        freshness, review_by = _freshness(metadata, evaluation_date, relative, diagnostics)
        node = {
            "id": node_id,
            "workspace": workspace,
            "kind": _kind(path, workspace_dir, metadata),
            "title": _title(path, metadata, body),
            "path": relative,
            "source_hash": source_hash,
            "memory_class": "long_term",
            "lifecycle": lifecycle,
            "freshness": freshness,
            "review_by": review_by,
            "id_source": id_source,
            "_fallback_id": fallback_id,
            "_relations": _requested_relations(metadata, relative, diagnostics),
        }
        provisional.append(node)

    by_requested_id: Dict[str, List[Dict]] = defaultdict(list)
    for node in provisional:
        by_requested_id[node["id"]].append(node)
    for requested_id, group in sorted(by_requested_id.items()):
        if len(group) < 2:
            continue
        paths = sorted(node["path"] for node in group)
        diagnostics.append(_diagnostic(
            "error",
            "duplicate-node-id",
            f"Duplicate node ID {requested_id!r}; conflicting nodes use path-derived IDs.",
            paths[0],
            related_paths=paths[1:],
        ))
        for node in group:
            node["requested_node_id"] = requested_id
            node["id"] = node["_fallback_id"]
            node["id_source"] = "path"

    node_ids = {node["id"] for node in provisional}
    edges: List[Dict] = []
    seen_edges: set[tuple[str, str, str]] = set()
    for node in sorted(provisional, key=lambda item: item["path"]):
        for relation in node["_relations"]:
            target, foreign_workspace = _normalize_cross_workspace_target(
                relation["target"], workspace,
            )
            if foreign_workspace:
                code = (
                    "invalid-workspace-target"
                    if foreign_workspace == "invalid"
                    else "cross-workspace-edge"
                )
                diagnostics.append(_diagnostic(
                    "error",
                    code,
                    f"Rejected relation target {relation['target']!r}; "
                    f"edges must stay in workspace {workspace!r}.",
                    node["path"],
                ))
                continue
            if target not in node_ids:
                diagnostics.append(_diagnostic(
                    "warning",
                    "dangling-edge",
                    f"Relation target {target!r} does not resolve in workspace {workspace!r}.",
                    node["path"],
                    target=target,
                ))
                continue
            if target == node["id"]:
                diagnostics.append(_diagnostic(
                    "warning",
                    "self-edge",
                    f"Rejected self-edge {relation['type']} on {target!r}.",
                    node["path"],
                ))
                continue
            key = (relation["type"], node["id"], target)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            edge_id = _sha256("\x00".join(key))[:20]
            edges.append({
                "id": edge_id,
                "type": relation["type"],
                "source": node["id"],
                "target": target,
            })

    cyclic_ids = _cyclic_supersede_edges(edges)
    if cyclic_ids:
        cyclic_edges = [edge for edge in edges if edge["id"] in cyclic_ids]
        diagnostics.append(_diagnostic(
            "error",
            "supersede-cycle",
            "Rejected supersedes cycle from traversable edges.",
            edge_ids=sorted(cyclic_ids),
            node_ids=sorted({
                value
                for edge in cyclic_edges
                for value in (edge["source"], edge["target"])
            }),
        ))
        edges = [edge for edge in edges if edge["id"] not in cyclic_ids]

    nodes: List[Dict] = []
    for item in sorted(provisional, key=lambda node: (node["id"], node["path"])):
        node = {key: value for key, value in item.items() if not key.startswith("_")}
        nodes.append(node)
    edges.sort(key=lambda edge: (edge["type"], edge["source"], edge["target"]))
    diagnostics.sort(key=lambda item: (
        {"error": 0, "warning": 1, "info": 2}.get(item["severity"], 9),
        item["code"],
        item.get("path", ""),
        item["message"],
    ))

    lifecycle_counts = dict(sorted(Counter(node["lifecycle"] for node in nodes).items()))
    freshness_counts = dict(sorted(Counter(node["freshness"] for node in nodes).items()))
    edge_counts = dict(sorted(Counter(edge["type"] for edge in edges).items()))
    hash_payload = {
        "version": VERSION,
        "policy_version": POLICY_VERSION,
        "workspace": workspace,
        "as_of": evaluation_date.isoformat(),
        "nodes": nodes,
        "edges": edges,
    }
    synapse_hash = compute_synapse_hash(hash_payload)
    graph = {
        "artifact_type": ARTIFACT_TYPE,
        "version": VERSION,
        "policy_version": POLICY_VERSION,
        "generated_at": _now(),
        "as_of": evaluation_date.isoformat(),
        "workspace": workspace,
        "knowledge_root": str(wiki_root),
        "synapse_hash": synapse_hash,
        "nodes": nodes,
        "edges": edges,
        "diagnostics": diagnostics,
        "summary": {
            "nodes": len(nodes),
            "edges": len(edges),
            "diagnostics": len(diagnostics),
            "errors": sum(1 for item in diagnostics if item["severity"] == "error"),
            "warnings": sum(1 for item in diagnostics if item["severity"] == "warning"),
            "lifecycle": lifecycle_counts,
            "freshness": freshness_counts,
            "edge_types": edge_counts,
        },
    }
    return SynapseBuildSnapshot(
        graph=graph,
        sources_by_path=sources_by_path,
        lookups=build_synapse_lookups(graph),
    )


def build_synapse_index(
    wiki_root: Path,
    workspace: str,
    *,
    as_of: Optional[date] = None,
) -> Dict:
    """Backward-compatible public graph builder."""
    return build_synapse_snapshot(wiki_root, workspace, as_of=as_of).graph


def nodes_by_path(synapse: Dict) -> Dict[str, Dict]:
    return {node["path"]: node for node in synapse.get("nodes", [])}


def nodes_by_id(synapse: Dict) -> Dict[str, Dict]:
    return {node["id"]: node for node in synapse.get("nodes", [])}


def build_synapse_lookups(synapse: Dict) -> SynapseLookups:
    """Build path, ID, and active-replacement indexes in one graph pass."""
    by_path = nodes_by_path(synapse)
    by_id = nodes_by_id(synapse)
    replacements: Dict[str, List[str]] = defaultdict(list)
    for edge in synapse.get("edges", []):
        if edge.get("type") != "supersedes":
            continue
        source = edge.get("source")
        target = edge.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        if by_id.get(source, {}).get("lifecycle") != "active":
            continue
        replacements[target].append(source)
    return SynapseLookups(
        nodes_by_path=by_path,
        nodes_by_id=by_id,
        replacements_by_target={
            target: tuple(sorted(set(source_ids)))
            for target, source_ids in replacements.items()
        },
    )


def replacement_node_ids(synapse: Dict, node_id: str) -> List[str]:
    """Return active nodes that declare they supersede ``node_id``."""
    lookups = build_synapse_lookups(synapse)
    return list(lookups.replacements_by_target.get(node_id, ()))


def materialize_synapse(synapse: Dict, project_dir: Path) -> Path:
    output = project_dir / ".contextd" / "context" / "synapse.json"
    atomic_write_text(output, json.dumps(synapse, indent=2, ensure_ascii=False) + "\n")
    return output


def render_text(synapse: Dict) -> str:
    summary = synapse.get("summary", {})
    lines = [
        f"Synapse: {synapse.get('synapse_hash', '')}",
        f"Workspace: {synapse.get('workspace', '')}",
        f"As of: {synapse.get('as_of', '')}",
        f"Nodes: {summary.get('nodes', 0)}",
        f"Edges: {summary.get('edges', 0)}",
        f"Diagnostics: {summary.get('diagnostics', 0)} "
        f"({summary.get('errors', 0)} errors, {summary.get('warnings', 0)} warnings)",
        "Lifecycle: " + json.dumps(summary.get("lifecycle", {}), sort_keys=True),
        "Freshness: " + json.dumps(summary.get("freshness", {}), sort_keys=True),
    ]
    return "\n".join(lines) + "\n"
