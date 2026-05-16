#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-patterns-index.py - Verify {ws}/patterns-index.md stays in sync with
{ws}/platform/{patterns,contracts}/*.md.

Flags drift:
  - File exists in folder but missing from index ("orphan file")
  - File listed in index but missing from folder ("dangling entry")
  - Index entry's link path doesn't resolve

Read-only. Exits non-zero if drift found, so CI can gate.

Usage:
    python scripts/check-patterns-index.py                  # all workspaces
    python scripts/check-patterns-index.py --workspace wiki # one workspace
    python scripts/check-patterns-index.py --fix-hint       # print suggested entries
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACES_DIR = REPO_ROOT / "workspaces"

# Match markdown table rows referencing a pattern/contract file.
# Format: | `name` | description | [path](link) |
LINK_RE = re.compile(r"\(([^)]*platform/(?:patterns|contracts)/[^)]+\.md)\)")


def parse_index(path: Path) -> List[Tuple[str, str]]:
    """Return list of (kind, relative-path) extracted from index links.
    kind = 'patterns' or 'contracts'.
    """
    if not path.exists():
        return []
    out = []
    for match in LINK_RE.finditer(path.read_text(encoding="utf-8")):
        link = match.group(1)
        rel = link.split("platform/")[1]  # patterns/xxx.md or contracts/xxx.md
        kind, fname = rel.split("/", 1)
        out.append((kind, fname))
    return out


def list_files(ws_dir: Path, kind: str) -> List[str]:
    folder = ws_dir / "platform" / kind
    if not folder.is_dir():
        return []
    return sorted(
        f.name
        for f in folder.iterdir()
        if f.is_file() and f.suffix == ".md" and f.name != "README.md"
    )


def check_workspace(ws_dir: Path, print_hints: bool) -> int:
    """Return number of drift issues found."""
    ws_name = ws_dir.name
    index_path = ws_dir / "patterns-index.md"
    indexed = parse_index(index_path)
    indexed_by_kind: Dict[str, set] = {"patterns": set(), "contracts": set()}
    for kind, fname in indexed:
        indexed_by_kind.setdefault(kind, set()).add(fname)

    drift = 0
    for kind in ("patterns", "contracts"):
        actual = set(list_files(ws_dir, kind))
        listed = indexed_by_kind.get(kind, set())
        orphans = actual - listed
        dangling = listed - actual

        for fname in sorted(orphans):
            drift += 1
            print(f"[{ws_name}] ORPHAN  {kind}/{fname} "
                  f"-- file exists but not in patterns-index.md")
            if print_hints:
                print(f"  | `{fname[:-3]}` | TODO: describe when to use | "
                      f"[platform/{kind}/{fname}](platform/{kind}/{fname}) |")

        for fname in sorted(dangling):
            drift += 1
            print(f"[{ws_name}] DANGLE  {kind}/{fname} "
                  f"-- listed in index but file missing")

    if not index_path.exists() and (
        list_files(ws_dir, "patterns") or list_files(ws_dir, "contracts")
    ):
        drift += 1
        print(f"[{ws_name}] MISSING patterns-index.md "
              f"(workspace has patterns/contracts)")

    return drift


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--workspace", help="Check only this workspace")
    ap.add_argument("--fix-hint", action="store_true",
                    help="Print suggested table rows for orphans")
    args = ap.parse_args()

    if args.workspace:
        targets = [WORKSPACES_DIR / args.workspace]
        if not targets[0].is_dir():
            print(f"ERROR: workspace not found: {args.workspace}",
                  file=sys.stderr)
            sys.exit(2)
    else:
        targets = sorted(
            d for d in WORKSPACES_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
        )

    total = 0
    for ws_dir in targets:
        total += check_workspace(ws_dir, args.fix_hint)

    if total == 0:
        print("[OK] No drift detected.")
        sys.exit(0)
    print(f"\nTotal drift issues: {total}")
    sys.exit(1)


if __name__ == "__main__":
    main()
