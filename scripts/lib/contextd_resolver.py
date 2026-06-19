#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared workspace/config resolver for contextd.

Canonical config is `.contextd/config.json`. Legacy `.claude/wiki.json`,
`.Codex/wiki.json`, and their global config files remain supported as
compatibility adapters during the migration window.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


PROJECT_CONFIGS = [
    (".contextd/config.json", "contextd"),
    (".claude/wiki.json", "claude-legacy"),
    (".Codex/wiki.json", "codex-legacy"),
]

GLOBAL_CONFIGS = [
    (Path("~/.contextd/config.json"), "contextd-global"),
    (Path("~/.claude/wiki-global.json"), "claude-global-legacy"),
    (Path("~/.Codex/wiki-global.json"), "codex-global-legacy"),
]

PACKS_SECTION_RE = re.compile(
    r"^\s*##\s+Packs\s*$(.+?)(?=^\s*##\s|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
PACK_LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+([a-z0-9][\w\-]*)\s*$", re.MULTILINE)


@dataclass
class ConfigHit:
    path: Path
    kind: str
    project_dir: Path
    data: Dict


def _read_json(path: Path) -> Dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _candidate_project_configs(start_dir: Path) -> List[ConfigHit]:
    cur = start_dir.resolve()
    by_kind: Dict[str, ConfigHit] = {}
    while True:
        for rel, kind in PROJECT_CONFIGS:
            p = cur / rel
            if p.is_file() and kind not in by_kind:
                by_kind[kind] = ConfigHit(
                    path=p,
                    kind=kind,
                    project_dir=p.parent.parent,
                    data=_read_json(p),
                )
        if cur.parent == cur:
            break
        cur = cur.parent
    return [by_kind[kind] for _, kind in PROJECT_CONFIGS if kind in by_kind]


def _candidate_global_configs() -> List[ConfigHit]:
    hits: List[ConfigHit] = []
    home = Path(os.path.expanduser("~"))
    for raw_path, kind in GLOBAL_CONFIGS:
        p = raw_path.expanduser()
        if p.is_file():
            hits.append(ConfigHit(
                path=p,
                kind=kind,
                project_dir=home,
                data=_read_json(p),
            ))
    return hits


def find_config(start_dir: Optional[Path] = None) -> Tuple[Optional[ConfigHit], List[ConfigHit]]:
    """Return the selected config and other discovered configs.

    Selection follows the canonical order:
    `.contextd/config.json` -> `.claude/wiki.json` -> `.Codex/wiki.json`
    -> `~/.contextd/config.json` -> legacy globals.
    """
    base = (start_dir or Path(".")).resolve()
    project_hits = _candidate_project_configs(base)
    global_hits = _candidate_global_configs()
    all_hits = project_hits + global_hits
    selected = all_hits[0] if all_hits else None
    others = all_hits[1:] if selected else []
    return selected, others


def _raw_knowledge_root(data: Dict) -> Optional[str]:
    value = data.get("knowledge_root")
    if value:
        return value
    return data.get("wiki_root")


def _raw_workspace(data: Dict) -> Optional[str]:
    return data.get("workspace") or data.get("default_workspace")


def _resolve_root(raw_value: Optional[str], base_dir: Path) -> Optional[Path]:
    if not raw_value:
        return None
    p = Path(raw_value).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (base_dir / p).resolve()


def parse_workspace_packs(workspace_md_path: Path) -> List[str]:
    """Read `## Packs` section from workspace.md and return pack names."""
    if not workspace_md_path.is_file():
        return []
    text = workspace_md_path.read_text(encoding="utf-8")
    m = PACKS_SECTION_RE.search(text)
    if not m:
        return []
    return PACK_LIST_ITEM_RE.findall(m.group(1))


def get_effective_packs(config: Dict, workspace_md_path: Path) -> Tuple[List[str], str]:
    local = config.get("packs")
    if isinstance(local, list):
        return [str(p) for p in local], "config"
    return parse_workspace_packs(workspace_md_path), "workspace.md"


def resolve(cwd: Optional[Path] = None, require_workspace: bool = False) -> Dict:
    """Resolve contextd workspace state.

    Returned keys include both canonical `knowledge_root` and legacy `wiki_root`
    for compatibility with existing callers.
    """
    start = (cwd or Path(".")).resolve()
    selected, others = find_config(start)
    warnings: List[str] = []

    result: Dict = {
        "project_dir": None,
        "config_path": None,
        "config_kind": None,
        "wiki_json_path": None,
        "workspace": None,
        "knowledge_root": None,
        "wiki_root": None,
        "workspace_dir": None,
        "packs": [],
        "pack_source": None,
        "warnings": warnings,
        "legacy_configs": [],
    }

    if selected is None:
        warnings.append("No contextd config found from cwd.")
        if require_workspace:
            result["error"] = "missing-config"
        return result

    result["project_dir"] = str(selected.project_dir)
    result["config_path"] = str(selected.path)
    result["config_kind"] = selected.kind
    if selected.kind.endswith("legacy"):
        result["wiki_json_path"] = str(selected.path)

    if selected.kind != "contextd":
        warnings.append(
            f"Using legacy config adapter: {selected.path}. "
            "Create .contextd/config.json to use the canonical config."
        )

    for hit in others:
        result["legacy_configs"].append(str(hit.path))
        if selected.kind == "contextd":
            warnings.append(f"Ignoring lower-priority config: {hit.path}")

    cfg = selected.data
    workspace = _raw_workspace(cfg)
    if not workspace:
        warnings.append("Config has no workspace/default_workspace field.")
        if require_workspace:
            result["error"] = "missing-workspace"
        return result
    result["workspace"] = workspace

    raw_root = _raw_knowledge_root(cfg)
    root = _resolve_root(raw_root, selected.project_dir)
    if root is None:
        for hit in _candidate_global_configs():
            root = _resolve_root(_raw_knowledge_root(hit.data), hit.project_dir)
            if root is not None:
                warnings.append(f"Using knowledge_root from global config: {hit.path}")
                break
    if root is None:
        warnings.append("Could not resolve knowledge_root/wiki_root.")
        if require_workspace:
            result["error"] = "missing-knowledge-root"
        return result

    result["knowledge_root"] = str(root)
    result["wiki_root"] = str(root)

    ws_dir = root / "workspaces" / workspace
    if ws_dir.is_dir():
        result["workspace_dir"] = str(ws_dir)
    else:
        result["workspace_dir"] = None
        warnings.append(f"Workspace directory not found: {ws_dir}")
        available = available_workspaces(root)
        if available:
            warnings.append("Available workspaces: " + ", ".join(available))
        if require_workspace:
            result["error"] = "missing-workspace-dir"

    workspace_md = ws_dir / "workspace.md"
    packs, source = get_effective_packs(cfg, workspace_md)
    result["packs"] = packs
    result["pack_source"] = source

    missing_packs = [p for p in packs if not (root / "packs" / p / "pack.yaml").is_file()]
    for pack_name in missing_packs:
        warnings.append(f"Active pack not found: {pack_name}")

    return result


def available_workspaces(knowledge_root: Path) -> List[str]:
    root = knowledge_root / "workspaces"
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())
