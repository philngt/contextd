#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack-agentic — Layer 1 validator rules. Prefix: pack-agentic-."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List


def _vio(rule, severity, file_path, lineno, snippet, message):
    return {
        "rule": rule, "severity": severity,
        "file": file_path.as_posix(), "line": lineno,
        "snippet": snippet.strip()[:200], "message": message,
    }


def _is_test(file_path: Path) -> bool:
    """Only filename-based test detection — broad path-substring matches are too aggressive."""
    name = file_path.name.lower()
    return (
        name.endswith("_test.py") or
        name.endswith(".test.ts") or name.endswith(".test.tsx") or
        name.endswith(".test.js") or name.endswith(".test.jsx") or
        name.endswith(".spec.ts") or name.endswith(".spec.tsx") or
        name.endswith("test.java")
    )


WHILE_TRUE = re.compile(r"\bwhile\s+(?:True|1|true)\s*[:{\(]")
AGENT_FILE_HINT = re.compile(
    r"\b(agent|tool_use|tool_call|step|reasoning|planner|executor)\b",
    re.IGNORECASE,
)


def rule_loop_no_max_steps(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if _is_test(file_path):
        return []
    text = "\n".join(lines)
    if not AGENT_FILE_HINT.search(text):
        return []
    out = []
    for i, raw in enumerate(lines, start=1):
        if not WHILE_TRUE.search(raw):
            continue
        # Look at next ~50 lines for `break` or step counter check
        body = "\n".join(lines[i:i + 50])
        has_break = bool(re.search(r"\bbreak\b", body))
        has_counter = bool(re.search(
            r"\b(step|iteration|count|i)\s*[+]?[+]?\s*[+=]\s*1|"
            r"\b(step|iteration|count|i)\s*>=?\s*MAX_STEPS|"
            r"\bif\s+\w+\s*>=?\s*\d+\s*:.*\b(break|return|raise)",
            body, re.MULTILINE | re.DOTALL,
        ))
        if has_break and has_counter:
            continue
        out.append(_vio(
            "pack-agentic-loop-no-max-steps", "error", file_path, i, raw,
            "Unbounded `while True:` in agent code — add explicit MAX_STEPS limit "
            "and termination condition to prevent runaway loops."
        ))
    return out


TOOL_DECORATOR = re.compile(r"^\s*@tool\b|^\s*@mcp\.\w+\.tool\b", re.MULTILINE)
TOOL_FUNC_DEF = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
TIMEOUT_HINT = re.compile(
    r"(\btimeout\s*[=:]|\btimeout\s*\(|"
    r"\bwait_for\s*\(|\bwith_timeout\s*\(|\basyncio\.timeout\s*\(|"
    r"\bsignal\.alarm\s*\(|\bsetTimeout\s*\(|\bAbortController\b|"
    r"\bTIMEOUT_(MS|S|SEC)?\b)",
    re.IGNORECASE,
)


def _strip_python_comments(text: str) -> str:
    """Remove `# ...` to end-of-line. Naive (doesn't handle strings)."""
    lines = []
    for ln in text.splitlines():
        idx = ln.find("#")
        # Skip if # is inside a string — heuristic: count quotes before #
        if idx > 0:
            prefix = ln[:idx]
            dq = prefix.count('"') - prefix.count('\\"')
            sq = prefix.count("'") - prefix.count("\\'")
            if dq % 2 == 0 and sq % 2 == 0:
                ln = prefix
        elif idx == 0:
            ln = ""
        lines.append(ln)
    return "\n".join(lines)


def rule_tool_no_timeout(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if _is_test(file_path):
        return []
    text = "\n".join(lines)
    out = []
    # For each @tool decorator, find the next def
    for d in TOOL_DECORATOR.finditer(text):
        # Find the function body following
        rest = text[d.end():]
        fn_match = TOOL_FUNC_DEF.search(rest)
        if not fn_match:
            continue
        # Slice ~60 lines for body inspection
        body_start = d.end() + fn_match.start()
        body = text[body_start:body_start + 4000]
        if TIMEOUT_HINT.search(body):
            continue
        prefix = text[:d.start()]
        lineno = prefix.count("\n") + 1
        snippet = lines[lineno - 1] if lineno - 1 < len(lines) else d.group(0)
        out.append(_vio(
            "pack-agentic-tool-no-timeout", "warn", file_path, lineno, snippet,
            "Tool handler without a timeout — wrap external calls in "
            "asyncio.wait_for / setTimeout / equivalent to bound execution."
        ))
    return out


DESTRUCTIVE_KEYWORDS = re.compile(
    r"(delete|drop|destroy|kill|send|publish|deploy|wipe|purge|terminate)",
    re.IGNORECASE,
)
TOOL_NAME_DECL = re.compile(
    r'(?:name\s*[=:]\s*["\']([\w_\-]+)["\']|'
    r'def\s+(\w+)\s*\([^)]*\)\s*->|'
    r'tool\s*\(\s*["\']([\w_\-]+)["\'])'
)


def rule_destructive_no_confirm(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if _is_test(file_path):
        return []
    text = "\n".join(lines)
    out = []
    # Find tool decorators
    for d in TOOL_DECORATOR.finditer(text):
        rest = text[d.end():]
        # Locate function name
        fn_match = TOOL_FUNC_DEF.search(rest)
        if not fn_match:
            continue
        name = fn_match.group(1)
        if not DESTRUCTIVE_KEYWORDS.search(name):
            continue
        # Inspect function signature + body for `confirm` param
        sig_end = rest.find(")", fn_match.end())
        sig = rest[fn_match.end():sig_end] if sig_end > 0 else ""
        body_start = d.end() + (sig_end if sig_end > 0 else fn_match.end())
        body = text[body_start:body_start + 2000]
        has_confirm_param = bool(re.search(r"\bconfirm\b\s*[:=]", sig, re.IGNORECASE))
        has_approval_call = bool(re.search(
            r"\b(request_approval|require_confirmation|human_in_the_loop|"
            r"prompt_user|await_approval)\b", body, re.IGNORECASE,
        ))
        if has_confirm_param or has_approval_call:
            continue
        prefix = text[:d.start()]
        lineno = prefix.count("\n") + 1
        snippet = lines[lineno - 1] if lineno - 1 < len(lines) else name
        out.append(_vio(
            "pack-agentic-destructive-no-confirm", "error", file_path, lineno, snippet,
            f"Destructive tool '{name}' has no `confirm` parameter and no human-in-the-loop "
            "approval call. Add explicit confirmation before allowing the agent to invoke it."
        ))
    return out


BOUNDED_LOOP = re.compile(r"\bfor\s+\w+\s+in\s+range\s*\(\s*[\w_]*MAX_STEPS")
TRACE_CALL = re.compile(
    r"\b(log|logger|trace|emit_trace|record_step|telemetry|metrics)\b",
    re.IGNORECASE,
)


def rule_no_step_trace(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if _is_test(file_path):
        return []
    text = "\n".join(lines)
    if not AGENT_FILE_HINT.search(text):
        return []
    out = []
    for m in BOUNDED_LOOP.finditer(text):
        # Inspect ~50 lines after for trace call (strip comments to avoid
        # false-negatives where the word "log" only appears in commentary)
        start = m.end()
        body = _strip_python_comments(text[start:start + 3000])
        if TRACE_CALL.search(body):
            continue
        prefix = text[:m.start()]
        lineno = prefix.count("\n") + 1
        snippet = lines[lineno - 1] if lineno - 1 < len(lines) else m.group(0)
        out.append(_vio(
            "pack-agentic-no-step-trace", "warn", file_path, lineno, snippet,
            "Agent loop without per-step trace — add structured logging "
            "(step_n, action, latency, status) for observability."
        ))
    return out


RULES = [
    rule_loop_no_max_steps,
    rule_tool_no_timeout,
    rule_destructive_no_confirm,
    rule_no_step_trace,
]
