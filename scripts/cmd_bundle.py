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
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_resolve  # noqa: E402
import context_security  # noqa: E402
import contextd_resolver  # noqa: E402


def _confined_file(path: Path, allowed_root: Path, label: str) -> Optional[Path]:
    try:
        relative = path.relative_to(allowed_root)
        safe = context_security.confined_child(
            allowed_root, relative, label, allow_symlink=False
        )
    except (OSError, RuntimeError, ValueError):
        return None
    if not safe.is_file():
        return None
    if context_security.path_policy_reason(safe, logical_path=path):
        return None
    return safe


def _collect_workspace_files(ws_dir: Path) -> List[Path]:
    """Collect all markdown files from a workspace directory."""
    files: List[Path] = []
    scan_specs = [
        ("platform/contracts", "*.md"),
        ("platform/patterns", "*.md"),
        ("projects", "**/services/*.md"),
        ("runbooks", "*.md"),
        ("domains", "**/*.md"),
        ("decisions", "**/*.md"),
        ("agents", "**/*.md"),
    ]
    for directory, pattern in scan_specs:
        try:
            scan_root = context_security.confined_child(
                ws_dir,
                directory,
                "workspace bundle directory",
                allow_symlink=False,
            )
        except ValueError:
            continue
        if not scan_root.is_dir():
            continue
        files.extend(
            sorted(
                safe
                for p in scan_root.glob(pattern)
                if (safe := _confined_file(p, ws_dir, "workspace document")) is not None
            )
        )
    for filename in ("patterns-index.md", "workspace.md"):
        safe = _confined_file(ws_dir / filename, ws_dir, "workspace document")
        if safe is not None:
            files.append(safe)
    return files


def _collect_pack_files(wiki_root: Path, pack_name: str) -> List[Path]:
    """Collect key markdown files from a pack."""
    try:
        pack_dir = context_security.pack_dir(wiki_root, pack_name)
    except ValueError:
        return []
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
        p = _confined_file(pack_dir / rel, pack_dir, "pack document")
        if p is not None:
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
        p = _confined_file(wiki_root / rel, wiki_root, "engine document")
        if p is not None:
            files.append(p)
    return files


def _read_md(path: Path, allowed_root: Path) -> Optional[str]:
    safe = _confined_file(path, allowed_root, "bundle document")
    if safe is None:
        return None
    try:
        return safe.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def bundle(
    workspace: Optional[str] = None,
    output_dir: Optional[Path] = None,
    max_chars: Optional[int] = None,
    include_packs: bool = False,
    include_engine: bool = False,
    cwd: Optional[Path] = None,
    knowledge_root: Optional[Path] = None,
    packs_override: Optional[List[str]] = None,
) -> str:
    """Build a single markdown bundle. Returns the bundle content."""
    resolved = cmd_resolve.resolve(cwd=cwd, require_workspace=True)
    try:
        wiki_root, ws, ws_dir, packs, _pack_source = (
            contextd_resolver.select_workspace_state(
                resolved,
                workspace,
                knowledge_root=knowledge_root,
            )
        )
    except ValueError as exc:
        _safe_workspace, workspace_error = context_security.validate_context_name(
            workspace if workspace is not None else resolved.get("workspace"),
            "workspace",
        )
        if workspace_error:
            raise RuntimeError(f"Invalid workspace: {workspace_error}") from exc
        raise RuntimeError(f"Could not resolve workspace state: {exc}") from exc

    if packs_override is not None:
        try:
            packs, _ = contextd_resolver.resolve_workspace_packs(
                wiki_root,
                ws,
                resolved={
                    "workspace": ws,
                    "packs": list(packs_override),
                    "pack_source": "override",
                },
            )
        except ValueError as exc:
            raise RuntimeError(f"Invalid pack override: {exc}") from exc

    parts: List[str] = []
    parts.append(f"# contextd Bundle — workspace: {ws}")
    parts.append("Generated from: knowledge_root")
    parts.append("")

    # Workspace files
    ws_files = _collect_workspace_files(ws_dir)
    for p in ws_files:
        content = _read_md(p, ws_dir)
        if content is None:
            continue
        rel = context_security.root_relative_posix(p, wiki_root)
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
                pack_root = context_security.pack_dir(wiki_root, pack_name)
                content = _read_md(p, pack_root)
                if content is None:
                    continue
                rel = context_security.root_relative_posix(p, wiki_root)
                parts.append(f"---")
                parts.append(f"# Source: {rel}")
                parts.append("")
                parts.append(content)
                parts.append("")

    # Engine files
    if include_engine:
        engine_files = _collect_engine_files(wiki_root)
        for p in engine_files:
            content = _read_md(p, wiki_root)
            if content is None:
                continue
            rel = context_security.root_relative_posix(p, wiki_root)
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
