#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd doctor — production-readiness diagnostics for a project."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_resolve  # noqa: E402
import pack_validation  # noqa: E402
import render_runtime  # noqa: E402
import task_context_engine  # noqa: E402
from context_security import block_reason, reject_unsafe_entry  # noqa: E402


Issue = Dict[str, str]


def _issue(severity: str, check: str, message: str, path: str | None = None) -> Issue:
    out: Issue = {"severity": severity, "check": check, "message": message}
    if path:
        out["path"] = path
    return out


def _is_compat_info(warning: str) -> bool:
    return warning.startswith("Ignoring lower-priority config:")


def _validate_schema_files(issues: List[Issue]) -> None:
    required = [
        "templates/contextd-config.schema.json",
        "templates/task-context.schema.json",
        "templates/context-policy.schema.json",
        "templates/pack.schema.json",
        "templates/retrieval-map.schema.json",
        "templates/run-trace.schema.json",
        ".contextd/manifest.schema.json",
        ".contextd/manifest.json",
        "contextd.spec",
    ]
    for rel in required:
        path = REPO_ROOT / rel
        if not path.is_file():
            issues.append(_issue("error", "schema-release-inputs", f"Missing required file: {rel}", rel))


def _validate_pack_retrieval_maps(root: Path, workspace: str, packs: List[str],
                                  issues: List[Issue]) -> None:
    _ = workspace  # Kept for future workspace-specific policy checks.
    for pack_name in packs:
        pack_dir = root / "packs" / pack_name
        if not (pack_dir / "pack.yaml").is_file():
            issues.append(_issue("warning", "active-packs", f"Active pack not found: {pack_name}",
                                 f"packs/{pack_name}"))
            continue
        map_path = pack_dir / "agents" / "pipeline" / "retrieval-map.md"
        if not map_path.is_file():
            continue
        rows = task_context_engine._parse_retrieval_map(map_path)  # noqa: SLF001
        for component, entries in rows.items():
            for entry in entries:
                unsafe = reject_unsafe_entry(entry)
                if unsafe:
                    issues.append(_issue(
                        "error",
                        "retrieval-map-safety",
                        f"`{component}` has unsafe retrieval path `{entry}`: {unsafe}",
                        str(map_path.relative_to(root)),
                    ))
                    continue
                if entry.startswith("packs/") and not entry.startswith(f"packs/{pack_name}/"):
                    issues.append(_issue(
                        "error",
                        "retrieval-map-safety",
                        (
                            f"`{component}` references another pack via `{entry}`; "
                            "pack retrieval may only read its own pack directory"
                        ),
                        str(map_path.relative_to(root)),
                    ))


def _scan_blocked_paths(root: Path, workspace: str, packs: List[str],
                        issues: List[Issue]) -> None:
    roots = [root / "workspaces" / workspace]
    roots.extend(root / "packs" / pack for pack in packs)
    for base in roots:
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            reason = block_reason(path)
            if not reason:
                continue
            try:
                rel = path.relative_to(root).as_posix()
            except ValueError:
                rel = path.as_posix()
            issues.append(_issue(
                "warning",
                "secret-risk",
                f"Secret-like path will be blocked by runtime reads: {reason}",
                rel,
            ))


def _append_pack_validation(root: Path, packs: List[str], issues: List[Issue],
                            infos: List[Issue]) -> None:
    report = pack_validation.validate_packs(root, pack_names=packs)
    summary = report.get("summary") or {}
    infos.append(_issue(
        "info",
        "pack-validation",
        (
            f"Checked {summary.get('packs_checked', 0)} pack(s): "
            f"{summary.get('errors', 0)} error(s), {summary.get('warnings', 0)} warning(s)."
        ),
    ))
    for issue in report.get("issues") or []:
        severity = issue.get("severity") or "error"
        if severity == "info":
            infos.append(_issue("info", issue.get("check", "pack-validation"),
                                issue.get("message", ""), issue.get("path")))
        else:
            issues.append(_issue(severity, issue.get("check", "pack-validation"),
                                 issue.get("message", ""), issue.get("path")))


