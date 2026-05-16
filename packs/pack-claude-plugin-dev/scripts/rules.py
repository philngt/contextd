#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack-claude-plugin-dev — Layer 1 validator rules. Prefix: pack-claude-plugin-dev-."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional


def _vio(rule, severity, file_path, lineno, snippet, message):
    return {
        "rule": rule, "severity": severity,
        "file": file_path.as_posix(), "line": lineno,
        "snippet": snippet.strip()[:200], "message": message,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> Optional[Dict[str, str]]:
    """Parse a minimal YAML frontmatter block (key: value pairs only).

    Returns dict if frontmatter found, None otherwise.
    Supports single-line scalar values, simple lists `[a, b, c]`, and
    block scalars `key: |` (concatenates following indented lines).
    """
    if not text.startswith("---"):
        return None
    # Find closing ---
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
            # block scalar — collect indented lines
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


def _under_claude_dir(file_path: Path, segment: str) -> bool:
    """True if file is inside `.claude/{segment}/...`."""
    parts = file_path.as_posix().split("/")
    try:
        idx = parts.index(".claude")
        return len(parts) > idx + 1 and parts[idx + 1] == segment
    except ValueError:
        return False


def _is_skill_md(file_path: Path) -> bool:
    if file_path.name != "SKILL.md":
        return False
    parts = file_path.as_posix().split("/")
    try:
        idx = parts.index(".claude")
        return len(parts) > idx + 2 and parts[idx + 1] == "skills"
    except ValueError:
        return False


def _find_plugin_root(file_path: Path) -> Optional[Path]:
    """Walk up from file looking for parent dir that contains .claude/."""
    cur = file_path.parent
    for _ in range(15):
        if (cur / ".claude").is_dir():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent
    return None


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def rule_missing_plugin_manifest(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    """If file is in .claude/{commands|agents|skills}/, check sibling .claude-plugin/plugin.json."""
    in_plugin_dir = any(
        _under_claude_dir(file_path, seg) for seg in ("commands", "agents", "skills")
    ) or _is_skill_md(file_path)
    if not in_plugin_dir:
        return []
    plugin_root = _find_plugin_root(file_path)
    if plugin_root is None:
        return []
    manifest = plugin_root / ".claude-plugin" / "plugin.json"
    if manifest.is_file():
        return []
    return [_vio(
        "pack-claude-plugin-dev-missing-plugin-manifest", "error", file_path, 1,
        lines[0] if lines else "",
        f"Plugin assets found under {plugin_root}/.claude/ but no manifest "
        f"at .claude-plugin/plugin.json. Create one with name/version/description/author."
    )]


def rule_command_missing_description(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _under_claude_dir(file_path, "commands") or file_path.suffix.lower() != ".md":
        return []
    text = "\n".join(lines)
    fm = _parse_frontmatter(text)
    if fm is None:
        return [_vio(
            "pack-claude-plugin-dev-command-missing-description", "error",
            file_path, 1, lines[0] if lines else "",
            "Slash command file missing YAML frontmatter. Add `---`-delimited block "
            "with at least `description: ...`."
        )]
    desc = fm.get("description", "").strip()
    if not desc:
        return [_vio(
            "pack-claude-plugin-dev-command-missing-description", "error",
            file_path, 1, lines[0] if lines else "",
            "Slash command frontmatter missing `description:` field. "
            "Add a single action-verb sentence (< 100 chars) — this is what users see in /help."
        )]
    return []


def rule_agent_missing_tools(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _under_claude_dir(file_path, "agents") or file_path.suffix.lower() != ".md":
        return []
    text = "\n".join(lines)
    fm = _parse_frontmatter(text)
    if fm is None:
        return []  # missing frontmatter caught by other rule path; skip
    if "tools" not in fm or not fm.get("tools", "").strip():
        return [_vio(
            "pack-claude-plugin-dev-agent-missing-tools", "warn",
            file_path, 1, lines[0] if lines else "",
            "Subagent frontmatter missing explicit `tools:` field — subagent will "
            "inherit ALL tools. Restrict to minimum needed (e.g. `tools: Read, Grep, Glob`)."
        )]
    tools_val = fm["tools"].strip()
    if tools_val in ("*", '"*"', "'*'"):
        return [_vio(
            "pack-claude-plugin-dev-agent-missing-tools", "warn",
            file_path, 1, lines[0] if lines else "",
            "Subagent declares `tools: *` (all tools). Explicit allowlist preferred "
            "for least-privilege."
        )]
    return []


TRIGGER_PHRASE = re.compile(
    r"(TRIGGER when|Use when|use this when|trigger when|invoke when|"
    r"Triggers? when)", re.IGNORECASE,
)


def rule_skill_description_too_vague(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_skill_md(file_path):
        return []
    text = "\n".join(lines)
    fm = _parse_frontmatter(text)
    if fm is None:
        return [_vio(
            "pack-claude-plugin-dev-skill-description-too-vague", "warn",
            file_path, 1, lines[0] if lines else "",
            "SKILL.md missing YAML frontmatter. Add `---` block with `name:` and "
            "`description:` (>= 50 chars, include TRIGGER when: phrase for auto-invoke)."
        )]
    desc = fm.get("description", "").strip()
    if len(desc) < 50:
        return [_vio(
            "pack-claude-plugin-dev-skill-description-too-vague", "warn",
            file_path, 1, lines[0] if lines else "",
            f"Skill description too short ({len(desc)} chars). Need >= 50 chars with "
            "explicit trigger condition (e.g. 'TRIGGER when: user asks about X')."
        )]
    if not TRIGGER_PHRASE.search(desc):
        return [_vio(
            "pack-claude-plugin-dev-skill-description-too-vague", "warn",
            file_path, 1, lines[0] if lines else "",
            "Skill description missing trigger phrase ('TRIGGER when:', 'Use when'). "
            "Auto-invocation depends on this — be explicit about when the skill should fire."
        )]
    return []


SECRET_PATTERNS = [
    (re.compile(r'\bsk-(?:proj-|ant-|live-)?[A-Za-z0-9_\-]{20,}\b'), "OpenAI/Anthropic API key"),
    (re.compile(r'\bsk-ant-[A-Za-z0-9_\-]{20,}\b'), "Anthropic API key"),
    (re.compile(r'\bghp_[A-Za-z0-9]{30,}\b'), "GitHub personal access token"),
    (re.compile(r'\bgho_[A-Za-z0-9]{30,}\b'), "GitHub OAuth token"),
    (re.compile(r'\bghs_[A-Za-z0-9]{30,}\b'), "GitHub server token"),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), "AWS access key ID"),
    (re.compile(r'\bAIzaSy[A-Za-z0-9_\-]{30,}\b'), "Google API key"),
    (re.compile(r'\bxox[baprs]-[A-Za-z0-9\-]{20,}\b'), "Slack token"),
    (re.compile(r'\beyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{20,}\b'), "JWT-shaped literal"),
]


def rule_secret_literal(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    out = []
    name = file_path.name.lower()
    # Skip obvious test/doc files where secrets-shaped placeholders are intentional
    if name.endswith(".test.ts") or name.endswith("_test.py") or name == "changelog.md":
        return []
    for i, raw in enumerate(lines, start=1):
        for pat, label in SECRET_PATTERNS:
            m = pat.search(raw)
            if not m:
                continue
            # Skip placeholders like sk-XXXX or sk-... (no real entropy)
            literal = m.group(0)
            if "XXX" in literal or "your-" in literal.lower() or "example" in literal.lower():
                continue
            out.append(_vio(
                "pack-claude-plugin-dev-secret-literal", "error", file_path, i, raw,
                f"Hardcoded secret detected ({label}). Move to environment variable "
                "or secret manager — never commit secrets to a plugin repo."
            ))
            break
    return out


def rule_hook_no_error_handling(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    """Flag hook scripts (.sh / .py under .claude/hooks/) without basic error handling."""
    parts = file_path.as_posix().split("/")
    try:
        idx = parts.index(".claude")
    except ValueError:
        return []
    if len(parts) <= idx + 1 or parts[idx + 1] != "hooks":
        return []
    text = "\n".join(lines)
    ext = file_path.suffix.lower()
    if ext in (".sh", ".bash"):
        # Look for `set -e`, `set -euo`, or `trap` AT START OF LINE (skip
        # mentions inside comments like "# don't forget set -e").
        if re.search(r"^\s*set\s+-[eu]", text, re.MULTILINE) or \
           re.search(r"^\s*trap\s+", text, re.MULTILINE):
            return []
        return [_vio(
            "pack-claude-plugin-dev-hook-no-error-handling", "warn", file_path, 1,
            lines[0] if lines else "",
            "Shell hook without `set -e` or `trap` — a silent failure can crash "
            "the session unexpectedly. Add `set -euo pipefail` at top."
        )]
    if ext == ".py":
        # Require try: or sys.exit at start of line (avoid matches inside comments)
        if re.search(r"^\s*try\s*:", text, re.MULTILINE) or \
           re.search(r"^\s*sys\.exit\s*\(", text, re.MULTILINE):
            return []
        return [_vio(
            "pack-claude-plugin-dev-hook-no-error-handling", "warn", file_path, 1,
            lines[0] if lines else "",
            "Python hook script without try/except or sys.exit() — uncaught exception "
            "will crash the hook. Wrap critical sections + exit 0 on non-critical fail."
        )]
    return []


RULES = [
    rule_missing_plugin_manifest,
    rule_command_missing_description,
    rule_agent_missing_tools,
    rule_skill_description_too_vague,
    rule_secret_literal,
    rule_hook_no_error_handling,
]
