#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack-ui-ux — Layer 1 validator rules. Prefix: pack-ui-ux-."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List


def _vio(rule, severity, file_path, lineno, snippet, message):
    return {
        "rule": rule,
        "severity": severity,
        "file": file_path.as_posix(),
        "line": lineno,
        "snippet": snippet.strip()[:200],
        "message": message,
    }


def _posix(file_path: Path) -> str:
    return file_path.as_posix().lower()


def _is_design_doc(file_path: Path) -> bool:
    path = _posix(file_path)
    return path.endswith(".md") and (
        "/platform/design/" in path
        or "/design/" in path
        or "/domains/" in path and "/flows/" in path
    )


def _is_design_system(file_path: Path) -> bool:
    return _posix(file_path).endswith("/platform/design/design-system.md")


def _is_flow_doc(file_path: Path) -> bool:
    path = _posix(file_path)
    return path.endswith(".md") and "/domains/" in path and "/flows/" in path


COLOR_LITERAL = re.compile(r"(#[0-9a-fA-F]{3,6}\b|\brgba?\s*\(|\bhsla?\s*\()")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
RATIO = re.compile(r"\b\d+(?:\.\d+)?:1\b")
COLOR_TOKEN_HINT = re.compile(
    r"\b(color[-_.][a-z0-9_-]+|[a-z0-9_-]+[-_.]color|color\s+token|token\s+color)\b",
    re.IGNORECASE,
)


def rule_hardcoded_color(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_design_doc(file_path) or file_path.name.lower() == "tokens.md":
        return []
    out = []
    in_fence = False
    for i, raw in enumerate(lines, start=1):
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if COLOR_LITERAL.search(raw):
            out.append(_vio(
                "pack-ui-ux-hardcoded-color",
                "error",
                file_path,
                i,
                raw,
                "Design docs must use token names instead of hardcoded color literals outside tokens.md.",
            ))
    return out


def rule_missing_a11y_note(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_design_system(file_path):
        return []
    if any(line.lstrip().startswith(">") and "A11y:" in line for line in lines):
        return []
    return [_vio(
        "pack-ui-ux-missing-a11y-note",
        "warn",
        file_path,
        1,
        lines[0] if lines else "",
        "Design system docs should include a blockquote `> A11y:` note for keyboard/ARIA guidance.",
    )]


def rule_flow_no_error_path(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_flow_doc(file_path):
        return []
    headings = []
    for raw in lines:
        match = HEADING.match(raw)
        if match:
            headings.append(match.group(1).lower())
    if any("error" in h or "edge" in h for h in headings):
        return []
    return [_vio(
        "pack-ui-ux-flow-no-error-path",
        "warn",
        file_path,
        1,
        lines[0] if lines else "",
        "User flow docs should include Error or Edge path coverage.",
    )]


def rule_contrast_unchecked(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_design_doc(file_path) or file_path.name.lower() == "tokens.md":
        return []
    text = "\n".join(lines)
    if not COLOR_TOKEN_HINT.search(text):
        return []
    if re.search(r"contrast", text, re.IGNORECASE) or RATIO.search(text):
        return []
    return [_vio(
        "pack-ui-ux-contrast-unchecked",
        "warn",
        file_path,
        1,
        lines[0] if lines else "",
        "Docs mention color tokens but do not record contrast validation or a contrast ratio.",
    )]


RULES = [
    rule_hardcoded_color,
    rule_missing_a11y_note,
    rule_flow_no_error_path,
    rule_contrast_unchecked,
]