def _validate_generated_adapters(root: Path, workspace: str, packs: List[str],
                                 issues: List[Issue]) -> None:
    manifest = render_runtime._load_manifest()  # noqa: SLF001
    if manifest is None:
        issues.append(_issue("warning", "adapter-drift", "Could not load contextd manifest."))
        return
    artifacts = render_runtime.render_codex_plugin(
        manifest,
        workspace,
        root,
        packs,
        include_engine=False,
    )

    skill = artifacts.get("skills/contextd/SKILL.md", "")
    context_idx = skill.find("`.contextd/config.json`")
    legacy_idx = skill.find("`.claude/wiki.json`")
    if context_idx < 0:
        issues.append(_issue(
            "error",
            "adapter-drift",
            "Generated Codex skill does not mention canonical `.contextd/config.json`.",
            "scripts/render_runtime.py",
        ))
    if "Look for `.claude/wiki.json`" in skill:
        issues.append(_issue(
            "warning",
            "adapter-drift",
            "Generated Codex skill still describes legacy `.claude/wiki.json` as primary.",
            "scripts/render_runtime.py",
        ))
    if legacy_idx >= 0 and context_idx >= 0 and legacy_idx < context_idx:
        issues.append(_issue(
            "warning",
            "adapter-drift",
            "Generated Codex skill mentions legacy config before canonical config.",
            "scripts/render_runtime.py",
        ))


def diagnose(cwd: str | None = None) -> Dict:
    start = Path(cwd).resolve() if cwd else None
    resolved = cmd_resolve.resolve(cwd=start, require_workspace=True)
    issues: List[Issue] = []
    infos: List[Issue] = []

    for warning in resolved.get("warnings") or []:
        if _is_compat_info(warning):
            infos.append(_issue("info", "config-resolution", warning))
        else:
            issues.append(_issue("warning", "config-resolution", warning))

    if resolved.get("error"):
        issues.append(_issue("error", "config-resolution", f"Resolver error: {resolved['error']}"))

    root_raw = resolved.get("knowledge_root") or resolved.get("wiki_root")
    workspace = resolved.get("workspace")
    if not root_raw:
        issues.append(_issue("error", "config-resolution", "Could not resolve knowledge_root."))
    if not workspace:
        issues.append(_issue("error", "config-resolution", "Could not resolve workspace."))

    if root_raw and workspace:
        root = Path(root_raw).resolve()
        ws_dir = root / "workspaces" / workspace
        if not ws_dir.is_dir():
            issues.append(_issue("error", "workspace-isolation", f"Workspace directory missing: {ws_dir}"))
        elif not (ws_dir / "workspace.md").is_file():
            issues.append(_issue("error", "workspace-isolation", "workspace.md missing.",
                                 str((ws_dir / "workspace.md").relative_to(root))))
        packs = resolved.get("packs") or []
        _validate_pack_retrieval_maps(root, workspace, packs, issues)
        _append_pack_validation(root, packs, issues, infos)
        _scan_blocked_paths(root, workspace, packs, issues)
        _validate_generated_adapters(root, workspace, packs, issues)

    _validate_schema_files(issues)

    error_count = sum(1 for issue in issues if issue["severity"] == "error")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
    status = "error" if error_count else "warning" if warning_count else "ok"
    return {
        "artifact_type": "contextd_doctor_report.v1",
        "status": status,
        "summary": {
            "errors": error_count,
            "warnings": warning_count,
            "info": len(infos),
        },
        "resolved": resolved,
        "issues": issues,
        "info": infos,
    }


def _render_text(report: Dict) -> str:
    lines = [
        "# contextd Doctor",
        "",
        f"Status: {report['status']}",
        (
            "Summary: "
            f"{report['summary']['errors']} error(s), "
            f"{report['summary']['warnings']} warning(s), "
            f"{report['summary']['info']} info"
        ),
        "",
    ]
    if report["issues"]:
        lines.append("## Issues")
        for issue in report["issues"]:
            path = f" ({issue['path']})" if issue.get("path") else ""
            lines.append(f"- [{issue['severity']}] {issue['check']}: {issue['message']}{path}")
        lines.append("")
    if report["info"]:
        lines.append("## Info")
        for issue in report["info"]:
            lines.append(f"- {issue['message']}")
        lines.append("")
    return "\n".join(lines)


def run(cwd: str | None = None, fmt: str = "json") -> int:
    report = diagnose(cwd=cwd)
    if fmt == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(_render_text(report))

    if report["summary"]["errors"]:
        return 1
    if report["summary"]["warnings"]:
        return 2
    return 0


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Diagnose contextd production-readiness issues.")
    parser.add_argument("--cwd", default=None, help="Start directory (default: current)")
    parser.add_argument("--format", choices=["text", "json"], default="json")
    args = parser.parse_args()
    sys.exit(run(cwd=args.cwd, fmt=args.format))


if __name__ == "__main__":
    main()
