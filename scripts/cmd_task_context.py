#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd context/task-context — deterministic context artifact builder."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib import contextd_resolver  # noqa: E402
from lib import task_context_engine, decision_context  # noqa: E402
from lib.stdio import configure_stdio  # noqa: E402


def run(
    task: str,
    workspace: str | None = None,
    output: str | None = None,
    fmt: str = "markdown",
    materialize: bool = False,
    output_dir: str | None = None,
    support_request: dict | None = None,
) -> int:
    if not task.strip():
        print("Error: Empty task", file=sys.stderr)
        return 1

    try:
        state = contextd_resolver.resolve_request(cwd=None, workspace=workspace)
    except contextd_resolver.ResolutionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        for warning in exc.payload.get("warnings", []):
            print(f"  - {warning}", file=sys.stderr)
        return 1
    wiki_root, ws, packs, project_dir = (state.knowledge_root, state.workspace,
                                        state.packs, state.project_dir)
    resolved = state.resolved
    try:
        build_result = task_context_engine.build_context_result(
            task=task,
            wiki_root=wiki_root,
            workspace=ws,
            packs=packs,
            project_dir=project_dir,
            warnings=resolved.get("warnings") or [],
            support_request=support_request,
        )
        artifact, synapse_snapshot = build_result.artifact, build_result.synapse
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if materialize:
        target_dir = Path(output_dir).resolve() if output_dir else project_dir
        try:
            artifact = task_context_engine.materialize_context(
                artifact, target_dir, synapse_snapshot=synapse_snapshot,
            )
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

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
    configure_stdio()
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
    decision_context.add_arguments(parser)
    args = parser.parse_args()
    sys.exit(run(
        args.task,
        workspace=args.workspace,
        output=args.output,
        fmt=args.format,
        materialize=args.materialize,
        output_dir=args.output_dir,
        support_request=decision_context.request_from_args(args),
    ))


if __name__ == "__main__":
    main()
