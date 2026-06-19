#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd context/task-context — deterministic context artifact builder."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_resolve  # noqa: E402
import task_context_engine  # noqa: E402


def run(
    task: str,
    workspace: str | None = None,
    output: str | None = None,
    fmt: str = "markdown",
    materialize: bool = False,
    output_dir: str | None = None,
) -> int:
    if not task.strip():
        print("Error: Empty task", file=sys.stderr)
        return 1

    resolved = cmd_resolve.resolve(require_workspace=True)
    if resolved.get("error"):
        print(f"Error: {resolved['error']}", file=sys.stderr)
        for warning in resolved.get("warnings") or []:
            print(f"  - {warning}", file=sys.stderr)
        return 1

    wiki_root_str = resolved.get("knowledge_root") or resolved.get("wiki_root")
    if not wiki_root_str:
        print("Error: Could not resolve knowledge_root.", file=sys.stderr)
        return 1

    wiki_root = Path(wiki_root_str).resolve()
    ws = workspace or resolved.get("workspace")

    if not ws:
        print("Error: No workspace resolved. Specify --workspace.", file=sys.stderr)
        return 1

    # If workspace is overridden, resolve packs from that workspace's workspace.md
    if workspace:
        ws_md = wiki_root / "workspaces" / workspace / "workspace.md"
        packs, _ = cmd_resolve.get_effective_packs({}, ws_md)
    else:
        packs = resolved.get("packs") or []

    project_dir = Path(resolved.get("project_dir") or ".").resolve()
    artifact = task_context_engine.build_context_artifact(
        task=task,
        wiki_root=wiki_root,
        workspace=ws,
        packs=packs,
        project_dir=project_dir,
        warnings=resolved.get("warnings") or [],
    )

    if materialize:
        target_dir = Path(output_dir).resolve() if output_dir else project_dir
        artifact = task_context_engine.materialize_context(artifact, target_dir)

    if fmt == "json":
        import json
        rendered = json.dumps(artifact, indent=2, ensure_ascii=False) + "\n"
    else:
        rendered = task_context_engine.render_markdown(artifact)

    if output:
        out_path = Path(output)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Task context written to: {out_path}")
    else:
        print(rendered, end="" if rendered.endswith("\n") else "\n")

    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build deterministic task context.")
    parser.add_argument("task", help="Task description (quote if multi-word)")
    parser.add_argument("--workspace", default=None, help="Override workspace name")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                        help="Output format (default: markdown)")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: stdout)")
    parser.add_argument("--materialize", action="store_true",
                        help="Write .contextd/context/current-task.{json,md} and context pack")
    parser.add_argument("--output-dir", default=None,
                        help="Project directory for materialized .contextd/context (default: resolved project)")
    args = parser.parse_args()
    sys.exit(run(
        args.task,
        workspace=args.workspace,
        output=args.output,
        fmt=args.format,
        materialize=args.materialize,
        output_dir=args.output_dir,
    ))


if __name__ == "__main__":
    main()
