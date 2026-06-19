#!/usr/bin/env python3
"""
lint-wiki.py — Detect broken markdown links and orphaned pattern/contract files
in wiki workspaces.

Standard library only. Cross-platform (Windows / Linux / macOS).

Usage:
    python lint-wiki.py [--workspace <name>] [--wiki-root <path>] [--all-workspaces]

Behavior:
- If --workspace omitted: use the shared contextd resolver.
- If --wiki-root omitted: resolve canonical knowledge_root per agents/system-prompt.md rule:
    absolute -> use as-is
    relative -> resolve relative to project root
    null/empty -> fallback global contextd/legacy config
- --all-workspaces: iterate every directory under {wiki-root}/workspaces/*/.

Checks per workspace:
- workspace.md — exists; all md links resolve.
- patterns-index.md — all md links resolve.
- projects/*/knowledge-map.md — all md links resolve.
- Cross-check: every platform/patterns/*.md and platform/contracts/*.md
  is referenced by patterns-index.md (warn-only orphan).

Output:
- JSON to stdout: combined result (single workspace -> dict; multi -> list).
- Human summary to stderr.

Exit codes:
- 0: clean
- 1: broken_links present
- 2: only orphans (warning)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from lib import contextd_resolver

# Markdown inline link: [text](target)
# - Skips images (preceding '!') by using a negative lookbehind.
# - Captures link text (allowing nested brackets minimally) and target up to first ')' or whitespace.
# - Strips optional title: [text](target "title")
LINK_RE = re.compile(
    r"(?<!\!)\[([^\]\n]+)\]\(\s*([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)"
)


def parse_links(md_text: str) -> list[tuple[str, str]]:
    """Return list of (link_text, raw_target) for inline markdown links."""
    out: list[tuple[str, str]] = []
    for m in LINK_RE.finditer(md_text):
        text = m.group(1).strip()
        target = m.group(2).strip()
        out.append((text, target))
    return out


def is_external(target: str) -> bool:
    """True if target is a URL, mailto, or anchor-only link we should skip."""
    if not target:
        return True
    if target.startswith("#"):
        return True
    parsed = urlparse(target)
    if parsed.scheme in ("http", "https", "mailto", "ftp", "ftps", "file", "data"):
        return True
    return False


def resolve_link_target(source_file: Path, target: str) -> Path:
    """Resolve a link target relative to source_file's directory.

    Drops fragment (#anchor) and query (?...). URL-decodes percent-encoded chars.
    """
    # Strip fragment / query
    raw = target
    for sep in ("#", "?"):
        i = raw.find(sep)
        if i != -1:
            raw = raw[:i]
    raw = unquote(raw)
    if not raw:
        # pure anchor — shouldn't reach here
        return source_file
    p = Path(raw)
    if p.is_absolute():
        return p
    return (source_file.parent / p).resolve()


def check_file_links(
    source_file: Path, broken: list[dict]
) -> None:
    """Parse source_file, append broken links to broken list."""
    try:
        text = source_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        broken.append({
            "source_file": str(source_file),
            "link_text": "<self>",
            "target": "<file missing>",
            "resolved_to": str(source_file),
        })
        return
    for text_label, target in parse_links(text):
        if is_external(target):
            continue
        resolved = resolve_link_target(source_file, target)
        # Allow link to a directory (e.g. [foo](platform/contracts/)) — accept if dir exists
        if not (resolved.is_file() or resolved.is_dir()):
            broken.append({
                "source_file": str(source_file),
                "link_text": text_label,
                "target": target,
                "resolved_to": str(resolved),
            })


def lint_workspace(ws_root: Path) -> dict:
    """Run all checks on a single workspace directory."""
    result: dict = {
        "workspace": ws_root.name,
        "broken_links": [],
        "orphans": [],
        "summary": {"broken": 0, "orphaned": 0},
    }

    if not ws_root.is_dir():
        result["broken_links"].append({
            "source_file": str(ws_root),
            "link_text": "<workspace>",
            "target": "<missing>",
            "resolved_to": str(ws_root),
        })
        result["summary"]["broken"] = 1
        return result

    broken: list[dict] = result["broken_links"]

    # 1. workspace.md
    workspace_md = ws_root / "workspace.md"
    if not workspace_md.is_file():
        broken.append({
            "source_file": str(workspace_md),
            "link_text": "<workspace.md>",
            "target": "<missing>",
            "resolved_to": str(workspace_md),
        })
    else:
        check_file_links(workspace_md, broken)

    # 2. patterns-index.md
    patterns_index = ws_root / "patterns-index.md"
    patterns_index_text = ""
    if not patterns_index.is_file():
        broken.append({
            "source_file": str(patterns_index),
            "link_text": "<patterns-index.md>",
            "target": "<missing>",
            "resolved_to": str(patterns_index),
        })
    else:
        check_file_links(patterns_index, broken)
        patterns_index_text = patterns_index.read_text(encoding="utf-8")

    # 3. every projects/*/knowledge-map.md
    projects_dir = ws_root / "projects"
    if projects_dir.is_dir():
        for proj in sorted(projects_dir.iterdir()):
            if not proj.is_dir():
                continue
            km = proj / "knowledge-map.md"
            if km.is_file():
                check_file_links(km, broken)
            # else: not an error — project may not have one yet.

    # 4. orphan check — patterns and contracts not referenced in patterns-index
    orphans: list[dict] = result["orphans"]
    referenced_paths: set[Path] = set()
    if patterns_index_text:
        for _label, target in parse_links(patterns_index_text):
            if is_external(target):
                continue
            resolved = resolve_link_target(patterns_index, target)
            try:
                referenced_paths.add(resolved.resolve())
            except OSError:
                referenced_paths.add(resolved)

    for sub in ("platform/patterns", "platform/contracts"):
        d = ws_root / sub
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            try:
                fr = f.resolve()
            except OSError:
                fr = f
            if fr not in referenced_paths:
                orphans.append({
                    "file": str(f),
                    "reason": f"not referenced by patterns-index.md ({sub})",
                })

    result["summary"]["broken"] = len(broken)
    result["summary"]["orphaned"] = len(orphans)
    return result


def print_human_summary(res: dict, stream) -> None:
    ws = res["workspace"]
    b = res["summary"]["broken"]
    o = res["summary"]["orphaned"]
    print(f"[workspace: {ws}] broken={b} orphaned={o}", file=stream)
    for item in res["broken_links"]:
        print(
            f"  BROKEN  {item['source_file']}  ->  {item['target']}  "
            f"(resolved: {item['resolved_to']})",
            file=stream,
        )
    for item in res["orphans"]:
        print(f"  ORPHAN  {item['file']}  ({item['reason']})", file=stream)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lint wiki workspaces for broken links and orphans.")
    ap.add_argument("--workspace", help="Workspace name (under {wiki-root}/workspaces/)")
    ap.add_argument("--wiki-root", help="Override wiki root directory")
    ap.add_argument("--all-workspaces", action="store_true",
                    help="Lint every workspace under {wiki-root}/workspaces/")
    args = ap.parse_args(argv)

    # Resolve project config (only needed if wiki-root or workspace not provided).
    resolved: dict = {}
    if args.wiki_root is None or (args.workspace is None and not args.all_workspaces):
        resolved = contextd_resolver.resolve(Path.cwd())

    # Resolve knowledge_root.
    if args.wiki_root:
        p = Path(args.wiki_root)
        wiki_root = p.resolve() if p.is_absolute() else p.resolve()
    else:
        root = resolved.get("knowledge_root") or resolved.get("wiki_root")
        if not root:
            print("ERROR: no .contextd/config.json or legacy config found by walking up from cwd; "
                  "pass --wiki-root explicitly.", file=sys.stderr)
            return 3
        wiki_root = Path(str(root)).resolve()

    workspaces_dir = wiki_root / "workspaces"
    if not workspaces_dir.is_dir():
        print(f"ERROR: {workspaces_dir} does not exist", file=sys.stderr)
        return 3

    targets: list[Path] = []
    if args.all_workspaces:
        targets = sorted([d for d in workspaces_dir.iterdir() if d.is_dir()])
    else:
        ws_name = args.workspace or resolved.get("workspace")
        if not ws_name:
            print("ERROR: workspace not specified and not found in contextd config",
                  file=sys.stderr)
            return 3
        targets = [workspaces_dir / ws_name]

    results = [lint_workspace(t) for t in targets]

    # JSON output
    payload: Any = results[0] if (len(results) == 1 and not args.all_workspaces) else results
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

    # Human summary
    total_broken = 0
    total_orphan = 0
    for r in results:
        print_human_summary(r, sys.stderr)
        total_broken += r["summary"]["broken"]
        total_orphan += r["summary"]["orphaned"]
    print(f"TOTAL: broken={total_broken} orphaned={total_orphan}", file=sys.stderr)

    if total_broken > 0:
        return 1
    if total_orphan > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
