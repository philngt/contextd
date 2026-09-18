#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime export renderer for contextd.

Bootstrap adapters describe how to consume the canonical compiler artifacts.
The explicit plain-workspace bundle reads source prose through shared safety
helpers; it is not a task-context selection or a pure in-memory renderer.

No external template engine — uses Python f-strings for formatting.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import cmd_resolve  # noqa: E402
import pack_loader  # noqa: E402
from lib import contextd_resolver  # noqa: E402
from lib.context_security import read_safe_text, reject_unsafe_entry  # noqa: E402
from lib.stdio import configure_stdio  # noqa: E402

REPO_ROOT = SCRIPT_DIR.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_manifest() -> Optional[Dict]:
    # PyInstaller onefile bundle: resources extracted to sys._MEIPASS
    if getattr(sys, '_MEIPASS', None):
        p = Path(sys._MEIPASS) / ".contextd" / "manifest.json"
    else:
        p = REPO_ROOT / ".contextd" / "manifest.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _collect_workspace_files(wiki_root: Path, workspace: str) -> Dict[str, str]:
    """Bundle the workspace inventory without bypassing workspace isolation."""
    wiki_root = wiki_root.resolve()
    ws_dir = contextd_resolver.resolve_workspace_dir(wiki_root, workspace)
    if ws_dir is None or not ws_dir.is_dir():
        raise ValueError(f"Invalid or missing workspace: {workspace!r}")
    paths = set()
    for pattern in (
        "platform/contracts/*.md", "platform/patterns/*.md",
        "projects/**/services/*.md", "runbooks/*.md",
        "domains/**/*.md", "decisions/**/*.md",
    ):
        paths.update(ws_dir.glob(pattern))
    files = {}
    for path in sorted(paths):
        content = read_safe_text(path, ws_dir)
        if content is not None:
            files[path.relative_to(wiki_root).as_posix()] = content
    return files


def _collect_engine_files(wiki_root: Path) -> Dict[str, str]:
    """Load engine prose through the same safety boundary as other exports."""
    files = {}
    if (wiki_root / "agents").is_symlink():
        return files
    for rel in (
        "agents/system-prompt.md", "agents/constraints.md",
        "agents/coding-rules.md", "agents/cross-cutting-principles.md",
    ):
        content = read_safe_text(wiki_root / rel, wiki_root / "agents")
        if content is not None:
            files[rel] = content
    return files


def _collect_pack_files(wiki_root: Path, pack_name: str) -> Dict[str, str]:
    """Bundle canonical v3 knowledge, or legacy v2 prose, never both."""
    if (not pack_name or pack_name in {".", ".."}
            or "/" in pack_name or "\\" in pack_name):
        return {}
    pack_dir = wiki_root / "packs" / pack_name
    if (wiki_root / "packs").is_symlink() or pack_dir.is_symlink() or not pack_dir.is_dir():
        return {}
    manifest = pack_loader.load_manifest(pack_dir / "pack.yaml")
    if not manifest:
        return {}
    try:
        version = int(manifest.get("manifest_version", 1))
    except (TypeError, ValueError):
        return {}
    if version >= 3:
        metadata = manifest.get("files") or {}
        knowledge = metadata.get("knowledge") if isinstance(metadata, dict) else None
        if not isinstance(knowledge, str) or reject_unsafe_entry(knowledge):
            return {}
        paths = ["pack.yaml", knowledge]
    else:
        paths = ["agents/constraints.md", "agents/coding-rules.md",
                 "agents/common-pitfalls.md", "README.md"]
    files = {}
    for rel in paths:
        path = pack_dir / rel
        content = read_safe_text(path, pack_dir)
        if content is not None:
            files[path.relative_to(wiki_root).as_posix()] = content
    return files


# ---------------------------------------------------------------------------
# Runtime renderers
# ---------------------------------------------------------------------------

