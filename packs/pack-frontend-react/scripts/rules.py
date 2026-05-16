#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack-frontend-react — Layer 1 validator rules. Prefix: pack-frontend-react-."""

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


_REACT_EXT = {".jsx", ".tsx"}


def _is_react_file(file_path: Path) -> bool:
    if file_path.suffix.lower() in _REACT_EXT:
        return True
    # .ts/.js may also have JSX if pragma — naive: skip them
    return False


# <img ...> without alt= attribute. Multi-line tolerant via simple state machine.
IMG_OPEN = re.compile(r"<img\b", re.IGNORECASE)


def rule_img_no_alt(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_react_file(file_path):
        return []
    out = []
    text = "\n".join(lines)
    # find each <img...> ... > and check for alt= within the tag bounds
    for m in re.finditer(r"<img\b([^>]*)/?>", text, re.IGNORECASE | re.DOTALL):
        body = m.group(1)
        if re.search(r"\balt\s*=", body):
            continue
        # spread props {...x} → can't tell, skip (don't false-positive)
        if re.search(r"\{\s*\.\.\.", body):
            continue
        # locate line number
        prefix = text[:m.start()]
        lineno = prefix.count("\n") + 1
        snippet = lines[lineno - 1] if lineno - 1 < len(lines) else m.group(0)
        out.append(_vio(
            "pack-frontend-react-img-no-alt", "error", file_path, lineno, snippet,
            "<img> without alt attribute — add alt=\"\" for decorative images "
            "or descriptive text for content images."
        ))
    return out


# .map(... => <ElementWithoutKey ...>)
MAP_RETURN_JSX = re.compile(
    r"\.map\s*\(\s*(?:\([^)]*\)|[\w$]+)\s*=>\s*\(?\s*(<\w+\b[^>]*>)",
    re.DOTALL,
)


def rule_list_no_key(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_react_file(file_path):
        return []
    out = []
    text = "\n".join(lines)
    for m in MAP_RETURN_JSX.finditer(text):
        tag = m.group(1)
        if re.search(r"\bkey\s*=", tag):
            continue
        if re.search(r"\{\s*\.\.\.", tag):
            continue
        # Skip Fragment shorthand <>
        if tag.startswith("<>") or tag.startswith("<React.Fragment"):
            continue
        prefix = text[:m.start(1)]
        lineno = prefix.count("\n") + 1
        snippet = lines[lineno - 1] if lineno - 1 < len(lines) else tag
        out.append(_vio(
            "pack-frontend-react-list-no-key", "warn", file_path, lineno, snippet,
            "List item rendered via .map() without `key=` prop. "
            "Add a stable key (item.id), avoid array index unless list is immutable."
        ))
    return out


# After useState declaration, find direct mutations on the same variable.
USESTATE_DECL = re.compile(
    r"\bconst\s+\[\s*(\w+)\s*,\s*(set\w+)\s*\]\s*=\s*useState\b"
)


def rule_direct_state_mutation(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_react_file(file_path):
        return []
    out = []
    text = "\n".join(lines)
    decls = list(USESTATE_DECL.finditer(text))
    if not decls:
        return []
    for d in decls:
        var = d.group(1)
        # search subsequent text for direct mutation
        scan_start = d.end()
        scan_text = text[scan_start:]
        # Patterns: var.foo = ..., var.push(...), var[0] = ..., var.splice(
        mutation_re = re.compile(
            rf"\b{re.escape(var)}\b\s*"
            rf"(?:\.\s*\w+\s*=(?!=)|"
            rf"\.\s*(?:push|pop|shift|unshift|splice|sort|reverse|fill)\s*\(|"
            rf"\[[^\]]+\]\s*=(?!=))"
        )
        for m in mutation_re.finditer(scan_text):
            absolute_pos = scan_start + m.start()
            prefix = text[:absolute_pos]
            lineno = prefix.count("\n") + 1
            snippet = lines[lineno - 1] if lineno - 1 < len(lines) else m.group(0)
            out.append(_vio(
                "pack-frontend-react-direct-state-mutation", "error",
                file_path, lineno, snippet,
                f"Direct mutation of useState variable '{var}'. "
                f"Use the setter ({d.group(2)}) — React won't re-render on direct mutation."
            ))
    return out


USEEFFECT_OPEN = re.compile(r"\buseEffect\s*\(\s*\(\s*\)\s*=>\s*\{")
SUBSCRIBE_HINT = re.compile(
    r"\b(addEventListener|setInterval|setTimeout|subscribe|"
    r"\.on\s*\(|observe\s*\()", re.IGNORECASE
)


def rule_effect_no_cleanup(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_react_file(file_path):
        return []
    out = []
    text = "\n".join(lines)
    for m in USEEFFECT_OPEN.finditer(text):
        start = m.end()
        # Find matching closing brace of the effect callback
        depth = 1
        j = start
        while j < len(text) and depth > 0:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        body = text[start:j - 1]
        if not SUBSCRIBE_HINT.search(body):
            continue
        # Check for cleanup return
        has_cleanup = bool(re.search(r"return\s*\(?\s*\(\s*\)\s*=>", body)) or \
                      bool(re.search(r"return\s+\w+;?\s*\}", body))  # named cleanup
        if has_cleanup:
            continue
        prefix = text[:m.start()]
        lineno = prefix.count("\n") + 1
        snippet = lines[lineno - 1] if lineno - 1 < len(lines) else m.group(0)
        out.append(_vio(
            "pack-frontend-react-effect-no-cleanup", "warn", file_path, lineno, snippet,
            "useEffect with subscription/listener/timer but no cleanup return. "
            "Return a cleanup function: `return () => removeEventListener(...)`."
        ))
    return out


RULES = [
    rule_img_no_alt,
    rule_list_no_key,
    rule_direct_state_mutation,
    rule_effect_no_cleanup,
]
