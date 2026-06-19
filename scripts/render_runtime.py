#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime export renderer for contextd.

Takes manifest + workspace knowledge and renders runtime-specific artifacts.
Each runtime is a pure function: receives context dict, returns file content dict.

No external template engine — uses Python f-strings for formatting.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_resolve  # noqa: E402
import cmd_bundle  # noqa: E402

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
    """Load all markdown content from a workspace."""
    ws_dir = wiki_root / "workspaces" / workspace
    if not ws_dir.is_dir():
        return {}

    files: Dict[str, str] = {}
    for pattern in [
        "platform/contracts/*.md",
        "platform/patterns/*.md",
        "projects/**/services/*.md",
        "runbooks/*.md",
        "domains/**/*.md",
        "decisions/**/*.md",
    ]:
        for p in ws_dir.glob(pattern):
            try:
                files[str(p.relative_to(wiki_root))] = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                pass
    return files


def _collect_engine_files(wiki_root: Path) -> Dict[str, str]:
    """Load key engine markdown files."""
    files: Dict[str, str] = {}
    for rel in [
        "agents/system-prompt.md",
        "agents/constraints.md",
        "agents/coding-rules.md",
        "agents/cross-cutting-principles.md",
    ]:
        p = wiki_root / rel
        if p.is_file():
            files[rel] = p.read_text(encoding="utf-8")
    return files


def _collect_pack_files(wiki_root: Path, pack_name: str) -> Dict[str, str]:
    """Load key pack markdown files."""
    pack_dir = wiki_root / "packs" / pack_name
    if not pack_dir.is_dir():
        return {}
    files: Dict[str, str] = {}
    for rel in [
        "agents/constraints.md",
        "agents/coding-rules.md",
        "agents/common-pitfalls.md",
        "README.md",
    ]:
        p = pack_dir / rel
        if p.is_file():
            files[str(p.relative_to(wiki_root))] = p.read_text(encoding="utf-8")
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
        "description": "Scoped context daemon for AI coding agents",
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
        "2. If missing, the project may not be set up yet. Ask the user to run `contextd setup`.",
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
        "# Build deterministic task context",
        'contextd context "kafka consumer retry" --format json',
        "",
        '# Search for a specific topic',
        'contextd find "kafka consumer retry"',
        "",
        "# Bundle all knowledge into a single file",
        "contextd bundle --include-packs --include-engine --output /tmp/contextd-bundle.md",
        "```",
        "",
        "> Codex should run `contextd resolve` first, then `contextd find <topic>` for the",
        "> task at hand, and optionally `contextd bundle` if the user needs comprehensive context.",
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
  short_description: "Scoped context daemon for AI coding agents — workspace knowledge, contracts, and patterns."
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
        "# contextd — Scoped Context Daemon",
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
    """Render Codex .codex/instructions.md — project-level instructions file.

    Codex CLI auto-reads this file from the project directory on every run.
    """
    lines: List[str] = [
        "# contextd Workspace Instructions",
        "",
        f"You are working in workspace **{workspace}**.",
        "",
        "## Knowledge Priority (strict)",
        "1. Contracts (highest priority — MUST follow)",
        "2. Platform Patterns",
        "3. Project Documentation",
        "4. Domain Knowledge",
        "",
        "## Workspace Isolation",
        "- NEVER mix knowledge between workspaces.",
        "- Retrieval is scoped to active workspace ONLY.",
        "",
    ]

    if packs:
        lines.append("## Active Packs")
        for pack_name in packs:
            lines.append(f"- {pack_name}")
        lines.append("")

    lines.append("## Commands Reference")
    for cmd in manifest.get("commands", [])[:15]:  # cap at 15 to avoid bloat
        lines.append(f"- `{cmd['name']}`: {cmd.get('description', '')}")
    lines.append("")

    lines.append("## Agents")
    for agent in manifest.get("agents", []):
        lines.append(f"- `{agent['name']}`: {agent.get('description', '')}")
    lines.append("")

    # Key workspace contracts
    ws_dir = wiki_root / "workspaces" / workspace
    contracts_dir = ws_dir / "platform" / "contracts"
    if contracts_dir.is_dir():
        lines.append("## Key Contracts")
        for p in sorted(contracts_dir.glob("*.md"))[:5]:
            content = p.read_text(encoding="utf-8")[:800]
            lines.append(f"### {p.stem}")
            lines.append(content)
            lines.append("")

    # Key patterns
    patterns_dir = ws_dir / "platform" / "patterns"
    if patterns_dir.is_dir():
        lines.append("## Key Patterns")
        for p in sorted(patterns_dir.glob("*.md"))[:5]:
            content = p.read_text(encoding="utf-8")[:800]
            lines.append(f"### {p.stem}")
            lines.append(content)
            lines.append("")

    # Engine system prompt excerpt
    if include_engine:
        system_prompt = wiki_root / "agents" / "system-prompt.md"
        if system_prompt.is_file():
            lines.append("## System Prompt")
            lines.append(system_prompt.read_text(encoding="utf-8")[:1200])
            lines.append("")

    lines.append("---")
    lines.append("_Generated by contextd for Codex CLI. Do not edit manually — regenerate with `contextd export --runtime codex-instructions`._")

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

    resolved = cmd_resolve.resolve()
    wiki_root_str = resolved.get("knowledge_root") or resolved.get("wiki_root")
    if not wiki_root_str:
        raise RuntimeError("Could not resolve knowledge_root.")

    wiki_root = Path(wiki_root_str).resolve()
    resolved_ws = resolved.get("workspace")
    ws = workspace or resolved_ws

    if not ws:
        raise RuntimeError("No workspace resolved. Specify --workspace.")

    # If workspace is overridden, read packs from that workspace's workspace.md
    if workspace and workspace != resolved_ws:
        ws_md = wiki_root / "workspaces" / workspace / "workspace.md"
        if ws_md.is_file():
            packs, _ = cmd_resolve.get_effective_packs({}, ws_md)
        else:
            packs = []
    else:
        packs = resolved.get("packs") or []

    return renderer(manifest, ws, wiki_root, packs, include_engine)


def main():
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