def render_plain(manifest: Dict, workspace: str, wiki_root: Path,
                 packs: List[str], include_engine: bool) -> Dict[str, str]:
    """Render plain markdown bundle — runtime-oriented (includes manifest content)."""
    lines: List[str] = []
    lines.append(f"# contextd Knowledge Bundle")
    lines.append(f"Workspace: {workspace}")
    lines.append(f"Generated: runtime=plain")
    lines.append("")

    # Manifest summary
    lines.append("## Commands")
    for cmd in manifest.get("commands", []):
        lines.append(f"- **{cmd['name']}**: {cmd.get('description', '')}")
    lines.append("")

    lines.append("## Agents")
    for agent in manifest.get("agents", []):
        lines.append(f"- **{agent['name']}**: {agent.get('description', '')}")
    lines.append("")

    lines.append("## Packs")
    for pack in manifest.get("packs", []):
        lines.append(f"- **{pack['name']}** ({pack.get('version', '?')}): {pack.get('description', '')}")
    lines.append("")

    # Workspace knowledge
    ws_files = _collect_workspace_files(wiki_root, workspace)
    if ws_files:
        lines.append("---")
        lines.append("# Workspace Knowledge")
        lines.append("")
        for path, content in sorted(ws_files.items()):
            lines.append(f"## Source: {path}")
            lines.append(content)
            lines.append("")

    # Packs
    for pack_name in packs:
        pack_files = _collect_pack_files(wiki_root, pack_name)
        if pack_files:
            lines.append("---")
            lines.append(f"# Pack: {pack_name}")
            lines.append("")
            for path, content in sorted(pack_files.items()):
                lines.append(f"## Source: {path}")
                lines.append(content)
                lines.append("")

    # Engine
    if include_engine:
        engine_files = _collect_engine_files(wiki_root)
        if engine_files:
            lines.append("---")
            lines.append("# Engine")
            lines.append("")
            for path, content in sorted(engine_files.items()):
                lines.append(f"## Source: {path}")
                lines.append(content)
                lines.append("")

    return {"contextd-bundle.md": "\n".join(lines)}


