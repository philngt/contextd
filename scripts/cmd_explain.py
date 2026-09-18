#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd explain — debug deterministic task-context selection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib import contextd_resolver  # noqa: E402
from lib import task_context_engine, decision_context  # noqa: E402
from lib.stdio import configure_stdio  # noqa: E402


def _render_text(payload: dict) -> str:
    summary = payload["summary"]
    trace = payload.get("selection_trace") or {}
    budget = summary.get("budget_report") or {}
    lines = [
        "# contextd Explain",
        "",
        f"Workspace: {summary['workspace']}",
        f"Intent: {summary['intent'].get('type')} / {summary['intent'].get('workstream')}",
    ]
    classification = summary["intent"].get("classification") or {}
    for axis in ("intent", "workstream"):
        info = classification.get(axis) or {}
        if info.get("scores"):
            scores_str = ", ".join(f"{k}={v}" for k, v in info["scores"].items())
            tie_note = " (tie-broken by precedence)" if info.get("tie_broken") else ""
            lines.append(f"  {axis} scores: {scores_str}{tie_note}")
    lines += [
        f"Context Pack: {summary['context_pack_key']}",
        f"Synapse: {summary.get('synapse_hash', '(not available)')}",
        (
            "Budget: "
            f"{budget.get('selected_docs', 0)}/{budget.get('max_docs', 0)} docs, "
            f"~{budget.get('estimated_tokens_referenced', budget.get('estimated_tokens_selected', 0))} referenced + "
            f"~{budget.get('estimated_tokens_static', 0)} static = "
            f"~{budget.get('estimated_tokens_total', budget.get('estimated_tokens_selected', 0))} total tokens"
        ),
        "",
        "## Selected Docs",
    ]
    selected = trace.get("selected_docs") or []
    if not selected:
        lines.append("- (none)")
    for doc in selected:
        redacted = " redacted=true" if doc.get("redacted") else ""
        state = doc.get("synapse") or {}
        state_note = ""
        if state:
            state_note = (
                f" lifecycle={state.get('lifecycle')} freshness={state.get('freshness')}"
                f" state_adjustment={doc.get('state_score_adjustment', 0)}"
            )
        lines.append(
            f"- {doc['path']} [{doc['category']}] "
            f"score={doc['selection_score']} reason={doc['selection_reason']}"
            f"{state_note}{redacted}"
        )

    dropped = trace.get("dropped_docs") or []
    lines.extend(["", "## Dropped Docs"])
    if not dropped:
        lines.append("- (none)")
    for doc in dropped[:30]:
        state = doc.get("synapse") or {}
        state_note = ""
        if state:
            state_note = (
                f" lifecycle={state.get('lifecycle')} freshness={state.get('freshness')}"
                f" state_adjustment={doc.get('state_score_adjustment', 0)}"
            )
        lines.append(
            f"- {doc['path']} [{doc['category']}] "
            f"score={doc['selection_score']} reason={doc['selection_reason']}"
            f"{state_note}"
        )
    if len(dropped) > 30:
        lines.append(f"- ... {len(dropped) - 30} more")

    artifact = payload["artifact"]
    lines.extend(decision_context.render_report(artifact.get("decision_context")))
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
    support_request: dict | None = None,
) -> int:
    if not task.strip():
        print("Error: Empty task", file=sys.stderr)
        return 1

    try:
        state = contextd_resolver.resolve_request(cwd=Path(cwd) if cwd else None, workspace=workspace)
    except contextd_resolver.ResolutionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        for warning in exc.payload.get("warnings", []):
            print(f"  - {warning}", file=sys.stderr)
        return 1
    wiki_root, ws, packs, project_dir = (state.knowledge_root, state.workspace,
                                        state.packs, state.project_dir)
    resolved = state.resolved
    try:
        payload = task_context_engine.build_context_explanation(
            task=task,
            wiki_root=wiki_root,
            workspace=ws,
            packs=packs,
            project_dir=project_dir,
            warnings=resolved.get("warnings") or [],
            support_request=support_request,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if fmt == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(_render_text(payload), end="")
    return 0


def main() -> None:
    configure_stdio()
    import argparse
    parser = argparse.ArgumentParser(description="Explain deterministic context selection.")
    parser.add_argument("task", help="Task description (quote if multi-word)")
    parser.add_argument("--workspace", default=None, help="Override workspace name")
    parser.add_argument("--cwd", default=None, help="Start directory (default: current)")
    parser.add_argument("--format", choices=["text", "json"], default="json")
    decision_context.add_arguments(parser)
    args = parser.parse_args()
    sys.exit(run(args.task, workspace=args.workspace, cwd=args.cwd, fmt=args.format,
                 support_request=decision_context.request_from_args(args)))


if __name__ == "__main__":
    main()
