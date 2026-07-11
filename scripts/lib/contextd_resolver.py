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

try:
    from . import context_security
except ImportError:  # pragma: no cover - top-level script import path
    import context_security  # type: ignore


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
# Capture every declared list item. Validation happens separately so malformed
# identifiers are blocking errors instead of disappearing from the selection.
PACK_LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class ConfigHit:
    path: Path
    kind: str
    project_dir: Path
    data: Dict


class PackResolutionError(ValueError):
    """Blocking active-pack resolution error with diagnostic selection data."""

    def __init__(self, message: str, *, packs: Optional[List[str]] = None,
                 source: Optional[str] = None, code: str = "invalid-pack"):
        super().__init__(message)
        self.packs = list(packs or [])
        self.source = source
        self.code = code


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


def _raw_knowledge_root(data: Dict) -> object:
    value = data.get("knowledge_root")
    if value:
        return value
    return data.get("wiki_root")


def _raw_workspace(data: Dict) -> object:
    return data.get("workspace") or data.get("default_workspace")


def _resolve_root(raw_value: object, base_dir: Path) -> Optional[Path]:
    if not raw_value:
        return None
    if not isinstance(raw_value, str):
        return None
    p = Path(raw_value).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (base_dir / p).resolve()


def parse_workspace_packs(workspace_md_path: Path) -> List[str]:
    """Read `## Packs` section from workspace.md and return pack names."""
    if not workspace_md_path.is_file():
        return []
    if workspace_md_path.is_symlink():
        raise ValueError(f"workspace.md must not be a symlink: {workspace_md_path}")
    try:
        text = workspace_md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"Could not read workspace.md: {workspace_md_path}: {exc}") from exc
    m = PACKS_SECTION_RE.search(text)
    if not m:
        return []
    return PACK_LIST_ITEM_RE.findall(m.group(1))


def get_effective_packs(config: Dict, workspace_md_path: Path) -> Tuple[List[object], str]:
    local = config.get("packs")
    if isinstance(local, list):
        # Preserve value types so a non-string entry cannot become a valid pack
        # name through implicit coercion (for example, `123` -> `"123"`).
        return list(local), "config"
    return parse_workspace_packs(workspace_md_path), "workspace.md"


def _valid_pack_names(raw_packs: List[object], source: str) -> List[str]:
    packs: List[str] = []
    errors: List[str] = []
    for raw_pack in raw_packs:
        pack_name, error = context_security.validate_context_name(raw_pack, "pack")
        if error or pack_name is None:
            errors.append(f"{raw_pack!r} ({error})")
            continue
        packs.append(pack_name)
    if errors:
        raise PackResolutionError(
            f"Invalid pack name from {source}: " + "; ".join(errors),
            source=source,
        )
    return packs


def _validated_workspace_md(ws_dir: Path) -> Path:
    """Return a regular, non-aliased workspace.md for a named workspace."""
    workspace_md = ws_dir / "workspace.md"
    if not workspace_md.is_file():
        raise ValueError(f"workspace.md missing: {workspace_md}")
    if workspace_md.is_symlink():
        raise ValueError(f"workspace.md must not be a symlink: {workspace_md}")
    try:
        return context_security.confined_child(
            ws_dir, "workspace.md", "workspace.md", allow_symlink=False
        )
    except ValueError as exc:
        raise ValueError(f"Invalid workspace.md: {exc}") from exc


def resolve_workspace_packs(
    knowledge_root: Path,
    workspace: object,
    *,
    resolved: Optional[Dict] = None,
    config: Optional[Dict] = None,
) -> Tuple[List[str], str]:
    """Resolve and validate effective packs for one exact workspace.

    A caller-provided workspace equal to the already resolved workspace keeps
    the codebase-level `config.packs` replacement semantics. Switching to a
    different workspace uses that workspace's defaults from `workspace.md`.
    Every selected pack must be a valid, non-aliased named root containing a
    regular `pack.yaml`; otherwise the whole resolution fails closed.
    """
    root = knowledge_root.resolve()
    ws_name, workspace_error = context_security.validate_context_name(
        workspace, "workspace"
    )
    if workspace_error or ws_name is None:
        raise ValueError(workspace_error or "invalid workspace")
    ws_dir = context_security.workspace_dir(root, ws_name)
    workspace_md = _validated_workspace_md(ws_dir)

    if resolved is not None and ws_name == resolved.get("workspace"):
        if resolved.get("error") in {"invalid-pack", "missing-pack"}:
            raise ValueError("Resolved configuration contains an invalid active pack")
        raw_packs: List[object] = list(resolved.get("packs") or [])
        source = str(resolved.get("pack_source") or "resolved")
    else:
        raw_packs, source = get_effective_packs(config or {}, workspace_md)

    packs = _valid_pack_names(raw_packs, source)
    for pack_name in packs:
        try:
            pack_root = context_security.pack_dir(root, pack_name)
            pack_manifest = context_security.confined_child(
                pack_root, "pack.yaml", "pack manifest", allow_symlink=False
            )
        except ValueError as exc:
            raise PackResolutionError(
                f"Invalid active pack {pack_name!r}: {exc}",
                packs=packs,
                source=source,
            ) from exc
        if not pack_manifest.is_file():
            raise PackResolutionError(
                f"Active pack not found: {pack_name}",
                packs=packs,
                source=source,
                code="missing-pack",
            )
    return packs, source


