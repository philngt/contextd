"""Read-only bounded projections over an already validated Synapse snapshot.

This module performs no filesystem, network, model, or execution operations.
The caller owns workspace resolution, safe source scanning and hash validation.
The output is advisory graph metadata, NOT a contextd_task_context.v1 artifact.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
import hashlib
import json
import re
from typing import Mapping

ARTIFACT_TYPE = "contextd_graph_projection.v1"
POLICY_VERSION = "bounded-graph-projection.v1"
EDGE_TYPES = frozenset({"depends_on", "implements", "derived_from", "supports",
                        "contradicts", "supersedes", "related_to"})
# Reuse v1 edge semantics; do not invent causal relations from similarity.
DEFAULT_EDGE_TYPES = tuple(sorted(EDGE_TYPES - {"related_to"}))
ROLES = frozenset({"knowledge", "primitive", "mechanism", "principle", "strategy",
                   "skill", "pattern", "guideline", "constraint", "procedure",
                   "decision", "evidence", "artifact"})
KIND_ROLES = {**{role: role for role in ROLES}, "contract": "constraint",
              "runbook": "procedure"}
EDGE_PRIORITY = {"depends_on": 0, "implements": 1, "derived_from": 2,
                 "contradicts": 3, "supersedes": 4, "supports": 5, "related_to": 6}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
REGION_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


@dataclass(frozen=True)
class ProjectionRequest:
    seeds: tuple[str, ...]
    max_depth: int = 2
    max_nodes: int = 20
    edge_types: tuple[str, ...] = DEFAULT_EDGE_TYPES
    direction: str = "outgoing"
    regions: tuple[str, ...] = ()
    max_boundary_edges: int = 100

    def normalized(self) -> dict:
        for name, value, minimum, maximum in (
            ("max_depth", self.max_depth, 0, 8),
            ("max_nodes", self.max_nodes, 1, 128),
            ("max_boundary_edges", self.max_boundary_edges, 1, 1024),
        ):
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")
        for name, values in (("seeds", self.seeds), ("edge_types", self.edge_types),
                             ("regions", self.regions)):
            if not isinstance(values, (tuple, list)) or any(
                not isinstance(value, str) for value in values
            ):
                raise ValueError(f"{name} must be a sequence of strings")
        seeds = sorted(set(self.seeds))
        if not seeds or any(not ID_RE.fullmatch(seed) for seed in seeds):
            raise ValueError("At least one valid local seed node ID is required")
        if len(seeds) > self.max_nodes:
            raise ValueError("max_nodes must accommodate all explicit seeds")
        if set(self.edge_types) - EDGE_TYPES:
            raise ValueError("Unsupported edge type")
        if self.direction not in {"outgoing", "incoming", "both"}:
            raise ValueError("direction must be outgoing, incoming, or both")
        if any(not REGION_RE.fullmatch(region) for region in self.regions):
            raise ValueError("Invalid region: use lowercase letters, digits, . _ or -")
        return {"seeds": seeds, "max_depth": self.max_depth,
                "max_nodes": self.max_nodes, "edge_types": sorted(set(self.edge_types)),
                "direction": self.direction, "regions": sorted(set(self.regions)),
                "max_boundary_edges": self.max_boundary_edges}


def _annotation(node: Mapping, metadata: Mapping) -> tuple[str, list[str], list[str]]:
    """Semantic role and region are independent of OKF type and lifecycle."""
    issues = []
    role = metadata.get("knowledge_role", KIND_ROLES.get(node.get("kind"), "knowledge"))
    if not isinstance(role, str) or role not in ROLES:
        role = "knowledge"
        issues.append("invalid-knowledge-role")
    regions = metadata.get("regions", [])
    if not isinstance(regions, list) or any(
        not isinstance(value, str) or not REGION_RE.fullmatch(value) for value in regions
    ):
        regions = []
        issues.append("invalid-regions")
    return role, sorted(set(regions)), issues


def project_graph(graph: Mapping, request: ProjectionRequest,
                  metadata_by_id: Mapping[str, Mapping] | None = None) -> dict:
    """Select a deterministic BFS neighborhood; report rather than hide gaps.

    Input must come from build_synapse_snapshot, not an untrusted uploaded graph.
    No source content, arbitrary annotations, or diagnostic messages are echoed.
    Node/region/depth bounds are not a token budget or an authorization boundary.
    """
    policy = request.normalized()
    if graph.get("artifact_type") != "contextd_synapse.v1":
        raise ValueError("Expected a contextd_synapse.v1 snapshot")
    workspace = graph.get("workspace")
    if not isinstance(workspace, str) or not ID_RE.fullmatch(workspace):
        raise ValueError("Invalid snapshot workspace")
    if not isinstance(graph.get("synapse_hash"), str) or not re.fullmatch(
        r"[0-9a-f]{64}", graph["synapse_hash"]
    ):
        raise ValueError("Invalid snapshot hash")
    try:
        date.fromisoformat(graph["as_of"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid snapshot evaluation date") from exc
    metadata_by_id = metadata_by_id or {}
    nodes = {}
    annotations = {}
    metadata_issues = Counter()
    for node in graph.get("nodes", []):
        node_id = node.get("id")
        if not isinstance(node_id, str) or not ID_RE.fullmatch(node_id) or node_id in nodes:
            raise ValueError("Invalid or duplicate snapshot node ID")
        path = node.get("path", "")
        if (node.get("workspace") != workspace or not isinstance(path, str)
                or not path.startswith(f"workspaces/{workspace}/")
                or any(part in {"", ".", ".."} for part in path.split("/"))
                or "\\" in path or node.get("memory_class") != "long_term"):
            raise ValueError("Snapshot node violates workspace or memory boundary")
        if (not isinstance(node.get("source_hash"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", node["source_hash"])
                or node.get("lifecycle") not in {"active", "draft", "deprecated", "superseded"}
                or node.get("freshness") not in {"fresh", "stale", "unknown"}
                or not isinstance(node.get("kind"), str)):
            raise ValueError("Invalid snapshot node state or source hash")
        nodes[node_id] = node
        metadata = metadata_by_id.get(node_id, {})
        if not isinstance(metadata, Mapping):
            raise ValueError("Node metadata must be a mapping")
        role, regions, issues = _annotation(node, metadata)
        annotations[node_id] = (role, regions)
        metadata_issues.update(issues)

    def is_constraint(node_id: str) -> bool:
        # Optional semantic annotations cannot demote a governed contract.
        return nodes[node_id]["kind"] == "contract" or annotations[node_id][0] == "constraint"

    def eligible(node_id: str) -> bool:
        return not policy["regions"] or bool(
            set(policy["regions"]) & set(annotations[node_id][1])
        )

    for seed in policy["seeds"]:
        if seed not in nodes:
            raise ValueError(f"Unknown seed node ID: {seed}")
        if not eligible(seed):
            raise ValueError(f"Seed is outside requested regions: {seed}")

    edges = []
    edge_ids = set()
    edge_keys = set()
    adjacency = defaultdict(list)
    for edge in graph.get("edges", []):
        source, target, kind = edge.get("source"), edge.get("target"), edge.get("type")
        edge_id = edge.get("id")
        if (source not in nodes or target not in nodes or source == target
                or kind not in EDGE_TYPES or not isinstance(edge_id, str)
                or not edge_id or edge_id in edge_ids
                or (kind, source, target) in edge_keys):
            raise ValueError("Invalid, duplicate, or unresolved snapshot edge")
        edge_ids.add(edge_id)
        edge_keys.add((kind, source, target))
        clean = {"id": edge_id, "type": kind, "source": source, "target": target}
        edges.append(clean)
        if kind in policy["edge_types"]:
            if policy["direction"] in {"outgoing", "both"}:
                adjacency[source].append((target, clean))
            if policy["direction"] in {"incoming", "both"}:
                adjacency[target].append((source, clean))
    edges.sort(key=lambda edge: (edge["type"], edge["source"], edge["target"]))
    selected = {seed: {"depth": 0, "seed": seed, "parent": None, "via_edge": None}
                for seed in policy["seeds"]}
    frontier = list(policy["seeds"])
    for depth in range(1, policy["max_depth"] + 1):
        candidates = []
        for parent in frontier:
            for target, edge in adjacency[parent]:
                if target not in selected and eligible(target):
                    # Contracts first within a BFS layer; explicit seeds are never evicted.
                    candidates.append((not is_constraint(target),
                                       EDGE_PRIORITY[edge["type"]], target, parent,
                                       edge["id"]))
        next_frontier = []
        for _, _, target, parent, edge_id in sorted(candidates):
            if target in selected:
                continue
            if len(selected) >= policy["max_nodes"]:
                break
            selected[target] = {"depth": depth, "seed": selected[parent]["seed"],
                                "parent": parent, "via_edge": edge_id}
            next_frontier.append(target)
        frontier = next_frontier
        if not frontier:
            break

    projected = []
    warnings = []
    for node_id in sorted(selected, key=lambda item: (selected[item]["depth"], item)):
        node = nodes[node_id]
        role, regions = annotations[node_id]
        projected.append({key: node.get(key) for key in (
            "id", "workspace", "kind", "path", "source_hash", "lifecycle", "freshness")}
            | {"knowledge_role": role, "regions": regions, **selected[node_id]})
        if node.get("lifecycle") != "active" or node.get("freshness") == "stale":
            warnings.append({"code": "selected-noncurrent-node", "node_id": node_id})

    boundary = []
    gaps = []
    for edge in edges:
        source, target = edge["source"], edge["target"]
        if (source in selected) == (target in selected):
            continue
        inside = source if source in selected else target
        outside = target if source in selected else source
        forward = inside == source
        if not eligible(outside):
            reason = "region-boundary"
        elif edge["type"] not in policy["edge_types"]:
            reason = "edge-filter"
        elif (policy["direction"] == "outgoing" and not forward
              or policy["direction"] == "incoming" and forward):
            reason = "direction-filter"
        elif selected[inside]["depth"] >= policy["max_depth"]:
            reason = "depth-limit"
        else:
            reason = "node-limit"
        item = {**edge, "omitted_node": outside, "reason": reason}
        boundary.append(item)
        if forward and (edge["type"] == "depends_on"
                        or edge["type"] == "implements"
                        and is_constraint(target)):
            gaps.append({**item, "code": "missing-required-neighbor"})
        if edge["type"] == "contradicts":
            warnings.append({"code": "contradiction-outside-projection", "edge_id": edge["id"]})
        if edge["type"] == "supersedes" and not forward:
            warnings.append({"code": "replacement-outside-projection", "edge_id": edge["id"]})

    # Summarize upstream diagnostics without copying arbitrary source text.
    diagnostics = Counter(item.get("code", "unknown") for item in graph.get("diagnostics", []))
    cap = policy["max_boundary_edges"]
    result = {
        "artifact_type": ARTIFACT_TYPE, "policy_version": POLICY_VERSION,
        "workspace": workspace, "synapse_hash": graph.get("synapse_hash"),
        "as_of": graph.get("as_of"), "request": policy,
        "usage": "advisory-metadata-only", "execution_authorized": False,
        "nodes": projected,
        # Retain ALL relations between selected nodes, even filtered relations.
        "edges": [edge for edge in edges if edge["source"] in selected and edge["target"] in selected],
        "boundary_edges": boundary[:cap], "gaps": gaps[:cap], "warnings": warnings[:cap],
        "source_hashes": {node["path"]: node["source_hash"] for node in projected},
        "diagnostic_counts": dict(sorted(diagnostics.items())),
        "metadata_issue_counts": dict(sorted(metadata_issues.items())),
        "summary": {"selected_nodes": len(projected), "boundary_edges": len(boundary),
                    "required_neighbor_gaps": len(gaps), "warnings": len(warnings),
                    "boundary_edges_truncated": max(0, len(boundary) - cap),
                    "gaps_truncated": max(0, len(gaps) - cap),
                    "warnings_truncated": max(0, len(warnings) - cap),
                    "graph_diagnostics": sum(diagnostics.values()),
                    "metadata_issues": sum(metadata_issues.values())},
    }
    encoded = json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    result["projection_hash"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return result


def render_text(artifact: Mapping) -> str:
    lines = ["Advisory graph projection (not execution context)",
             f"Workspace: {artifact['workspace']}",
             f"Projection: {artifact['projection_hash']}", "", "Selected nodes:"]
    for node in artifact["nodes"]:
        lines.append(f"- {node['id']} [{node['knowledge_role']}] depth={node['depth']}")
    lines.extend(["", "Required-neighbor gaps:"])
    lines.extend(f"- {gap['source']} -> {gap['target']}: {gap['reason']}"
                 for gap in artifact["gaps"])
    if not artifact["gaps"]:
        lines.append("- none observed (not a completeness guarantee)")
    lines.extend(["", "Summary: " + json.dumps(artifact["summary"], sort_keys=True),
                  "Use normal context/policy checks before agent execution."])
    return "\n".join(lines) + "\n"
