#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd policy-check — evaluate policy-as-code for a task context."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_resolve  # noqa: E402
import task_context_engine  # noqa: E402


def _render_text(report: dict) -> str:
    lines = [
        "# contextd Policy Check",
        "",
        f"Status: {report['status']}",
        (
            "Summary: "
            f"{report['summary']['errors']} error(s), "
            f"{report['summary']['warnings']} warning(s), "
            f"{report['summary']['rules_evaluated']} rule(s) evaluated"
        ),
        "",
    ]
    if report.get("policy_sources"):
        lines.append("## Policy Sources")
        for source in report["policy_sources"]:
            lines.append(f"- {source['path']} ({source['rule_count']} rule(s))")
        lines.append("")
    if report.get("violations"):
        lines.append("## Violations")
        for violation in report["violations"]:
            lines.append(
                f"- [{violation['severity']}] {violation['rule_id']} "
                f"{violation['check']}: {violation['detail']}"
            )
        lines.append("")
    if report.get("load_errors"):
        lines.append("## Load Errors")
        for error in report["load_errors"]:
            lines.append(f"- [{error['severity']}] {error['source']}: {error['message']}")
        lines.append("")
    return "\n".join(lines)


def _resolve_task(task: str, workspace: str | None, cwd: str | None) -> tuple[dict, Path, str, list[str]]:
    start = Path(cwd).resolve() if cwd else None
    resolved = cmd_resolve.resolve(cwd=start, require_workspace=True)
    if resolved.get("error"):
        raise RuntimeError(str(resolved["error"]))
    root_raw = resolved.get("knowledge_root") or resolved.get("wiki_root")
    if not root_raw:
        raise RuntimeError("Could not resolve knowledge_root.")
    wiki_root = Path(str(root_raw)).resolve()
    ws = workspace or resolved.get("workspace")
    if not ws:
        raise RuntimeError("No workspace resolved.")
    if workspace:
        packs, _ = cmd_resolve.get_effective_packs({}, wiki_root / "workspaces" / ws / "workspace.md")
    else:
        packs = resolved.get("packs") or []
    artifact = task_context_engine.build_context_artifact(
        task=task,
        wiki_root=wiki_root,
        workspace=ws,
        packs=packs,
        project_dir=Path(resolved.get("project_dir") or ".").resolve(),
        warnings=resolved.get("warnings") or [],
    )
    return artifact, wiki_root, ws, packs


def run(task: str, workspace: str | None = None, cwd: str | None = None,
        fmt: str = "json") -> int:
    if not task.strip():
        print("Error: Empty task", file=sys.stderr)
        return 1
    try:
        artifact, _, _, _ = _resolve_task(task, workspace, cwd)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    report = artifact.get("governance_report") or {}
    payload = {
        "artifact_type": "contextd_policy_check.v1",
        "task": task,
        "workspace": artifact.get("workspace"),
        "governance_report": report,
    }
    if fmt == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(_render_text(report))

    if report.get("summary", {}).get("errors"):
        return 1
    if report.get("summary", {}).get("warnings"):
        return 2
    return 0


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate contextd policy-as-code for a task.")
    parser.add_argument("task", help="Task description (quote if multi-word)")
    parser.add_argument("--workspace", default=None, help="Override workspace name")
    parser.add_argument("--cwd", default=None, help="Start directory (default: current)")
    parser.add_argument("--format", choices=["text", "json"], default="json")
    args = parser.parse_args()
    sys.exit(run(args.task, workspace=args.workspace, cwd=args.cwd, fmt=args.format))


if __name__ == "__main__":
    main()
