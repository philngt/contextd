#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack-web-api — Layer 1 validator rules. Prefix: pack-web-api-."""

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
    """Strip Java/JS/TS // comment, but preserve URLs (`://`)."""
    idx = 0
    while True:
        idx = line.find("//", idx)
        if idx < 0:
            return line
        if idx > 0 and line[idx - 1] == ":":
            idx += 2
            continue
        return line[:idx]


PRINT_STACK_TRACE = re.compile(r"\bprintStackTrace\s*\(")


def rule_print_stack_trace(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    out = []
    for i, raw in enumerate(lines, start=1):
        line = _strip_line_comment(raw)
        if PRINT_STACK_TRACE.search(line):
            out.append(_vio(
                "pack-web-api-print-stack-trace", "error", file_path, i, raw,
                "printStackTrace() leaks internal info — use a logger with structured "
                "error output instead."
            ))
    return out


REQUEST_BODY_PARAM = re.compile(r"@RequestBody\b")
VALID_ANNOTATION = re.compile(r"@Valid(ated)?\b")


def rule_missing_valid(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    """Spring: @RequestBody parameter without @Valid/@Validated on the same line/param."""
    out = []
    for i, raw in enumerate(lines, start=1):
        line = _strip_line_comment(raw)
        if REQUEST_BODY_PARAM.search(line) and not VALID_ANNOTATION.search(line):
            # also check previous line (annotation can be on its own line)
            prev = _strip_line_comment(lines[i - 2]) if i >= 2 else ""
            if not VALID_ANNOTATION.search(prev):
                out.append(_vio(
                    "pack-web-api-missing-valid", "warn", file_path, i, raw,
                    "@RequestBody without @Valid/@Validated — input is not validated "
                    "at the boundary."
                ))
    return out


URL_LITERAL = re.compile(r'"(https?://[^"\s]+)"')
URL_ALLOWLIST = re.compile(
    r"(localhost|127\.0\.0\.1|0\.0\.0\.0|example\.com|example\.org|"
    r"placeholder|schemas?\.|w3\.org|xmlns)",
    re.IGNORECASE,
)


def rule_hardcoded_base_url(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    """Literal http(s):// URL outside the allowlist (localhost, example.com, ...)."""
    out = []
    for i, raw in enumerate(lines, start=1):
        line = _strip_line_comment(raw)
        for m in URL_LITERAL.finditer(line):
            url = m.group(1)
            if URL_ALLOWLIST.search(url):
                continue
            out.append(_vio(
                "pack-web-api-hardcoded-base-url", "warn", file_path, i, raw,
                f"Hardcoded URL '{url}' — read from config/env."
            ))
    return out


CATCH_BROAD = re.compile(r"\bcatch\s*\(\s*(Exception|Throwable|Error)\s+(\w+)\s*\)")


def rule_broad_exception_catch(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    """catch (Exception e) without re-throwing within ~10 lines."""
    out = []
    n = len(lines)
    for i, raw in enumerate(lines):
        m = CATCH_BROAD.search(raw)
        if not m:
            continue
        body = []
        depth = raw.count("{") - raw.count("}")
        j = i + 1
        while j < n and j < i + 12:
            body.append(lines[j])
            depth += lines[j].count("{") - lines[j].count("}")
            if depth <= 0:
                break
            j += 1
        body_text = "\n".join(body)
        has_rethrow = bool(re.search(r"\bthrow\s+\w", body_text))
        if has_rethrow:
            continue
        out.append(_vio(
            "pack-web-api-broad-exception-catch", "warn", file_path, i + 1, raw,
            "Broad catch (Exception/Throwable) without rethrow — likely swallowing. "
            "Catch specific exceptions or rethrow as a domain-specific error."
        ))
    return out


RULES = [
    rule_print_stack_trace,
    rule_missing_valid,
    rule_hardcoded_base_url,
    rule_broad_exception_catch,
]
