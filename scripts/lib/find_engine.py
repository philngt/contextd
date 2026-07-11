#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuzzy search engine for contextd — extracted from .claude/commands/find.md logic.

Scoring (per keyword, case-insensitive substring match):
  Filename (basename without .md)     10
  First H1 heading (# ...)             8
  H2/H3 heading (## ... / ### ...)     5
  First 500 chars (lead paragraph)     3
  Anywhere else in content             1

Score = sum across all keywords. Items with score=0 excluded.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from . import context_security
except ImportError:  # pragma: no cover - top-level script import path
    import context_security  # type: ignore

SKIP_SIZE_BYTES = 100 * 1024  # 100KB

H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
H2_H3_RE = re.compile(r"^(##|###)\s+(.+)$", re.MULTILINE)


def _safe_read_path(path: Path, allowed_root: Path) -> Optional[Path]:
    """Return a canonical regular file without following any symlink."""
    try:
        relative = path.relative_to(allowed_root)
        safe = context_security.confined_child(
            allowed_root, relative, "search document", allow_symlink=False
        )
    except (OSError, RuntimeError, ValueError):
        return None
    if not safe.is_file():
        return None
    if context_security.path_policy_reason(safe, logical_path=path):
        return None
    return safe


def _safe_directory(path: Path, allowed_root: Path, label: str) -> Optional[Path]:
    try:
        relative = path.relative_to(allowed_root)
        safe = context_security.confined_child(
            allowed_root, relative, label, allow_symlink=False
        )
    except (OSError, RuntimeError, ValueError):
        return None
    return safe if safe.is_dir() else None


def _load_file(path: Path) -> Optional[str]:
    """Read a path already accepted by `_safe_read_path`."""
    try:
        if path.stat().st_size > SKIP_SIZE_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _score_for_keyword(keyword: str, text: str, filename: str) -> int:
    """Return score for a single keyword against a file's content."""
    kw = keyword.lower()
    score = 0

    # Filename match
    if kw in filename.lower():
        score += 10

    # Parse headings and lead
    lines = text.splitlines()
    first_h1 = ""
    headings_h2_h3 = []
    lead = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not first_h1:
            first_h1 = stripped[2:].strip()
        elif stripped.startswith("## ") or stripped.startswith("### "):
            headings_h2_h3.append(stripped.lstrip("#").strip())

    if first_h1 and kw in first_h1.lower():
        score += 8

    for h in headings_h2_h3:
        if kw in h.lower():
            score += 5
            break  # only count once for headings

    lead_end = min(500, len(text))
    lead = text[:lead_end]
    if kw in lead.lower():
        score += 3

    # Anywhere else
    if kw in text.lower():
        score += 1

    return score


def _kind_from_path(path: Path, wiki_root: Path, workspace: Optional[str]) -> str:
    """Determine the kind/category of a markdown file."""
    rel = Path(context_security.root_relative_posix(path, wiki_root))
    parts = rel.parts

    if "contracts" in parts:
        return "contract"
    if "patterns" in parts:
        return "pattern"
    if "services" in parts:
        return "service"
    if "runbooks" in parts:
        return "runbook"
    if "projects" in parts:
        return "project"
    if "domains" in parts:
        return "domain"
    if "agents" in parts:
        return "agent"
    if "commands" in parts:
        return "command"
    if "packs" in parts:
        return "pack"
    if rel.name == "cross-cutting-principles.md":
        return "cross-cutting"
    return "doc"


def build_corpus(
    wiki_root: Path,
    workspace: Optional[str] = None,
    packs: Optional[List[str]] = None,
    include_engine: bool = True,
) -> List[Dict]:
    """Build a flat list of searchable items from wiki sources.

    Each item: {path, kind, content, filename}
    """
    corpus: List[Dict] = []

    def _add(paths, kind_override=None, allowed_root: Optional[Path] = None):
        for p in paths:
            if allowed_root is None:
                continue
            safe = _safe_read_path(p, allowed_root)
            if safe is None:
                continue
            content = _load_file(safe)
            if content is None:
                continue
            try:
                relative_path = context_security.root_relative_posix(safe, wiki_root)
            except ValueError:
                continue
            corpus.append({
                "path": safe,
                "relative_path": relative_path,
                "kind": kind_override or _kind_from_path(safe, wiki_root, workspace),
                "content": content,
                "filename": safe.stem,
            })

    # Engine
    if include_engine:
        engine_files = [
            wiki_root / "agents" / "cross-cutting-principles.md",
            wiki_root / "agents" / "constraints.md",
            wiki_root / "agents" / "coding-rules.md",
            wiki_root / "agents" / "system-prompt.md",
        ]
        _add([p for p in engine_files if p.is_file()], "engine", wiki_root)

    # Packs
    if packs is None:
        # All packs
        try:
            packs_dir = context_security.confined_child(
                wiki_root, "packs", "packs root", allow_symlink=False
            )
        except ValueError:
            packs_dir = None
        if packs_dir is not None and packs_dir.is_dir():
            for candidate in packs_dir.iterdir():
                if candidate.is_symlink():
                    continue
                pack_name, error = context_security.validate_context_name(candidate.name, "pack")
                if error or pack_name is None:
                    continue
                try:
                    pack_dir = context_security.pack_dir(wiki_root, pack_name)
                except ValueError:
                    continue
                if not pack_dir.is_dir():
                    continue
                pack_files = [
                    pack_dir / "agents" / "constraints.md",
                    pack_dir / "agents" / "coding-rules.md",
                    pack_dir / "agents" / "common-pitfalls.md",
                    pack_dir / "README.md",
                ]
                _add([p for p in pack_files if p.is_file()], "pack", pack_dir)
    else:
        for pack_name in packs:
            try:
                pack_dir = context_security.pack_dir(wiki_root, pack_name)
            except ValueError:
                continue
            if not pack_dir.is_dir():
                continue
            pack_files = [
                pack_dir / "agents" / "constraints.md",
                pack_dir / "agents" / "coding-rules.md",
                pack_dir / "agents" / "common-pitfalls.md",
                pack_dir / "README.md",
            ]
            _add([p for p in pack_files if p.is_file()], "pack", pack_dir)

    # Workspace
    if workspace:
        try:
            ws_dir = context_security.workspace_dir(wiki_root, workspace)
        except ValueError:
            return corpus
        if ws_dir.is_dir():
            # contracts
            contracts_dir = _safe_directory(
                ws_dir / "platform" / "contracts", ws_dir, "contracts directory"
            )
            if contracts_dir is not None:
                _add(list(contracts_dir.glob("*.md")), "contract", ws_dir)
            # patterns
            patterns_dir = _safe_directory(
                ws_dir / "platform" / "patterns", ws_dir, "patterns directory"
            )
            if patterns_dir is not None:
                _add(list(patterns_dir.glob("*.md")), "pattern", ws_dir)
            # services
            services_dir = _safe_directory(
                ws_dir / "projects", ws_dir, "projects directory"
            )
            if services_dir is not None:
                for proj_dir in services_dir.iterdir():
                    if proj_dir.is_symlink():
                        continue
                    try:
                        rel_project = proj_dir.relative_to(ws_dir)
                        safe_project = context_security.confined_child(
                            ws_dir,
                            rel_project,
                            "project directory",
                            allow_symlink=False,
                        )
                    except ValueError:
                        continue
                    svc_dir = _safe_directory(
                        safe_project / "services", ws_dir, "services directory"
                    )
                    if svc_dir is not None:
                        _add(list(svc_dir.glob("*.md")), "service", ws_dir)
            # runbooks
            runbooks_dir = _safe_directory(
                ws_dir / "runbooks", ws_dir, "runbooks directory"
            )
            if runbooks_dir is not None:
                _add(list(runbooks_dir.glob("*.md")), "runbook", ws_dir)

    return corpus


def find(
    query: str,
    wiki_root: Path,
    workspace: Optional[str] = None,
    packs: Optional[List[str]] = None,
    limit: int = 5,
) -> List[Tuple[int, Dict]]:
    """Search corpus for items matching query keywords.

    Returns list of (score, item) sorted descending by score.
    """
    keywords = [kw.strip() for kw in query.lower().split() if kw.strip()]
    if not keywords:
        return []

    corpus = build_corpus(wiki_root, workspace, packs)
    results: List[Tuple[int, Dict]] = []

    for item in corpus:
        score = sum(_score_for_keyword(kw, item["content"], item["filename"]) for kw in keywords)
        if score > 0:
            results.append((score, item))

    # Sort by score desc
    results.sort(key=lambda x: (-x[0], x[1]["kind"], x[1]["relative_path"]))
    return results[:limit]


def format_result_text(score: int, item: Dict) -> str:
    """Format a single result as human-readable text."""
    rel_path = item["path"]
    # First non-empty line trimmed to 120 chars
    first_line = ""
    for line in item["content"].splitlines():
        stripped = line.strip()
        if stripped:
            first_line = stripped[:120]
            break

    workspace_tag = "(engine)" if item["kind"] == "engine" else f"({item['kind']})"

    return (
        f"  [{item['kind']}] {workspace_tag} {rel_path}\n"
        f"  {first_line}\n"
        f"  Score: {score}\n"
    )


def format_results(results: List[Tuple[int, Dict]], query: str, workspace: Optional[str]) -> str:
    """Format results as plain text."""
    lines = [f'Found {len(results)} match{"es" if len(results) != 1 else ""} for "{query}"'
               f' (workspace: {workspace or "all"}):\n']
    for i, (score, item) in enumerate(results, 1):
        display_path = item["path"]
        lines.append(f"{i}. [{item['kind']}] ({item['kind']}) {display_path}")
        # first non-empty line
        for line in item["content"].splitlines():
            if line.strip():
                lines.append(f"   {line.strip()[:120]}")
                break
        lines.append(f"   Score: {score}")
        lines.append("")
    return "\n".join(lines)
