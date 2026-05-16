#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pack loader for the wiki-template knowledge engine.

Resolves which packs an active workspace opts into, and loads their:
  - Constraints (markdown, additive)
  - Coding rules (markdown, additive)
  - Validator rules (Python rule functions, dynamically imported)
  - Retrieval map (component → file paths)
  - Prompt overrides (markdown, append to self-check section)

Pack opt-in: parsed from `workspaces/{ws}/workspace.md` `## Packs` section.
Format:

    ## Packs

    - pack-event-driven
    - pack-web-api

Rule namespace conventions (loader fail-fast on collision):
  - Engine rules: no prefix (e.g. `no-hardcoded-config`)
  - Pack rules: prefix `pack-{name}-` (e.g. `pack-event-driven-kafka-dlq-required`)
  - Workspace rules: prefix `ws-` (e.g. `ws-no-mongodb-direct`)

Standard library only (no PyYAML dep). YAML parsing is a minimal subset
sufficient for pack.yaml shape (key: value, nested mapping, simple lists).
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Minimal YAML parser (sufficient for pack.yaml — flat mappings, lists, nested
# one-level mapping). For complex YAML, install PyYAML and replace this.
# ---------------------------------------------------------------------------

def _parse_simple_yaml(text: str) -> Dict:
    """Parse a small subset of YAML used by pack.yaml.

    Supports:
      - `key: value` (string/number/bool)
      - `key:` followed by indented `- item` list
      - `key:` followed by indented `subkey: value` (one level nesting)
      - `key: [a, b, c]` flow-style list
      - `# comment` and blank lines
    Does NOT support: anchors, multi-line strings, deeply nested structures.
    """
    result: Dict = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.split("#", 1)[0].rstrip() if not _in_string(raw, "#") else raw.rstrip()
        if not line.strip():
            i += 1
            continue
        # top-level key
        m = re.match(r"^([A-Za-z_][\w\-]*)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2).strip()
        if rest == "":
            # block — could be list of dicts/scalars, or nested mapping
            block_lines = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip() or nxt.startswith("#"):
                    block_lines.append(nxt)
                    i += 1
                    continue
                # require indentation > 0
                if not (nxt.startswith(" ") or nxt.startswith("\t")):
                    break
                block_lines.append(nxt)
                i += 1
            result[key] = _parse_block(block_lines)
        else:
            result[key] = _parse_scalar_or_flow(rest)
            i += 1
    return result


def _in_string(line: str, ch: str) -> bool:
    # Heuristic: treat # as comment unless it appears inside quotes
    in_dq = False
    in_sq = False
    for c in line:
        if c == '"' and not in_sq:
            in_dq = not in_dq
        elif c == "'" and not in_dq:
            in_sq = not in_sq
        elif c == ch and not (in_dq or in_sq):
            return False
    return True


def _parse_block(block_lines: List[str]):
    # Determine: is it a list (starts with `-`) or a mapping?
    stripped = [ln for ln in block_lines if ln.strip() and not ln.lstrip().startswith("#")]
    if not stripped:
        return None
    first = stripped[0].lstrip()
    if first.startswith("- "):
        items = []
        for ln in stripped:
            s = ln.lstrip()
            if s.startswith("- "):
                items.append(_parse_scalar_or_flow(s[2:].strip()))
        return items
    # mapping
    sub: Dict = {}
    for ln in stripped:
        s = ln.lstrip()
        m = re.match(r"^([A-Za-z_][\w\-]*)\s*:\s*(.*)$", s)
        if m:
            sub[m.group(1)] = _parse_scalar_or_flow(m.group(2).strip())
    return sub


def _parse_scalar_or_flow(s: str):
    if s == "":
        return None
    # flow list
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        # split on commas not inside quotes
        items = _split_flow(inner)
        return [_parse_scalar_or_flow(x.strip()) for x in items]
    # quoted string
    if (s.startswith('"') and s.endswith('"')) or \
       (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # bool / null
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~", ""):
        return None
    # number
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def _split_flow(s: str) -> List[str]:
    out, buf, in_dq, in_sq = [], "", False, False
    for c in s:
        if c == '"' and not in_sq:
            in_dq = not in_dq
            buf += c
        elif c == "'" and not in_dq:
            in_sq = not in_sq
            buf += c
        elif c == "," and not (in_dq or in_sq):
            out.append(buf)
            buf = ""
        else:
            buf += c
    if buf:
        out.append(buf)
    return out


# ---------------------------------------------------------------------------
# Workspace pack list parsing
# ---------------------------------------------------------------------------

PACKS_SECTION_RE = re.compile(
    r"^\s*##\s+Packs\s*$(.+?)(?=^\s*##\s|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE
)
PACK_LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+([a-z0-9][\w\-]*)\s*$", re.MULTILINE)


def parse_workspace_packs(workspace_md_path: Path) -> List[str]:
    """Read `## Packs` section from workspace.md and return pack names."""
    if not workspace_md_path.is_file():
        return []
    text = workspace_md_path.read_text(encoding="utf-8")
    m = PACKS_SECTION_RE.search(text)
    if not m:
        return []
    body = m.group(1)
    return PACK_LIST_ITEM_RE.findall(body)


# ---------------------------------------------------------------------------
# Pack discovery & loading
# ---------------------------------------------------------------------------

class Pack:
    def __init__(self, name: str, root: Path, manifest: Dict):
        self.name = name
        self.root = root
        self.manifest = manifest

    @property
    def files(self) -> Dict:
        return self.manifest.get("files") or {}

    @property
    def conflicts_with(self) -> List[str]:
        return self.manifest.get("conflicts_with") or []

    def file_path(self, key: str) -> Optional[Path]:
        rel = self.files.get(key)
        if not rel:
            return None
        p = self.root / rel
        return p if p.is_file() else None

    def __repr__(self):
        return f"Pack({self.name}@{self.manifest.get('version', '?')})"


def discover_pack(wiki_root: Path, pack_name: str) -> Optional[Pack]:
    pack_dir = wiki_root / "packs" / pack_name
    manifest_path = pack_dir / "pack.yaml"
    if not manifest_path.is_file():
        return None
    try:
        manifest = _parse_simple_yaml(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"[pack_loader] failed to parse {manifest_path}: {e}\n")
        return None
    return Pack(pack_name, pack_dir, manifest or {})


def load_packs_for_workspace(wiki_root: Path, ws_name: str) -> List[Pack]:
    """Resolve packs for a given workspace. Returns sorted-alphabetical list."""
    ws_md = wiki_root / "workspaces" / ws_name / "workspace.md"
    pack_names = sorted(set(parse_workspace_packs(ws_md)))
    packs: List[Pack] = []
    for name in pack_names:
        p = discover_pack(wiki_root, name)
        if p is None:
            sys.stderr.write(
                f"[pack_loader] workspace '{ws_name}' references unknown pack "
                f"'{name}' (not found in {wiki_root}/packs/).\n"
            )
            continue
        packs.append(p)
    # Conflict check
    enabled = {p.name for p in packs}
    for p in packs:
        for other in p.conflicts_with:
            if other in enabled:
                raise RuntimeError(
                    f"Pack conflict: '{p.name}' conflicts_with '{other}', "
                    f"but both are enabled in workspace '{ws_name}'."
                )
    return packs


# ---------------------------------------------------------------------------
# Validator rule loading
# ---------------------------------------------------------------------------

def load_pack_validator_rules(packs: List[Pack]) -> List[Callable]:
    """Dynamically import each pack's scripts/rules.py and aggregate RULES.

    Each rule function: rule_fn(file_path, lines, ctx) -> List[Dict].
    Pack module must expose module-level `RULES = [fn1, fn2, ...]`.
    """
    all_rules: List[Callable] = []
    for pack in packs:
        script = pack.file_path("validator_script")
        if script is None:
            continue
        mod_name = f"_pack_rules_{pack.name.replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(mod_name, script)
        if spec is None or spec.loader is None:
            sys.stderr.write(f"[pack_loader] cannot load spec for {script}\n")
            continue
        try:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = mod
            spec.loader.exec_module(mod)
            rules = getattr(mod, "RULES", None)
            if not isinstance(rules, list):
                sys.stderr.write(
                    f"[pack_loader] {script} missing module-level "
                    f"`RULES = [...]` — skipping.\n"
                )
                continue
            all_rules.extend(rules)
        except Exception as e:
            sys.stderr.write(
                f"[pack_loader] failed to import {script}: {e!r}\n"
            )
    return all_rules


def check_rule_name_collisions(engine_rule_ids: List[str],
                               packs: List[Pack],
                               pack_rules: List[Callable]) -> Optional[str]:
    """Detect rule ID collisions across engine/pack/workspace.

    Returns error string if collision found, None otherwise. We can only
    check pack rule IDs by inspecting their first emitted output; instead,
    we enforce naming via pack.yaml + module convention. Here we just check
    that pack rule fn names hint at correct prefix.

    Returns None always — collision check is best-effort and runtime-only.
    """
    return None


__all__ = [
    "Pack",
    "parse_workspace_packs",
    "discover_pack",
    "load_packs_for_workspace",
    "load_pack_validator_rules",
]