def render_codex_plugin(manifest: Dict, workspace: str, wiki_root: Path,
                        packs: List[str], include_engine: bool = False) -> Dict[str, str]:
    """Render Codex plugin artifacts:
      - .codex-plugin/plugin.json
      - skills/contextd/SKILL.md
      - skills/contextd/agents/openai.yaml
    """
    # Plugin manifest
    plugin_json = {
        "name": "contextd",
        "version": manifest.get("schema_version", "1.0.0"),
        "description": "Build system for AI coding-agent context",
        "skills": [
            {
                "name": "contextd",
                "description": "Use contextd workspace knowledge for consistent, contract/context-driven work.",
                "commands": [
                    {"name": cmd["name"], "description": cmd.get("description", "")}
                    for cmd in manifest.get("commands", [])
                ],
            }
        ],
    }

    # Skill markdown — instructional skill for Codex
    skill_lines: List[str] = [
        "---",
        "name: contextd",
        "description: |",
        "  Use contextd workspace knowledge for consistent, contract/context-driven work.",
        "  TRIGGER when: user asks about project patterns, contracts, requirements, runbooks, workspace rules,",
        '  or requests "use contextd" / "follow wiki" / "the rules say...".',
        "---",
        "",
        "# contextd Skill",
        "",
        "## When to use",
        "- Before a coding, product, design, QA, security, ops, or domain-research task",
        '- When user mentions "pattern", "contract", "requirement", "runbook", "workspace rule", "follow the wiki"',
        '- When user says "use contextd" or references `.contextd/config.json`',
        "",
        "## How to resolve workspace",
        "",
        '1. Look for `.contextd/config.json` in the current working directory or walk up the tree.',
        "2. If missing, the project may not be set up yet. Ask the user to run `contextd init`.",
        '3. If found, read `workspace` and `knowledge_root` fields.',
        '4. Legacy `.claude/wiki.json` and `.Codex/wiki.json` remain supported adapters.',
        "",
        "## How to find relevant docs",
        "",
        "Run CLI commands (user must have `contextd` installed):",
        "",
        "```bash",
        "# Discover workspace context",
        "contextd resolve",
        "",
        "# Diagnose config, pack, adapter, and safety drift",
        "contextd doctor",
        "",
        "# Build deterministic task context",
        'contextd context "kafka consumer retry" --format json',
        "",
        "# Explain why contextd selected or dropped docs",
        'contextd explain "kafka consumer retry" --format json',
        "",
        '# Search for a specific topic',
        'contextd find "kafka consumer retry"',
        "",
        "# Bundle all knowledge into a single file",
        "contextd bundle --include-packs --include-engine --output /tmp/contextd-bundle.md",
        "```",
        "",
        "> Codex should run `contextd resolve` first, use `contextd context <task>` as",
        "> the canonical artifact, and use `contextd explain <task>` when selection looks wrong.",
        "> `contextd find <topic>` is advisory discovery only.",
        "",
        "## Knowledge priority (strict)",
        "1. Contracts / requirements / runbooks relevant to the task",
        "2. Platform patterns and active-pack working rules",
        "3. Project, product, design, quality, or evidence docs",
        "4. Domain knowledge",
        "",
        "## Workspace isolation",
        "- NEVER mix knowledge between workspaces.",
        "- Only read files under `workspaces/{workspace}/`.",
        "- Treat `contextd find` as advisory; deterministic task context and contracts win.",
        "",
        "## Agents reference",
        "The following subagents exist in Claude Code; Codex can emulate them by reading",
        "the referenced docs directly:",
        "- `contextd-planner`: reads `agents/pipeline/task-to-docs-map.md`",
        "- `contextd-context-selector`: reads `agents/pipeline/context-filter.md`",
        "- `contextd-reviewer`: reads `agents/pipeline/validator-rules.md`",
        "",
    ]

    yaml_content = """---
interface:
  display_name: "contextd"
  short_description: "Build system for AI coding-agent context."
  default_prompt: "Resolve the active workspace and find relevant patterns for this task."
---
"""

    return {
        ".codex-plugin/plugin.json": json.dumps(plugin_json, indent=2, ensure_ascii=False),
        "skills/contextd/SKILL.md": "\n".join(skill_lines),
        "skills/contextd/agents/openai.yaml": yaml_content,
    }


def render_cursor(manifest: Dict, workspace: str, wiki_root: Path,
                  packs: List[str], include_engine: bool = False) -> Dict[str, str]:
    """Render Cursor IDE artifacts:
      - .cursorrules
      - .cursor/context.md
    """
    # .cursorrules
    rules_lines: List[str] = [
        "# contextd — Build System for AI Coding-Agent Context",
        "",
        f"Workspace: {workspace}",
        f"Packs: {', '.join(packs) if packs else '(none)'}",
        "",
        "## Priority Order (strict)",
        "1. Contracts (highest)",
        "2. Platform Patterns",
        "3. Project Documentation",
        "4. Domain Knowledge",
        "",
        "## Commands",
    ]
    for cmd in manifest.get("commands", []):
        rules_lines.append(f"- {cmd['name']}: {cmd.get('description', '')}")
    rules_lines.append("")

    rules_lines.append("## Agents")
    for agent in manifest.get("agents", []):
        rules_lines.append(f"- {agent['name']}: {agent.get('description', '')}")
    rules_lines.append("")

    rules_lines.append("## Workspace Isolation")
    rules_lines.append("- NEVER mix knowledge between workspaces.")
    rules_lines.append("- Retrieval scoped to active workspace ONLY.")
    rules_lines.append("")

    if packs:
        rules_lines.append("## Active Packs")
        for pack_name in packs:
            rules_lines.append(f"- {pack_name}")
        rules_lines.append("")

    # .cursor/context.md
    ctx_lines: List[str] = [
        "# contextd Context",
        "",
        f"This file provides additional context for workspace **{workspace}**.",
        "",
        "## Retrieval Rules",
    ]
    priority = manifest.get("retrieval", {}).get("priority", [])
    for p in priority:
        ctx_lines.append(f"- {p}")
    ctx_lines.append("")

    ctx_lines.append("## Intent Types")
    intent_types = manifest.get("retrieval", {}).get("intent_types", [])
    ctx_lines.append(", ".join(intent_types))
    ctx_lines.append("")

    return {
        ".cursorrules": "\n".join(rules_lines),
        ".cursor/context.md": "\n".join(ctx_lines),
    }


