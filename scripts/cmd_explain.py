#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd explain — debug deterministic task-context selection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_resolve  # noqa: E402
import task_context_engine  # noqa: E402


def _render_text(payload: dict) -> str:
    summary = payload["summary"]
    trace = payload.get("selection_trace") or {}
    budget = summary.get("budget_report") or {}
    lines = [
        "# contextd Explain",
        "",
        f"Workspace: {summary['workspace']}",
        f"Intent: {summary['intent'].get('type')} / {summary['intent'].get('workstream')}",
        f"Context Pack: {summary['context_pack_key']}",
        (
            "Budget: "
            f"{budget.get('selected_docs', 0)}/{budget.get('max_docs', 0)} docs, "
            f"~{budget.get('estimated_tokens_selected', 0)} tokens"
        ),
        "",
        "## Selected Docs",
    ]
    selected = trace.get("selected_docs") or []
    if not selected:
        lines.append("- (none)")
    for doc in selected:
        redacted = " redacted=true" if doc.get("redacted") else ""
        lines.append(
            f"- {doc['path']} [{doc['category']}] "
            f"score={doc['selection_score']} reason={doc['selection_reason']}{redacted}"
        )

    dropped = trace.get("dropped_docs") or []
    lines.extend(["", "## Dropped Docs"])
    if not dropped:
        lines.append("- (none)")
    for doc in dropped[:30]:
        lines.append(
            f"- {doc['path']} [{doc['category']}] "
            f"score={doc['selection_score']} reason={doc['selection_reason']}"
        )
    if len(dropped) > 30:
        lines.append(f"- ... {len(dropped) - 30} more")

    artifact = payload["artifact"]
    lines.extend(["", "## Gaps"])
    if not artifact.get("gaps"):
        lines.append("- (none)")
    for gap in artifact.get("gaps") or []:
        lines.append(
            f"- [{gap.get('category')}] {gap.get('missing')} "
            f"(blocking_hint={gap.get('blocking_hint')})"
        )

    lines.extend(["", "## Warnings"])
    if not artifact.get("warnings"):
        lines.append("- (none)")
    for warning in artifact.get("warnings") or []:
        lines.append(f"- {warning}")

    return "\n".join(lines) + "\n"


def run(
    task: str,
    workspace: str | None = None,
    cwd: str | None = None,
    fmt: str = "json",
) -> int:
    if not task.strip():
        print("Error: Empty task", file=sys.stderr)
        return 1

    start = Path(cwd).resolve() if cwd else None
    resolved = cmd_resolve.resolve(cwd=start, require_workspace=True)
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

    if workspace:
        ws_md = wiki_root / "workspaces" / workspace / "workspace.md"
        packs, _ = cmd_resolve.get_effective_packs({}, ws_md)
    else:
        packs = resolved.get("packs") or []

    project_dir = Path(resolved.get("project_dir") or ".").resolve()
    payload = task_context_engine.build_context_explanation(
        task=task,
        wiki_root=wiki_root,
        workspace=ws,
        packs=packs,
        project_dir=project_dir,
        warnings=resolved.get("warnings") or [],
    )

    if fmt == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(_render_text(payload), end="")
    return 0


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Explain deterministic context selection.")
    parser.add_argument("task", help="Task description (quote if multi-word)")
    parser.add_argument("--workspace", default=None, help="Override workspace name")
    parser.add_argument("--cwd", default=None, help="Start directory (default: current)")
    parser.add_argument("--format", choices=["text", "json"], default="json")
    args = parser.parse_args()
    sys.exit(run(args.task, workspace=args.workspace, cwd=args.cwd, fmt=args.format))


if __name__ == "__main__":
    main()
