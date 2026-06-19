#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Workspace resolver command for contextd.

The shared implementation lives in `scripts/lib/contextd_resolver.py`.
This module keeps the historical `cmd_resolve.resolve()` import path stable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import contextd_resolver  # noqa: E402


def find_wiki_json(start_dir: Path) -> Optional[Path]:
    """Legacy helper: walk up looking specifically for .claude/wiki.json."""
    cur = start_dir.resolve()
    while True:
        candidate = cur / ".claude" / "wiki.json"
        if candidate.is_file():
            return candidate
        if cur.parent == cur:
            return None
        cur = cur.parent
    return None


def parse_workspace_packs(workspace_md_path: Path) -> List[str]:
    return contextd_resolver.parse_workspace_packs(workspace_md_path)


def get_effective_packs(config: Dict, workspace_md_path: Path) -> Tuple[List[str], str]:
    return contextd_resolver.get_effective_packs(config, workspace_md_path)


def resolve(cwd: Optional[Path] = None, require_workspace: bool = False) -> Dict:
    return contextd_resolver.resolve(cwd=cwd, require_workspace=require_workspace)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Resolve contextd workspace context.")
    parser.add_argument("--cwd", default=None, help="Start directory (default: .)")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="Output format (default: json)")
    args = parser.parse_args()

    cwd = Path(args.cwd).resolve() if args.cwd else None
    result = resolve(cwd)

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for key, value in result.items():
            if isinstance(value, list):
                print(f"{key}:")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{key}: {value}")


if __name__ == "__main__":
    main()