def render_codex_instructions(manifest: Dict, workspace: str, wiki_root: Path,
                                packs: List[str], include_engine: bool = False) -> Dict[str, str]:
    """Render the legacy instructions export as a compiler bootstrap only.

    This compatibility path is not a guarantee that a client auto-loads it.
    It deliberately contains no independently selected source excerpts.
    """
    lines = [
        "# contextd Workspace Instructions", "",
        f"Workspace: {workspace}",
        f"Active packs: {', '.join(packs) if packs else '(none)'}", "",
        "## Build task context", "",
        "Use `contextd resolve` to confirm the active workspace.",
        'Run `contextd context "<task>"` to build the canonical task artifact.',
        "Read the artifact and its contextPack.compiledRef for compiled guidance.",
        'Use `contextd explain "<task>" --text` to inspect selection and gaps.',
        "Treat `contextd find` as advisory discovery, not authority over the artifact.", "",
        "## Boundaries", "",
        "Do not mix workspaces or invent missing contracts.",
        "Report missing knowledge and respect required constraints and verification.",
        "This adapter does not select, truncate, or embed workspace/pack source files.", "",
        "---",
        "Generated by contextd export --runtime codex-instructions. Do not edit manually.",
    ]
    return {".codex/instructions.md": "\n".join(lines)}


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

RUNTIME_RENDERERS = {
    "plain": render_plain,
    "codex-plugin": render_codex_plugin,
    "codex-instructions": render_codex_instructions,
    "cursor": render_cursor,
    "claude": None,  # TODO Phase 3.4 — requires copying canonical files
}


def render(runtime: str, workspace: Optional[str] = None,
           include_engine: bool = True) -> Dict[str, str]:
    """Render artifacts for a given runtime.

    Returns dict: {output_path: content}.
    """
    renderer = RUNTIME_RENDERERS.get(runtime)
    if renderer is None:
        raise ValueError(f"Unknown runtime: {runtime}. Supported: {list(RUNTIME_RENDERERS.keys())}")

    manifest = _load_manifest()
    if manifest is None:
        raise RuntimeError("Manifest not found. Run `python scripts/generate_manifest.py` first.")

    state = contextd_resolver.resolve_request(workspace=workspace)
    return renderer(manifest, state.workspace, state.knowledge_root,
                    state.packs, include_engine)



def main():
    configure_stdio()
    import argparse
    parser = argparse.ArgumentParser(description="Export contextd knowledge to runtime-specific formats.")
    parser.add_argument("--runtime", required=True,
                        choices=["plain", "codex-plugin", "codex-instructions", "cursor"],
                        help="Target runtime format")
    parser.add_argument("--workspace", default=None, help="Workspace name (default: resolved)")
    parser.add_argument("--output", default=None,
                        help="Output directory (default: stdout for single-file, ./ for multi-file)")
    parser.add_argument("--include-engine", action="store_true",
                        help="Include engine docs (for plain runtime)")
    args = parser.parse_args()

    try:
        artifacts = render(
            runtime=args.runtime,
            workspace=args.workspace,
            include_engine=args.include_engine,
        )
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output) if args.output else Path(".")
    output_dir.mkdir(parents=True, exist_ok=True)

    for rel_path, content in artifacts.items():
        out_path = output_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
