#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd bundle — merge workspace knowledge into a single markdown bundle.

Usage:
    contextd bundle --workspace default [--output ./] [--max-chars N]
                    [--include-packs] [--include-engine]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import cmd_resolve  # noqa: E402


def _collect_workspace_files(ws_dir: Path) -> List[Path]:
    """Collect all markdown files from a workspace directory."""
    files: List[Path] = []
    for pattern in [
        "platform/contracts/*.md",
        "platform/patterns/*.md",
        "projects/**/services/*.md",
        "runbooks/*.md",
        "domains/**/*.md",
        "decisions/**/*.md",
        "agents/**/*.md",
        "patterns-index.md",
        "workspace.md",
    ]:
        files.extend(sorted(ws_dir.glob(pattern)))
    return files


def _collect_pack_files(wiki_root: Path, pack_name: str) -> List[Path]:
    """Collect key markdown files from a pack."""
    pack_dir = wiki_root / "packs" / pack_name
    if not pack_dir.is_dir():
        return []
    files: List[Path] = []
    for rel in [
        "agents/constraints.md",
        "agents/coding-rules.md",
        "agents/common-pitfalls.md",
        "agents/pipeline/validator-rules.md",
        "agents/pipeline/retrieval-map.md",
        "README.md",
    ]:
        p = pack_dir / rel
        if p.is_file():
            files.append(p)
    return files


def _collect_engine_files(wiki_root: Path) -> List[Path]:
    """Collect key engine markdown files."""
    files: List[Path] = []
    for rel in [
        "agents/system-prompt.md",
        "agents/constraints.md",
        "agents/coding-rules.md",
        "agents/cross-cutting-principles.md",
    ]:
        p = wiki_root / rel
        if p.is_file():
            files.append(p)
    return files


def _read_md(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def bundle(
    workspace: Optional[str] = None,
    output_dir: Optional[Path] = None,
    max_chars: Optional[int] = None,
    include_packs: bool = False,
    include_engine: bool = False,
) -> str:
    """Build a single markdown bundle. Returns the bundle content."""
    resolved = cmd_resolve.resolve()
    wiki_root_str = resolved.get("knowledge_root") or resolved.get("wiki_root")
    if not wiki_root_str:
        raise RuntimeError("Could not resolve knowledge_root. Run `contextd resolve` to diagnose.")

    wiki_root = Path(wiki_root_str).resolve()
    ws = workspace or resolved.get("workspace")
    packs = resolved.get("packs") or []

    if not ws:
        raise RuntimeError("No workspace resolved. Specify --workspace or run `contextd resolve`.")

    ws_dir = wiki_root / "workspaces" / ws
    if not ws_dir.is_dir():
        raise RuntimeError(f"Workspace directory not found: {ws_dir}")

    parts: List[str] = []
    parts.append(f"# contextd Bundle — workspace: {ws}")
    parts.append(f"Generated from: {wiki_root}")
    parts.append("")

    # Workspace files
    ws_files = _collect_workspace_files(ws_dir)
    for p in ws_files:
        content = _read_md(p)
        if content is None:
            continue
        rel = p.relative_to(wiki_root)
        parts.append(f"---")
        parts.append(f"# Source: {rel}")
        parts.append("")
        parts.append(content)
        parts.append("")

    # Pack files
    if include_packs:
        for pack_name in packs:
            pack_files = _collect_pack_files(wiki_root, pack_name)
            for p in pack_files:
                content = _read_md(p)
                if content is None:
                    continue
                rel = p.relative_to(wiki_root)
                parts.append(f"---")
                parts.append(f"# Source: {rel}")
                parts.append("")
                parts.append(content)
                parts.append("")

    # Engine files
    if include_engine:
        engine_files = _collect_engine_files(wiki_root)
        for p in engine_files:
            content = _read_md(p)
            if content is None:
                continue
            rel = p.relative_to(wiki_root)
            parts.append(f"---")
            parts.append(f"# Source: {rel}")
            parts.append("")
            parts.append(content)
            parts.append("")

    bundle_text = "\n".join(parts)

    if max_chars and len(bundle_text) > max_chars:
        bundle_text = bundle_text[:max_chars]
        bundle_text += f"\n\n\n[TRUNCATED at {max_chars} chars]"

    return bundle_text


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bundle workspace knowledge into a single markdown file.")
    parser.add_argument("--workspace", default=None, help="Workspace name (default: resolved)")
    parser.add_argument("--output", default=None, help="Output directory or file (default: stdout)")
    parser.add_argument("--max-chars", type=int, default=None, help="Truncate bundle after N chars")
    parser.add_argument("--include-packs", action="store_true", help="Include active packs")
    parser.add_argument("--include-engine", action="store_true", help="Include engine docs")
    args = parser.parse_args()

    try:
        result = bundle(
            workspace=args.workspace,
            output_dir=Path(args.output).parent if args.output else None,
            max_chars=args.max_chars,
            include_packs=args.include_packs,
            include_engine=args.include_engine,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(result, encoding="utf-8")
        print(f"Bundle written to: {out_path}")
    else:
        print(result)


if __name__ == "__main__":
    main()
