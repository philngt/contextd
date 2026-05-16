#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack-ai-app — Layer 1 validator rules. Prefix: pack-ai-app-."""

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


def _strip_line_comment(line: str) -> str:
    # Both // and # comments (cover JS, Java, Python)
    for marker in ("//", "#"):
        if marker == "#" and not _looks_python_or_shell(line):
            continue
        idx = line.find(marker)
        if idx >= 0:
            return line[:idx]
    return line


def _looks_python_or_shell(line: str) -> bool:
    s = line.strip()
    return s.startswith("#") or "  # " in line


def _is_test_file(file_path: Path) -> bool:
    """Only true for files whose name is unambiguously a test (e.g. *_test.py, *.test.ts).

    Test fixtures and example code may live in /test/ but still want validation —
    rules rely on content-level filters (e.g. config keyword) instead of path.
    """
    name = file_path.name.lower()
    return (
        name.endswith("_test.py") or
        name.endswith(".test.ts") or name.endswith(".test.tsx") or
        name.endswith(".test.js") or name.endswith(".test.jsx") or
        name.endswith(".spec.ts") or name.endswith(".spec.tsx") or
        name.endswith(".spec.js") or name.endswith(".spec.jsx") or
        name.endswith("test.java")
    )


MODEL_ID_LITERAL = re.compile(
    r'"((?:claude|gpt|gemini|llama|mistral|deepseek|qwen)[\w\-\.@]*)"',
    re.IGNORECASE,
)


def rule_hardcoded_model_id(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if _is_test_file(file_path):
        return []
    out = []
    for i, raw in enumerate(lines, start=1):
        line = raw
        # Skip config-like lines (assignment to a config object/dict key)
        for m in MODEL_ID_LITERAL.finditer(line):
            mid = m.group(1)
            # Filter false positives — short tokens
            if len(mid) < 7 or "." not in mid and "-" not in mid:
                continue
            # If line has 'config' / 'env' / 'getenv' / 'process.env' / '@Value' near it, skip
            if re.search(r"(config|env\.|getenv|process\.env|@Value|os\.environ)",
                         line, re.IGNORECASE):
                continue
            out.append(_vio(
                "pack-ai-app-hardcoded-model-id", "warn", file_path, i, raw,
                f"Hardcoded model ID '{mid}' — read from config/env so the model "
                "can be upgraded without a code change."
            ))
    return out


# log/print call where the argument expression contains 'prompt' or 'messages'
LOG_PROMPT = re.compile(
    r"\b(log\.\w+|logger\.\w+|console\.log|print|System\.out\.println)\s*\("
    r"[^)]*\b(prompt|system_prompt|systemPrompt|messages|user_prompt|userPrompt)\b",
    re.IGNORECASE,
)


def rule_log_raw_prompt(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if _is_test_file(file_path):
        return []
    out = []
    for i, raw in enumerate(lines, start=1):
        line = raw
        m = LOG_PROMPT.search(line)
        if not m:
            continue
        # Skip if explicitly logging length/hash (safe pattern)
        if re.search(r"\b(len|length|sha\d+|hash|count)\s*\(\s*(prompt|messages)",
                     line, re.IGNORECASE):
            continue
        out.append(_vio(
            "pack-ai-app-log-raw-prompt", "error", file_path, i, raw,
            "Logging raw prompt/messages risks leaking PII. Log metadata "
            "(length, hash, request_id) instead."
        ))
    return out


# messages.create(...) / chat.completions.create(...) without max_tokens
LLM_CALL_OPEN = re.compile(
    r"\b(messages\.create|chat\.completions\.create|completions\.create|"
    r"generate_content)\s*\("
)


def rule_no_max_tokens(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    out = []
    text = "\n".join(lines)
    for m in LLM_CALL_OPEN.finditer(text):
        # Find matching closing paren (naive depth tracking)
        start = m.end()
        depth = 1
        j = start
        while j < len(text) and depth > 0:
            c = text[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            j += 1
            if j - start > 4000:
                break
        body = text[start:j - 1]
        if re.search(r"\bmax_tokens\s*[=:]", body):
            continue
        prefix = text[:m.start()]
        lineno = prefix.count("\n") + 1
        snippet = lines[lineno - 1] if lineno - 1 < len(lines) else m.group(0)
        out.append(_vio(
            "pack-ai-app-no-max-tokens", "warn", file_path, lineno, snippet,
            f"{m.group(1)}(...) without max_tokens — output is unbounded. "
            "Set max_tokens explicitly to control cost."
        ))
    return out


# Long string literal (>800 chars) that looks like a system prompt
# Crude heuristic: triple-quoted strings or backtick template literals
LONG_STRING = re.compile(
    r'(?:"""(.*?)"""|\'\'\'(.*?)\'\'\'|`([^`]{800,})`)',
    re.DOTALL,
)


def rule_missing_prompt_cache(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if _is_test_file(file_path):
        return []
    text = "\n".join(lines)
    # Only flag if file mentions anthropic SDK
    if not re.search(r"\b(anthropic|claude|messages\.create)\b", text, re.IGNORECASE):
        return []
    # Match cache_control as code (followed by `=`, `:`, or `"`) — avoids
    # false-positive on commentary like "# no cache_control here".
    if re.search(r'cache_control\s*[=:"\']', text):
        return []
    out = []
    for m in LONG_STRING.finditer(text):
        body = next((g for g in m.groups() if g), "")
        if len(body) < 800:
            continue
        # Heuristic: prompt-ish content
        if not re.search(r"\b(you are|role|assistant|system|user|task)\b", body,
                         re.IGNORECASE):
            continue
        prefix = text[:m.start()]
        lineno = prefix.count("\n") + 1
        snippet = lines[lineno - 1] if lineno - 1 < len(lines) else "<long string>"
        out.append(_vio(
            "pack-ai-app-missing-prompt-cache", "warn", file_path, lineno, snippet,
            f"Long system prompt ({len(body)} chars) without cache_control. "
            "Anthropic prompt caching can save up to 90% on cached input tokens."
        ))
        break  # one warning per file is enough
    return out


RULES = [
    rule_hardcoded_model_id,
    rule_log_raw_prompt,
    rule_no_max_tokens,
    rule_missing_prompt_cache,
]
