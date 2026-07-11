#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd find — fuzzy search across workspace patterns/contracts/services/packs.

Port of .claude/commands/find.md logic to CLI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow importing from sibling modules and lib/
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_resolve  # noqa: E402
import context_security  # noqa: E402
import contextd_resolver  # noqa: E402
import find_engine  # noqa: E402


def run(query: str, workspace: str | None = None, limit: int = 5, fmt: str = "text") -> int:
    if not query.strip():
        if fmt == "json":
            print(json.dumps({"error": "Empty query"}, ensure_ascii=False))
        else:
            print("Error: Empty query", file=sys.stderr)
        return 1

    # Resolve workspace context
    resolved = cmd_resolve.resolve(require_workspace=True)
    try:
        wiki_root, ws, _ws_dir, packs, _pack_source = (
            contextd_resolver.select_workspace_state(resolved, workspace)
        )
    except ValueError as exc:
        message = f"Could not resolve workspace state: {exc}"
        if fmt == "json":
            print(json.dumps({"error": message}, ensure_ascii=False))
        else:
            print(f"Error: {message}", file=sys.stderr)
        return 1

    results = find_engine.find(query, wiki_root, workspace=ws, packs=packs, limit=limit)

    if fmt == "json":
        items = []
        for score, item in results:
            items.append({
                "score": score,
                "kind": item["kind"],
                "path": str(item["path"]),
                "relative_path": item.get("relative_path") or context_security.root_relative_posix(
                    Path(item["path"]), wiki_root
                ),
                "filename": item["filename"],
            })
        out = {
            "query": query,
            "workspace": ws or "all",
            "advisory": True,
            "limit": limit,
            "matches": items,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        text = find_engine.format_results(results, query, ws)
        print(text)
        if not results:
            print(f"No match. Try:")
            print(f"  - Broader keyword (e.g. 'kafka' instead of 'kafka-consumer-batch-retry')")
            print(f"  - Check workspace: workspace_active = {ws or 'none'}")
            print(f"  - Suggest: /list-workspaces, or /use-contextd \"{query}\" for full pipeline")

    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fuzzy search across contextd workspace knowledge.")
    parser.add_argument("query", help="Search keywords")
    parser.add_argument("--workspace", default=None, help="Override workspace (default: from resolved config)")
    parser.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")
    args = parser.parse_args()
    sys.exit(run(args.query, workspace=args.workspace, limit=args.limit, fmt=args.format))


if __name__ == "__main__":
    main()
