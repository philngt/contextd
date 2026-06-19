#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve a contextd contract id to a file path."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_resolve  # noqa: E402
import task_context_engine  # noqa: E402


def run(contract_id: str, workspace: str | None = None,
        fmt: str = "text") -> int:
    if not contract_id.strip():
        print("Error: Empty contract id", file=sys.stderr)
        return 1

    resolved = cmd_resolve.resolve(require_workspace=True)
    root_raw = resolved.get("knowledge_root") or resolved.get("wiki_root")
    ws = workspace or resolved.get("workspace")
    if not root_raw or not ws:
        print("Error: Could not resolve workspace context.", file=sys.stderr)
        return 1

    wiki_root = Path(root_raw).resolve()
    packs = resolved.get("packs") or []
    path, warnings = task_context_engine.resolve_contract_path(
        contract_id, wiki_root, ws, packs,
    )

    if fmt == "json":
        payload = {
            "contract_id": contract_id,
            "workspace": ws,
            "path": str(path) if path else None,
            "warnings": warnings,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif path:
        print(path)
    else:
        print(f"Contract not found: {contract_id}", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)

    return 0 if path else 1


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Resolve a contextd contract id.")
    parser.add_argument("contract_id", help="Contract id, e.g. citation-format")
    parser.add_argument("--workspace", default=None, help="Override workspace")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    sys.exit(run(args.contract_id, workspace=args.workspace, fmt=args.format))


if __name__ == "__main__":
    main()
