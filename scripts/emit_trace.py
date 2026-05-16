#!/usr/bin/env python3
"""
emit_trace.py — Claude Code PostToolUse hook handler.

Reads hook payload from stdin (JSON), extracts trace JSON from a wiki-* subagent's
output, and writes it to {cwd}/.claude/runs/{run_id}/{stage}.json.

Hook event: PostToolUse (matcher=Task).
Subagents handled: wiki-planner, wiki-context-selector, wiki-plan-reviewer, wiki-reviewer.

Behavior:
- No-op (exit 0) if tool_name != Task or subagent not in allow-list.
- No-op if no fenced ```json block found in tool_response.
- No-op if extracted JSON has no `run_id` + `stage` fields (malformed).
- NEVER fail the pipeline — exit 0 even on parse errors. Errors logged to stderr.

Schema: agents/pipeline/run-trace.schema.json (or templates/run-trace.schema.json).
Design doc: agents/pipeline/observability.md.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.atomic_write import (  # noqa: E402
    LockTimeout,
    atomic_write_json,
    with_advisory_lock,
)

ALLOWED_SUBAGENTS = {
    "wiki-planner",
    "wiki-context-selector",
    "wiki-plan-reviewer",
    "wiki-reviewer",
}

VALID_STAGES = {
    "01-planner",
    "02-context",
    "03-plan-review",
    "04-builder",
    "05-review",
}


def warn(msg: str) -> None:
    print(f"[emit_trace] {msg}", file=sys.stderr)


def extract_last_json_block(text: str) -> dict | None:
    """Find the last ```json ... ``` fenced block and parse it."""
    pattern = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
    matches = pattern.findall(text)
    if not matches:
        return None
    # Try parsing matches from last to first; first one that parses wins.
    for raw in reversed(matches):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            continue
    return None


def update_run_rollup(run_dir: Path, stage: str, trace: dict, cwd: Path) -> None:
    """Maintain {run_dir}/run.json with stages_completed + ts_end.

    Concurrency: 2+ subagents finishing close in time cause concurrent hook
    invocations on the same run.json. Use advisory lock + atomic write so the
    last-update-wins window is closed. If the lock cannot be acquired within
    budget, log and skip — trace must NEVER block the pipeline.
    """
    run_file = run_dir / "run.json"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        with with_advisory_lock(run_file, timeout_ms=600, backoff_ms=50):
            if run_file.exists():
                try:
                    rollup = json.loads(run_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    rollup = {}
            else:
                rollup = {}

            rollup.setdefault("stage", "run")
            rollup.setdefault("run_id", trace.get("run_id"))
            rollup.setdefault("ts_start", trace.get("ts", now))
            rollup.setdefault(
                "workspace_at_run", trace.get("workspace_at_run", "unknown")
            )
            rollup.setdefault("user_task", "")
            rollup.setdefault("ts", now)

            completed = set(rollup.get("stages_completed", []))
            completed.add(stage)
            rollup["stages_completed"] = sorted(completed)
            rollup["ts_end"] = now

            totals = rollup.setdefault("totals", {
                "unverified_patterns": 0,
                "knowledge_gaps": 0,
                "violations": 0,
                "hallucinations": 0,
            })
            if stage == "01-planner":
                totals["unverified_patterns"] = trace.get("unverified_count", 0)
            elif stage == "02-context":
                totals["knowledge_gaps"] = trace.get("gap_count", 0)
            elif stage == "05-review":
                totals["violations"] = trace.get("violation_count", 0)
                totals["hallucinations"] = trace.get("hallucination_count", 0)

            if "05-review" in completed and stage == "05-review":
                rollup["final_verdict"] = (
                    "VIOLATIONS" if trace.get("verdict") == "VIOLATIONS"
                    else "APPROVED"
                )
            elif "03-plan-review" in completed and stage == "03-plan-review":
                if trace.get("verdict") == "BLOCK":
                    rollup["final_verdict"] = "BLOCKED"
                else:
                    rollup.setdefault("final_verdict", "INCOMPLETE")
            else:
                rollup.setdefault("final_verdict", "INCOMPLETE")

            atomic_write_json(run_file, rollup)
    except LockTimeout:
        warn(f"trace lost (run.json lock contention): stage={stage}")
    except OSError as e:
        warn(f"failed to update run.json: {e}")


def stage_to_filename(stage: str) -> str:
    return f"{stage}.json"


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        warn(f"hook payload not JSON: {e}")
        return 0

    if payload.get("tool_name") != "Task":
        return 0

    tool_input = payload.get("tool_input") or {}
    subagent = tool_input.get("subagent_type")
    if subagent not in ALLOWED_SUBAGENTS:
        return 0

    tool_response = payload.get("tool_response")
    # tool_response can be a string or a list of content blocks
    if isinstance(tool_response, list):
        tool_response = "\n".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in tool_response
        )
    elif not isinstance(tool_response, str):
        tool_response = str(tool_response or "")

    trace = extract_last_json_block(tool_response)
    if not trace:
        warn(f"no ```json block found in {subagent} output")
        return 0

    run_id = trace.get("run_id")
    stage = trace.get("stage")
    if not run_id or stage not in VALID_STAGES:
        warn(f"trace missing run_id or invalid stage: {stage}")
        return 0

    cwd = Path(payload.get("cwd") or os.getcwd())
    run_dir = cwd / ".claude" / "runs" / run_id
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        warn(f"cannot create run_dir {run_dir}: {e}")
        return 0

    # Add ts if missing
    trace.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))

    out_file = run_dir / stage_to_filename(stage)
    try:
        atomic_write_json(out_file, trace)
    except OSError as e:
        warn(f"failed to write {out_file}: {e}")
        return 0

    update_run_rollup(run_dir, stage, trace, cwd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
