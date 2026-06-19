#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate .contextd/manifest.json from canonical sources.

Reads:
  - .claude/commands/*.md  → commands[]
  - .claude/agents/*.md    → agents[]
  - packs/*/pack.yaml      → packs[]
  - agents/pipeline/*.md   → pipeline_docs[]

Writes .contextd/manifest.json (generated index, NOT single source of truth).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
import pack_loader  # noqa: E402


def _parse_frontmatter(text: str) -> Optional[Dict[str, str]]:
    """Parse YAML frontmatter block (--- delimited)."""
    if not text.startswith("---"):
        return None
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        return None
    block = rest[:end].lstrip("\n")
    result: Dict[str, str] = {}
    i = 0
    lines = block.splitlines()
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z_][\w\-]*)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "|" or val == ">":
            i += 1
            collected = []
            while i < len(lines) and (lines[i].startswith(" ") or
                                       lines[i].startswith("\t") or
                                       not lines[i].strip()):
                collected.append(lines[i].lstrip())
                i += 1
            result[key] = " ".join(s for s in collected if s)
            continue
        result[key] = val
        i += 1
    return result


def _parse_command_title(path: Path) -> Optional[str]:
    """Parse first H1 line from a command markdown file."""
    try:
        text = path.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if m:
            return m.group(1).strip()
    except (OSError, UnicodeDecodeError):
        pass
    return None


def _parse_agent(path: Path) -> Optional[Dict]:
    """Parse agent definition from markdown with YAML frontmatter."""
    try:
        text = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        if fm is None:
            return None
        return {
            "name": fm.get("name", path.stem),
            "description": fm.get("description", ""),
            "tools": fm.get("tools", ""),
            "model": fm.get("model", ""),
            "template_file": str(path.relative_to(REPO_ROOT)),
        }
    except (OSError, UnicodeDecodeError):
        return None


def _parse_command(path: Path) -> Optional[Dict]:
    """Parse command definition from markdown."""
    title = _parse_command_title(path)
    if title is None:
        return None
    return {
        "name": path.stem,
        "description": title,
        "template_file": str(path.relative_to(REPO_ROOT)),
    }


def _parse_pack(pack_dir: Path) -> Optional[Dict]:
    """Parse pack from pack.yaml."""
    manifest_path = pack_dir / "pack.yaml"
    if not manifest_path.is_file():
        return None
    try:
        manifest = pack_loader._parse_simple_yaml(
            manifest_path.read_text(encoding="utf-8")
        )
    except Exception:
        return None

    name = manifest.get("name", pack_dir.name)
    description = manifest.get("description", "")
    version = manifest.get("version", "")
    components = manifest.get("components", [])
    if isinstance(components, str):
        components = [components]

    return {
        "name": name,
        "description": description,
        "version": version,
        "components": components,
        "template_file": str(manifest_path.relative_to(REPO_ROOT)),
    }


def generate_manifest() -> Dict:
    """Build manifest dict from all canonical sources."""
    commands_dir = REPO_ROOT / ".claude" / "commands"
    agents_dir = REPO_ROOT / ".claude" / "agents"
    packs_dir = REPO_ROOT / "packs"
    pipeline_dir = REPO_ROOT / "agents" / "pipeline"

    commands: List[Dict] = []
    agents: List[Dict] = []
    packs: List[Dict] = []
    pipeline_docs: List[Dict] = []
    schemas: List[Dict] = []

    # Commands
    if commands_dir.is_dir():
        for path in sorted(commands_dir.glob("*.md")):
            if path.name == "README.md":
                continue
            cmd = _parse_command(path)
            if cmd:
                commands.append(cmd)

    # Agents
    if agents_dir.is_dir():
        for path in sorted(agents_dir.glob("*.md")):
            agent = _parse_agent(path)
            if agent:
                agents.append(agent)

    # Packs
    if packs_dir.is_dir():
        for pack_dir in sorted(packs_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            pack = _parse_pack(pack_dir)
            if pack:
                packs.append(pack)

    # Pipeline docs
    if pipeline_dir.is_dir():
        for path in sorted(pipeline_dir.glob("*.md")):
            title = _parse_command_title(path)
            pipeline_docs.append({
                "name": path.stem,
                "description": title or path.stem,
                "template_file": str(path.relative_to(REPO_ROOT)),
            })

    for path in sorted((REPO_ROOT / "templates").glob("*.schema.json")):
        schemas.append({
            "name": path.stem,
            "template_file": str(path.relative_to(REPO_ROOT)),
        })

    manifest = {
        "schema_version": "1.0.0",
        "generated_at": None,  # filled below
        "generated_from": {
            "commands_dir": str(commands_dir.relative_to(REPO_ROOT)),
            "agents_dir": str(agents_dir.relative_to(REPO_ROOT)),
            "packs_dir": str(packs_dir.relative_to(REPO_ROOT)),
            "pipeline_dir": str(pipeline_dir.relative_to(REPO_ROOT)),
        },
        "commands": commands,
        "agents": agents,
        "packs": packs,
        "pipeline_docs": pipeline_docs,
        "schemas": schemas,
        "retrieval": {
            "priority": ["contracts", "patterns", "project_docs", "domain_knowledge"],
            "max_docs": 7,
            "intent_types": ["implement_feature", "fix_bug", "design", "incident", "review"],
        },
        "supported_runtimes": ["claude", "cursor", "codex-plugin", "codex-instructions", "plain"],
    }

    return manifest


def write_manifest(manifest: Dict, output_path: Optional[Path] = None) -> Path:
    """Write manifest to .contextd/manifest.json."""
    if output_path is None:
        output_path = REPO_ROOT / ".contextd" / "manifest.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate contextd manifest index.")
    parser.add_argument("--output", default=None, help="Output path (default: .contextd/manifest.json)")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout without writing")
    args = parser.parse_args()

    manifest = generate_manifest()

    if args.dry_run:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        output = Path(args.output) if args.output else None
        path = write_manifest(manifest, output)
        print(f"Manifest written to: {path}")
        print(f"  Commands: {len(manifest['commands'])}")
        print(f"  Agents:   {len(manifest['agents'])}")
        print(f"  Packs:    {len(manifest['packs'])}")
        print(f"  Pipeline docs: {len(manifest['pipeline_docs'])}")
        print(f"  Schemas:  {len(manifest['schemas'])}")


if __name__ == "__main__":
    main()
