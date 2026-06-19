#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd pack-validate — validate pack API and retrieval maps."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_resolve  # noqa: E402
import pack_validation  # noqa: E402


def _render_text(report: dict) -> str:
    lines = [
        "# contextd Pack Validation",
        "",
        f"Status: {report['status']}",
        (
            "Summary: "
            f"{report['summary']['packs_checked']} pack(s), "
            f"{report['summary']['errors']} error(s), "
            f"{report['summary']['warnings']} warning(s)"
        ),
        "",
    ]
    if report.get("issues"):
        lines.append("## Issues")
        for issue in report["issues"]:
            lines.append(
                f"- [{issue['severity']}] {issue['check']}: "
                f"{issue['message']} ({issue['path']})"
            )
        lines.append("")
    return "\n".join(lines)


def run(all_packs: bool = False, pack: str | None = None, fmt: str = "json",
        cwd: str | None = None) -> int:
    if not all_packs and not pack:
        all_packs = True
    start = Path(cwd).resolve() if cwd else None
    resolved = cmd_resolve.resolve(cwd=start, require_workspace=False)
    root_raw = resolved.get("knowledge_root") or resolved.get("wiki_root")
    if not root_raw:
        print("Error: Could not resolve knowledge_root.", file=sys.stderr)
        return 1
    root = Path(str(root_raw)).resolve()
    pack_names = None if all_packs else [str(pack)]
    report = pack_validation.validate_packs(root, pack_names=pack_names)
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
    parser = argparse.ArgumentParser(description="Validate contextd packs and retrieval maps.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Validate all packs")
    group.add_argument("--pack", default=None, help="Validate a single pack")
    parser.add_argument("--cwd", default=None, help="Start directory (default: current)")
    parser.add_argument("--format", choices=["text", "json"], default="json")
    args = parser.parse_args()
    sys.exit(run(all_packs=args.all, pack=args.pack, fmt=args.format, cwd=args.cwd))


if __name__ == "__main__":
    main()