def select_workspace_state(
    resolved: Dict,
    workspace: object = None,
    *,
    knowledge_root: Optional[Path] = None,
) -> Tuple[Path, str, Path, List[str], str]:
    """Select one workspace and its effective packs from a resolver result.

    This is the common adapter boundary for CLI, renderers, and MCP. It keeps
    local pack replacement semantics only when the target root/workspace are
    the same state that produced ``resolved``. An explicit switch to another
    workspace or root uses that target workspace's defaults.
    """
    root_raw = knowledge_root or resolved.get("knowledge_root") or resolved.get("wiki_root")
    if not root_raw:
        raise ValueError("Could not resolve knowledge_root")
    root = Path(root_raw).expanduser().resolve()

    target = workspace if workspace is not None else resolved.get("workspace")
    ws_name, workspace_error = context_security.validate_context_name(target, "workspace")
    if workspace_error or ws_name is None:
        raise ValueError(workspace_error or "No workspace resolved")

    ws_dir = context_security.workspace_dir(root, ws_name)
    _validated_workspace_md(ws_dir)

    resolved_root_raw = resolved.get("knowledge_root") or resolved.get("wiki_root")
    same_root = False
    if resolved_root_raw:
        try:
            same_root = Path(str(resolved_root_raw)).expanduser().resolve() == root
        except (OSError, RuntimeError):
            same_root = False
    reuse_resolved = (
        same_root
        and ws_name == resolved.get("workspace")
    )
    packs, source = resolve_workspace_packs(
        root,
        ws_name,
        resolved=resolved if reuse_resolved else None,
    )
    return root, ws_name, ws_dir, packs, source


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
    raw_root = _raw_knowledge_root(cfg)
    if raw_root is not None and not isinstance(raw_root, str):
        warnings.append("knowledge_root/wiki_root must be a string.")
        result["error"] = "invalid-knowledge-root"
        return result
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

    # Resolve root diagnostics independently from workspace identity. A bad
    # workspace must still block all workspace reads, but callers such as
    # doctor/init need the valid root to explain available workspaces.
    raw_workspace = _raw_workspace(cfg)
    workspace, workspace_error = context_security.validate_context_name(
        raw_workspace, "workspace"
    )
    if workspace_error or workspace is None:
        if raw_workspace:
            warnings.append(f"Invalid workspace name: {raw_workspace!r} ({workspace_error})")
        else:
            warnings.append("Config has no workspace/default_workspace field.")
        if require_workspace:
            result["error"] = "invalid-workspace" if raw_workspace else "missing-workspace"
        return result
    result["workspace"] = workspace

    try:
        ws_dir = context_security.workspace_dir(root, workspace)
    except ValueError as exc:
        warnings.append(str(exc))
        if require_workspace:
            result["error"] = "invalid-workspace"
        return result

    workspace_md: Optional[Path] = None
    if ws_dir.is_dir():
        try:
            workspace_md = _validated_workspace_md(ws_dir)
        except ValueError as exc:
            warnings.append(str(exc))
    if workspace_md is not None:
        result["workspace_dir"] = str(ws_dir)
    else:
        result["workspace_dir"] = None
        if not ws_dir.is_dir():
            warnings.append(f"Workspace directory not found: {ws_dir}")
        available = available_workspaces(root)
        if available:
            warnings.append("Available workspaces: " + ", ".join(available))
        if require_workspace:
            result["error"] = "missing-workspace-dir" if not ws_dir.is_dir() else "missing-workspace-md"
        return result

    try:
        packs, source = resolve_workspace_packs(
            root,
            workspace,
            config=cfg,
        )
    except ValueError as exc:
        message = str(exc)
        warnings.append(message)
        result["packs"] = list(getattr(exc, "packs", []))
        result["pack_source"] = getattr(exc, "source", None) or (
            "config" if isinstance(cfg.get("packs"), list) else "workspace.md"
        )
        result["error"] = getattr(exc, "code", "invalid-pack")
        return result
    result["packs"] = packs
    result["pack_source"] = source

    return result


def available_workspaces(knowledge_root: Path) -> List[str]:
    try:
        root = context_security.confined_child(
            knowledge_root,
            "workspaces",
            "workspaces root",
            allow_symlink=False,
        )
    except ValueError:
        return []
    if not root.is_dir():
        return []
    names: List[str] = []
    for path in root.iterdir():
        name, error = context_security.validate_context_name(path.name, "workspace")
        if error or name is None:
            continue
        if not path.is_dir() or path.is_symlink():
            continue
        try:
            ws_dir = context_security.workspace_dir(knowledge_root, name)
            _validated_workspace_md(ws_dir)
        except ValueError:
            continue
        names.append(name)
    return sorted(names)
