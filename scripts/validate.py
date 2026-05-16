#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Layer 1 validator for the wiki-template knowledge engine.

Engine baseline: stack-agnostic rules (domain workflow, hardcoded config,
constructor injection, /wiki-report HTML hygiene). Stack-specific rules
(Kafka/MQTT/REST/frontend/...) live in packs and are loaded dynamically
via `scripts/pack_loader.py` based on the workspace's `## Packs` section.

USAGE
-----
    python validate.py --file <path-to-code-file>
                       [--workspace <name>]
                       [--wiki-root <path>]
                       [--pretty]

EXIT CODE
---------
    0 — no errors (warnings allowed)
    1 — at least one error-severity violation
    2 — bad invocation (missing file, unresolved workspace, etc.)

OUTPUT
------
    JSON to stdout:
    {
      "violations": [
        {"rule": str, "severity": "error"|"warn",
         "file": str, "line": int, "snippet": str, "message": str}
      ],
      "summary": {"errors": N, "warnings": M},
      "context": {..., "active_packs": [...]}
    }

DESIGN NOTES
------------
* Pure regex / line-based scan — NO real parser. False positives are accepted;
  false negatives are minimised. This is a fast pre-flight check, not a compiler.
* Pack rules: workspace opts in via `## Packs` section in workspace.md.
  Each pack contributes `packs/{name}/scripts/rules.py#RULES`.
* Workspace rules: if `{ws}/agents/pipeline/validator-rules.md` exists, the
  script logs that workspace rules were detected. A real loader for `ws-`
  prefixed rules is a TODO (extension point: see `load_workspace_rules`).
* All paths are normalised to POSIX-style in the JSON output for stable diffs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Pack loader — sibling module
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_loader  # noqa: E402


# ---------------------------------------------------------------------------
# Workspace + wiki_root resolution
# ---------------------------------------------------------------------------

def find_wiki_json(start_dir: Path) -> Optional[Path]:
    cur = start_dir.resolve()
    while True:
        candidate = cur / ".claude" / "wiki.json"
        if candidate.is_file():
            return candidate
        if cur.parent == cur:
            return None
        cur = cur.parent


def load_global_wiki_root() -> Optional[str]:
    home = Path(os.path.expanduser("~"))
    p = home / ".claude" / "wiki-global.json"
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("wiki_root")
    except (json.JSONDecodeError, OSError):
        return None


def resolve_wiki_root(wiki_json_path: Path, raw_value) -> Optional[Path]:
    if raw_value:
        p = Path(raw_value)
        if p.is_absolute():
            return p.resolve()
        project_root = wiki_json_path.parent.parent
        return (project_root / p).resolve()
    fallback = load_global_wiki_root()
    if fallback:
        return Path(fallback).expanduser().resolve()
    return None


