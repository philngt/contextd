"""Experimental read-only graph projection command; does not replace context."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.graph_projection import (  # noqa: E402
    DEFAULT_EDGE_TYPES, EDGE_TYPES, ProjectionRequest, project_graph, render_text,
)


def project_snapshot(snapshot, request: ProjectionRequest) -> dict:
    """Annotate only retained source records; never re-read canonical files."""
    from lib import synapse_engine
    from lib.frontmatter import split_frontmatter

    graph = snapshot.graph
    if graph.get("synapse_hash") != synapse_engine.compute_synapse_hash(graph):
        raise ValueError("Snapshot hash mismatch; rebuild with contextd synapse")
    if any(item.get("severity") == "error" for item in graph.get("diagnostics", [])):
        raise ValueError("Graph contains errors; inspect contextd synapse before projection")
    annotations = {}
    for node in graph.get("nodes", []):
        source = snapshot.sources_by_path.get(node["path"])
        if source is None or source.source_hash != node["source_hash"]:
            raise ValueError("Snapshot source record is missing or mismatched")
        metadata, _ = split_frontmatter(source.text)
        annotations[node["id"]] = metadata or {}
    return project_graph(graph, request, annotations)


def main(argv: list[str] | None = None) -> int:
    # Lazy imports keep the pure projection engine independently testable.
    import cmd_resolve
    from lib import synapse_engine
    from lib.stdio import configure_stdio

    configure_stdio()
    parser = argparse.ArgumentParser(
        description="Experimental, advisory graph metadata projection (read-only).")
    parser.add_argument("--seed", action="append", required=True, help="Local node ID; repeatable")
    parser.add_argument("--depth", type=int, default=2, help="BFS depth, 0..8 (default: 2)")
    parser.add_argument("--max-nodes", type=int, default=20, help="Node cap, 1..128 (default: 20)")
    parser.add_argument("--edge-type", action="append", choices=sorted(EDGE_TYPES),
                        help="Allowed traversal type; repeatable; default excludes related_to")
    parser.add_argument("--direction", choices=["outgoing", "incoming", "both"], default="outgoing")
    parser.add_argument("--region", action="append", default=[], help="Allowed region; repeatable")
    parser.add_argument("--max-boundary-edges", type=int, default=100)
    parser.add_argument("--cwd", help="Resolve canonical config from this project directory")
    parser.add_argument("--workspace", help="Explicit workspace within the resolved knowledge root")
    parser.add_argument("--as-of", help="Fixed evaluation date, YYYY-MM-DD")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--strict", action="store_true", help="Fail on gaps or warnings")
    args = parser.parse_args(argv)
    request = ProjectionRequest(
        seeds=tuple(args.seed), max_depth=args.depth, max_nodes=args.max_nodes,
        edge_types=tuple(args.edge_type) if args.edge_type is not None else DEFAULT_EDGE_TYPES,
        direction=args.direction, regions=tuple(args.region),
        max_boundary_edges=args.max_boundary_edges,
    )
    try:
        request.normalized()
        as_of = date.fromisoformat(args.as_of) if args.as_of else None
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    resolved = cmd_resolve.resolve(
        cwd=Path(args.cwd).resolve() if args.cwd else None, require_workspace=True)
    if resolved.get("error"):
        print(f"Error: {resolved['error']}", file=sys.stderr)
        return 1
    raw_root = resolved.get("knowledge_root") or resolved.get("wiki_root")
    workspace = args.workspace or resolved.get("workspace")
    if not raw_root or not workspace:
        print("Error: knowledge_root and workspace are required", file=sys.stderr)
        return 1
    root = Path(raw_root).resolve()
    workspace_dir = synapse_engine.resolve_workspace_dir(root, workspace)
    if workspace_dir is None or not workspace_dir.is_dir():
        print("Error: workspace is invalid or missing", file=sys.stderr)
        return 1
    try:
        snapshot = synapse_engine.build_synapse_snapshot(root, workspace, as_of=as_of)
        artifact = project_snapshot(snapshot, request)
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    rendered = (json.dumps(artifact, indent=2, ensure_ascii=False) + "\n"
                if args.format == "json" else render_text(artifact))
    print(rendered, end="")
    summary = artifact["summary"]
    has_issues = any(summary[key] for key in (
        "required_neighbor_gaps", "warnings", "graph_diagnostics", "metadata_issues"))
    return 1 if args.strict and has_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
