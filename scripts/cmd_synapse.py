#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd synapse — build the active workspace lifecycle graph."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import cmd_resolve  # noqa: E402
from lib import synapse_engine  # noqa: E402
from lib.stdio import configure_stdio  # noqa: E402


def run(
    workspace: str | None = None,
    cwd: str | None = None,
    fmt: str = "json",
    materialize: bool = True,
    output_dir: str | None = None,
    output: str | None = None,
    as_of: str | None = None,
) -> int:
    resolved = cmd_resolve.resolve(
        cwd=Path(cwd).resolve() if cwd else None,
        require_workspace=True,
    )
    if resolved.get("error"):
        print(f"Error: {resolved['error']}", file=sys.stderr)
        for warning in resolved.get("warnings") or []:
            print(f"  - {warning}", file=sys.stderr)
        return 1

    wiki_root_raw = resolved.get("knowledge_root") or resolved.get("wiki_root")
    if not wiki_root_raw:
        print("Error: Could not resolve knowledge_root.", file=sys.stderr)
        return 1
    selected_workspace = workspace or resolved.get("workspace")
    if not selected_workspace:
        print("Error: No workspace resolved. Specify --workspace.", file=sys.stderr)
        return 1
    if not synapse_engine.is_valid_workspace_name(selected_workspace):
        print(f"Error: Invalid workspace name: {selected_workspace!r}", file=sys.stderr)
        return 1

    evaluation_date = None
    if as_of:
        try:
            evaluation_date = date.fromisoformat(as_of)
        except ValueError:
            print("Error: --as-of must be an ISO date (YYYY-MM-DD).", file=sys.stderr)
            return 2

    wiki_root = Path(wiki_root_raw).resolve()
    workspace_dir = synapse_engine.resolve_workspace_dir(wiki_root, selected_workspace)
    if workspace_dir is None or not workspace_dir.is_dir():
        print(f"Error: Workspace not found: {workspace_dir}", file=sys.stderr)
        return 1

    artifact = synapse_engine.build_synapse_index(
        wiki_root,
        selected_workspace,
        as_of=evaluation_date,
    )
    if materialize:
        project_dir = Path(
            output_dir or resolved.get("project_dir") or "."
        ).resolve()
        synapse_engine.materialize_synapse(artifact, project_dir)

    rendered = (
        json.dumps(artifact, indent=2, ensure_ascii=False) + "\n"
        if fmt == "json"
        else synapse_engine.render_text(artifact)
    )
    if output:
        output_path = Path(output)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if artifact.get("summary", {}).get("errors", 0) else 0


def main() -> None:
    import argparse

    configure_stdio()
    parser = argparse.ArgumentParser(description="Build workspace lifecycle graph.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--cwd", default=None)
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--no-materialize", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(
        workspace=args.workspace,
        cwd=args.cwd,
        fmt=args.format,
        materialize=not args.no_materialize,
        output_dir=args.output_dir,
        output=args.output,
        as_of=args.as_of,
    ))


if __name__ == "__main__":
    main()