def resolve_workspace_context(
    file_path: Path,
    cli_workspace: Optional[str],
    cli_wiki_root: Optional[str],
) -> Tuple[Optional[str], Optional[Path], Optional[str]]:
    workspace = cli_workspace
    wiki_root = Path(cli_wiki_root).resolve() if cli_wiki_root else None
    domain: Optional[str] = None

    wiki_json = find_wiki_json(file_path.parent if file_path.is_file()
                               else file_path)
    if wiki_json:
        try:
            cfg = json.loads(wiki_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cfg = {}
        if not workspace:
            workspace = cfg.get("workspace")
        if not wiki_root:
            wiki_root = resolve_wiki_root(wiki_json, cfg.get("wiki_root"))
        domain = cfg.get("domain")
    return workspace, wiki_root, domain


# ---------------------------------------------------------------------------
# Knowledge loaders (best-effort)
# ---------------------------------------------------------------------------

TABLE_ROW_TYPE = re.compile(r"^\|\s*`?([a-zA-Z0-9_\-]+)`?\s*\|")
WORKFLOW_STATE_TOKEN = re.compile(r"`([A-Z][A-Z0-9_]{2,})`")


def load_mqtt_registered_types(ws_root: Path) -> List[str]:
    """Parse the 'Registered Types' table from mqtt-topic-contract.md.

    NOTE: This loader stays in the engine (despite being MQTT-specific) because
    pack rules consume it via ctx['mqtt_types']. It's a no-op for workspaces
    without the contract file.
    """
    p = ws_root / "platform" / "contracts" / "mqtt-topic-contract.md"
    if not p.is_file():
        return []
    text = p.read_text(encoding="utf-8")
    m = re.search(r"##\s*Registered Types\s*\n(.+?)(?:\n##|\Z)",
                  text, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    block = m.group(1)
    types: List[str] = []
    for line in block.splitlines():
        if line.strip().startswith("|") and "Type" not in line and "---" not in line:
            mt = TABLE_ROW_TYPE.match(line.strip())
            if mt:
                types.append(mt.group(1))
    seen = set()
    out = []
    for t in types:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def load_workflow_states(ws_root: Path, domain: Optional[str]) -> List[str]:
    if not domain:
        ddir = ws_root / "domains"
        if ddir.is_dir():
            subs = [p for p in ddir.iterdir() if p.is_dir()]
            if len(subs) == 1:
                domain = subs[0].name
    if not domain:
        return []
    p = ws_root / "domains" / domain / "workflow.md"
    if not p.is_file():
        return []
    text = p.read_text(encoding="utf-8")
    states = WORKFLOW_STATE_TOKEN.findall(text)
    seen = set()
    out = []
    for s in states:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def load_workspace_rules(ws_root: Path) -> List[str]:
    p = ws_root / "agents" / "pipeline" / "validator-rules.md"
    return [str(p)] if p.is_file() else []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_line_comment(line: str) -> str:
    idx = line.find("//")
    if idx >= 0:
        return line[:idx]
    return line


def _vio(rule: str, severity: str, file_path: Path, lineno: int,
         snippet: str, message: str) -> Dict:
    return {
        "rule": rule,
        "severity": severity,
        "file": file_path.as_posix(),
        "line": lineno,
        "snippet": snippet.strip()[:200],
        "message": message,
    }


# ---------------------------------------------------------------------------
# ENGINE rules — stack-agnostic
# ---------------------------------------------------------------------------

STATE_TOKEN_RE = re.compile(r'"([A-Z][A-Z0-9_]{2,})"')
STATE_IGNORE = {
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS",
    "TRUE", "FALSE", "NULL", "OK", "ERROR", "WARN", "INFO", "DEBUG",
    "UTF_8", "UTF8", "ISO_8859_1", "US_ASCII",
    "SUCCESS", "FAILURE",
}


def rule_domain_no_new_states(file_path: Path, lines: List[str],
                              ctx: Dict) -> List[Dict]:
    states = ctx.get("workflow_states") or []
    if not states:
        return []
    state_set = set(states)
    out = []
    for i, raw in enumerate(lines, start=1):
        for m in STATE_TOKEN_RE.finditer(raw):
            tok = m.group(1)
            if tok in STATE_IGNORE or tok in state_set:
                continue
            looks_state = ("_" in tok) or tok.endswith(
                ("ED", "ING", "AL", "ANT", "OUS"))
            if not looks_state:
                continue
            out.append(_vio(
                "domain-unknown-state", "error", file_path, i, raw,
                f"State literal '{tok}' is not in workflow.md "
                f"(allowed: {', '.join(states)})."
            ))
    return out


HARDCODED_CONFIG = re.compile(
    r"\b(batch[_]?[Ss]ize|timeout(?:Ms)?|concurrency|maxPoll(?:Records)?|"
    r"poll[_]?[Tt]imeout|retr(?:y|ies)|backoff(?:Ms)?)\s*=\s*(\d+)\b"
)


def rule_no_hardcoded_config(file_path: Path, lines: List[str],
                             ctx: Dict) -> List[Dict]:
    out = []
    for i, raw in enumerate(lines, start=1):
        line = _strip_line_comment(raw)
        for m in HARDCODED_CONFIG.finditer(line):
            name, value = m.group(1), m.group(2)
            out.append(_vio(
                "no-hardcoded-config", "warn", file_path, i, raw,
                f"Hardcoded value '{value}' assigned to '{name}'. "
                "Read from configuration."
            ))
    return out


def rule_constructor_injection(file_path: Path, lines: List[str],
                               ctx: Dict) -> List[Dict]:
    out = []
    n = len(lines)
    for i, raw in enumerate(lines):
        if "@Autowired" not in raw:
            continue
        j = i + 1
        while j < n and not lines[j].strip():
            j += 1
        if j >= n:
            continue
        nxt = lines[j].strip()
        is_method_or_ctor = "(" in nxt
        if not is_method_or_ctor and nxt.endswith(";"):
            out.append(_vio(
                "constructor-injection", "error", file_path, i + 1, raw,
                "@Autowired on a field — use constructor injection instead."
            ))
    return out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

ENGINE_RULES = [
    rule_domain_no_new_states,
    rule_no_hardcoded_config,
    rule_constructor_injection,
]

LINTABLE_EXT = {".java", ".kt", ".kts", ".scala", ".groovy",
                ".js", ".ts", ".jsx", ".tsx",
                ".py", ".go", ".rb", ".cs",
                # Plugin-dev assets (frontmatter validation, hook scripts):
                ".md", ".sh", ".bash"}


def run(file_path: Path, ws_root: Optional[Path], domain: Optional[str],
        ws_name: Optional[str]) -> Tuple[List[Dict], Dict]:
    violations: List[Dict] = []

    if file_path.suffix.lower() not in LINTABLE_EXT:
        return violations, {
            "skipped": True,
            "reason": f"unsupported extension '{file_path.suffix}'",
            "workspace": ws_name,
            "active_packs": [],
        }

    text = file_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    ctx: Dict = {
        "workspace": ws_name,
        "domain": domain,
        "mqtt_types": [],
        "workflow_states": [],
        "workspace_rules_file": [],
        "active_packs": [],
    }

    # Resolve packs for the active workspace
    pack_rules = []
    active_pack_names: List[str] = []
    if ws_root and ws_root.is_dir() and ws_name:
        ws_dir = ws_root / "workspaces" / ws_name
        if ws_dir.is_dir():
            ctx["mqtt_types"] = load_mqtt_registered_types(ws_dir)
            ctx["workflow_states"] = load_workflow_states(ws_dir, domain)
            ctx["workspace_rules_file"] = load_workspace_rules(ws_dir)
        try:
            packs = pack_loader.load_packs_for_workspace(ws_root, ws_name)
        except RuntimeError as e:
            return [_vio("pack-conflict", "error", file_path, 0, "", str(e))], ctx
        active_pack_names = [p.name for p in packs]
        ctx["active_packs"] = active_pack_names
        pack_rules = pack_loader.load_pack_validator_rules(packs)

    all_rules = ENGINE_RULES + pack_rules

    for rule_fn in all_rules:
        try:
            violations.extend(rule_fn(file_path, lines, ctx))
        except Exception as e:
            violations.append(_vio(
                f"internal-{rule_fn.__name__}", "warn", file_path, 0, "",
                f"Rule crashed: {e!r}"
            ))

    return violations, ctx


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="validate.py",
        description="Layer 1 rule-based validator — see "
                    "agents/pipeline/validator-rules.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--file", required=True)
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--wiki-root", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    file_path = Path(args.file).resolve()
    if not file_path.exists():
        print(json.dumps({
            "violations": [],
            "summary": {"errors": 1, "warnings": 0},
            "error": f"file not found: {file_path}",
        }), file=sys.stdout)
        return 2

    ws_name, wiki_root, domain = resolve_workspace_context(
        file_path, args.workspace, args.wiki_root
    )

    violations, ctx = run(file_path, wiki_root, domain, ws_name)

    errors = sum(1 for v in violations if v["severity"] == "error")
    warnings = sum(1 for v in violations if v["severity"] == "warn")

    out = {
        "violations": violations,
        "summary": {"errors": errors, "warnings": warnings},
        "context": {
            "workspace": ws_name,
            "wiki_root": wiki_root.as_posix() if wiki_root else None,
            "domain": domain,
            "active_packs": ctx.get("active_packs", []),
            "mqtt_registered_types": ctx.get("mqtt_types", []),
            "workflow_states": ctx.get("workflow_states", []),
            "workspace_rules_file": ctx.get("workspace_rules_file", []),
            "skipped": ctx.get("skipped", False),
        },
    }
    if args.pretty:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(out, ensure_ascii=False))

    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
