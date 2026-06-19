#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create canonical .contextd/config.json from existing contextd config."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import contextd_resolver  # noqa: E402


def run(cwd: str | None = None, force: bool = False,
        dry_run: bool = False) -> int:
    start = Path(cwd).resolve() if cwd else Path(".").resolve()
    selected, hits = contextd_resolver.find_config(start)
    if selected is None:
        print("Error: no legacy or canonical config found.", file=sys.stderr)
        return 1

    project_dir = selected.project_dir
    out_path = project_dir / ".contextd" / "config.json"
    if out_path.is_file() and not force and not dry_run:
        print(f"Error: {out_path} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    data = selected.data
    knowledge_root = data.get("knowledge_root") or data.get("wiki_root")
    payload = {
        "project": data.get("project") or project_dir.name,
        "workspace": data.get("workspace") or data.get("default_workspace"),
        "knowledge_root": knowledge_root,
        "packs": data.get("packs", None),
        "compat": {
            "generated_from": str(selected.path),
            "legacy_field_alias": "wiki_root",
        },
    }
    if data.get("domain") is not None:
        payload["domain"] = data.get("domain")
    if data.get("knowledge_map") is not None:
        payload["knowledge_map"] = data.get("knowledge_map")

    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if dry_run:
        print(rendered, end="")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote: {out_path}")
    if hits:
        print("Lower-priority configs kept for compatibility:")
        for hit in hits:
            print(f"  - {hit.path}")
    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Migrate legacy config to .contextd/config.json.")
    parser.add_argument("--cwd", default=None, help="Start directory (default: current)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing .contextd/config.json")
    parser.add_argument("--dry-run", action="store_true", help="Print config without writing")
    args = parser.parse_args()
    sys.exit(run(cwd=args.cwd, force=args.force, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
