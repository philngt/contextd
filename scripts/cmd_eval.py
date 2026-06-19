#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd eval — deterministic context selection evaluation."""

from __future__ import annotations

import fnmatch
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_resolve  # noqa: E402
import task_context_engine  # noqa: E402


def _load_fixture(path: Path) -> Dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _match_any(paths: List[str], pattern: str) -> bool:
    return any(path == pattern or fnmatch.fnmatch(path, pattern) for path in paths)


def _gaps_match(gaps: List[Dict], expected: str) -> bool:
    return any(expected in str(gap.get("missing") or "") for gap in gaps)


def _score_fixture(fixture: Dict, artifact: Dict) -> Dict:
    paths = [str(doc.get("path") or "") for doc in artifact.get("referenced_docs") or []]
    categories = {str(doc.get("category") or "") for doc in artifact.get("referenced_docs") or []}
    errors: List[str] = []

    for pattern in fixture.get("expected_docs") or []:
        if not _match_any(paths, str(pattern)):
            errors.append(f"expected doc not selected: {pattern}")
    for category in fixture.get("expected_categories") or []:
        if str(category) not in categories:
            errors.append(f"expected category not selected: {category}")
    for pattern in fixture.get("forbidden_docs") or []:
        if _match_any(paths, str(pattern)):
            errors.append(f"forbidden doc selected: {pattern}")
    for expected in fixture.get("expected_gaps") or []:
        if not _gaps_match(artifact.get("gaps") or [], str(expected)):
            errors.append(f"expected gap not found: {expected}")

    expected_policy = fixture.get("policy_expectation")
    if expected_policy:
        actual_policy = (artifact.get("governance_report") or {}).get("status")
        if actual_policy != expected_policy:
            errors.append(f"policy status {actual_policy} != expected {expected_policy}")

    return {
        "id": fixture.get("id") or "<unknown>",
        "task": fixture.get("task") or "",
        "status": "fail" if errors else "pass",
        "errors": errors,
        "selected_docs": paths,
        "selected_categories": sorted(categories),
        "governance_status": (artifact.get("governance_report") or {}).get("status"),
        "budget_report": artifact.get("budget_report") or {},
    }


def _fixture_paths(wiki_root: Path, workspace: str) -> List[Path]:
    base = wiki_root / "workspaces" / workspace / "eval" / "golden-tasks"
    if not base.is_dir():
        return []
    return sorted(p for p in base.glob("*.json") if p.is_file())


def _render_text(report: Dict) -> str:
    lines = [
        "# contextd Eval",
        "",
        f"Status: {report['status']}",
        (
            "Summary: "
            f"{report['summary']['passed']}/{report['summary']['tasks']} passed, "
            f"{report['summary']['failed']} failed"
        ),
        "",
    ]
    for result in report.get("results") or []:
        lines.append(f"## {result['id']} — {result['status']}")
        if result.get("errors"):
            for error in result["errors"]:
                lines.append(f"- {error}")
        else:
            lines.append("- ok")
        lines.append("")
    return "\n".join(lines)


def run(golden: bool = False, workspace: str | None = None, fmt: str = "json",
        output: str | None = None, cwd: str | None = None) -> int:
    if not golden:
        print("Error: only --golden evaluation is supported.", file=sys.stderr)
        return 1
    start = Path(cwd).resolve() if cwd else None
    resolved = cmd_resolve.resolve(cwd=start, require_workspace=True)
    if resolved.get("error"):
        print(f"Error: {resolved['error']}", file=sys.stderr)
        return 1
    root_raw = resolved.get("knowledge_root") or resolved.get("wiki_root")
    if not root_raw:
        print("Error: Could not resolve knowledge_root.", file=sys.stderr)
        return 1
    wiki_root = Path(str(root_raw)).resolve()
    ws = workspace or resolved.get("workspace")
    if not ws:
        print("Error: No workspace resolved.", file=sys.stderr)
        return 1
    default_packs = resolved.get("packs") or []
    results: List[Dict] = []
    load_errors: List[Dict] = []
    for path in _fixture_paths(wiki_root, ws):
        fixture = _load_fixture(path)
        if fixture is None:
            load_errors.append({"path": path.relative_to(wiki_root).as_posix(), "error": "invalid-json"})
            continue
        task = str(fixture.get("task") or "")
        packs = [str(pack) for pack in fixture.get("packs") or default_packs]
        artifact = task_context_engine.build_context_artifact(
            task=task,
            wiki_root=wiki_root,
            workspace=str(fixture.get("workspace") or ws),
            packs=packs,
            project_dir=Path(resolved.get("project_dir") or ".").resolve(),
            warnings=resolved.get("warnings") or [],
        )
        scored = _score_fixture(fixture, artifact)
        scored["fixture_path"] = path.relative_to(wiki_root).as_posix()
        results.append(scored)

    failed = sum(1 for result in results if result["status"] == "fail")
    passed = sum(1 for result in results if result["status"] == "pass")
    status = "error" if failed or load_errors else "ok"
    report = {
        "artifact_type": "contextd_evaluation_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workspace": ws,
        "mode": "golden",
        "status": status,
        "summary": {
            "tasks": len(results),
            "passed": passed,
            "failed": failed,
            "load_errors": len(load_errors),
        },
        "results": results,
        "load_errors": load_errors,
    }

    rendered = (
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if fmt == "json"
        else _render_text(report)
    )
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Eval report written to: {out_path}")
    else:
        print(rendered, end="" if rendered.endswith("\n") else "\n")
    return 1 if status == "error" else 0


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate contextd context selection.")
    parser.add_argument("--golden", action="store_true", help="Run golden task fixtures")
    parser.add_argument("--workspace", default=None, help="Workspace name (default: resolved)")
    parser.add_argument("--cwd", default=None, help="Start directory (default: current)")
    parser.add_argument("--format", choices=["text", "json"], default="json")
    parser.add_argument("--output", default=None, help="Output file path")
    args = parser.parse_args()
    sys.exit(run(
        golden=args.golden,
        workspace=args.workspace,
        cwd=args.cwd,
        fmt=args.format,
        output=args.output,
    ))


if __name__ == "__main__":
    main()
