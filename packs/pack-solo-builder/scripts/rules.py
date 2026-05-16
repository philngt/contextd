#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack-solo-builder — Layer 1 validator rules. Prefix: pack-solo-builder-.

Applies to markdown spec docs under {ws}/tools/. Checks structural completeness
of tool specs, recipe citation validity, jargon explanation, multi-purpose flag.
"""

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


def _is_tool_spec(file_path: Path) -> bool:
    p = file_path.as_posix().lower()
    return "/tools/" in p and p.endswith("-spec.md")


HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")


def _headings(lines: List[str]) -> List[str]:
    out = []
    for raw in lines:
        m = HEADING_RE.match(raw)
        if m:
            out.append(m.group(1).strip().lower())
    return out


def _has_section(headings: List[str], keywords: List[str]) -> bool:
    for h in headings:
        for kw in keywords:
            if kw in h:
                return True
    return False


def rule_spec_missing_problem(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_tool_spec(file_path):
        return []
    if _has_section(_headings(lines), ["problem", "vấn đề", "van de"]):
        return []
    return [_vio(
        "pack-solo-builder-spec-missing-problem", "error", file_path, 1,
        lines[0] if lines else "",
        "Tool spec missing 'Problem' / 'Vấn đề' section — describe the real-world pain first."
    )]


def rule_spec_missing_system_map(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_tool_spec(file_path):
        return []
    if _has_section(_headings(lines), ["system map", "sơ đồ hệ thống", "so do he thong", "flow"]):
        return []
    return [_vio(
        "pack-solo-builder-spec-missing-system-map", "error", file_path, 1,
        lines[0] if lines else "",
        "Tool spec missing 'System Map' section — Input → Process → Output diagram required."
    )]


def rule_spec_missing_stack(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_tool_spec(file_path):
        return []
    if _has_section(_headings(lines), ["tech stack", "stack", "technology"]):
        return []
    return [_vio(
        "pack-solo-builder-spec-missing-stack", "error", file_path, 1,
        lines[0] if lines else "",
        "Tool spec missing 'Tech Stack' section — declare chosen tech + reasoning."
    )]


def rule_spec_missing_acceptance(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_tool_spec(file_path):
        return []
    if _has_section(_headings(lines), ["acceptance criteria", "acceptance", "done criteria"]):
        return []
    return [_vio(
        "pack-solo-builder-spec-missing-acceptance", "error", file_path, 1,
        lines[0] if lines else "",
        "Tool spec missing 'Acceptance Criteria' — what does 'done' look like?"
    )]


def rule_spec_missing_setup(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_tool_spec(file_path):
        return []
    if _has_section(_headings(lines), ["setup", "cài đặt", "cai dat", "install"]):
        return []
    return [_vio(
        "pack-solo-builder-spec-missing-setup", "warn", file_path, 1,
        lines[0] if lines else "",
        "Tool spec missing 'Setup' section — must include per-OS instructions (Linux + Windows)."
    )]


RECIPE_CITE = re.compile(r"recipe\s*used\s*[:：]\s*\[(?:[^\]]+)\]\(([^)]+)\)", re.IGNORECASE)
RECIPE_FILE = re.compile(r"recipe\s*used\s*[:：]\s*([^\s]+\.md)", re.IGNORECASE)


def rule_recipe_not_in_library(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_tool_spec(file_path):
        return []
    out = []
    # Try to find wiki root by walking up to find 'packs' dir
    wiki_root = None
    for parent in file_path.resolve().parents:
        if (parent / "packs" / "pack-solo-builder" / "recipes").exists():
            wiki_root = parent
            break
    if wiki_root is None:
        return []  # can't validate without wiki root
    recipes_dir = wiki_root / "packs" / "pack-solo-builder" / "recipes"
    for i, raw in enumerate(lines, start=1):
        m = RECIPE_CITE.search(raw) or RECIPE_FILE.search(raw)
        if not m:
            continue
        path_str = m.group(1)
        # extract just the filename if it has path
        recipe_name = Path(path_str).name
        if not (recipes_dir / recipe_name).exists():
            out.append(_vio(
                "pack-solo-builder-recipe-not-in-library", "warn", file_path, i, raw,
                f"Cited recipe '{recipe_name}' not found in pack-solo-builder/recipes/. "
                f"Either add the recipe or pick from existing library."
            ))
    return out


JARGON_TERMS = {
    "venv": "thư mục riêng cho thư viện Python",
    "docker": "container chạy app cô lập với hệ thống",
    "docker-compose": "tool chạy nhiều container cùng lúc bằng 1 file config",
    "cron": "scheduler Linux chạy lệnh định kỳ",
    "sqlite": "database file đơn lẻ, không cần server",
    "argparse": "library Python parse command-line arguments",
    "streamlit": "framework Python build web app nhanh",
    "flask": "framework Python build web app nhỏ",
    "tkinter": "library Python build GUI native đơn giản",
    "pywebview": "library Python wrap web app thành GUI desktop",
    "pandas": "library Python xử lý bảng dữ liệu",
    "openpyxl": "library Python đọc/ghi file Excel",
    "weasyprint": "library Python render HTML thành PDF",
    "reportlab": "library Python tạo PDF từ code",
}
JARGON_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in JARGON_TERMS) + r")\b", re.IGNORECASE)
EXPLAIN_HINT = re.compile(r"\(.{6,}\)|—|–|:.{8,}|=.{8,}|nghĩa là|tức là|tức|là gì")


def rule_jargon_without_explain(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_tool_spec(file_path):
        return []
    out = []
    in_code_fence = False
    for i, raw in enumerate(lines, start=1):
        if raw.lstrip().startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        # Skip table separator and headings
        stripped = raw.strip()
        if stripped.startswith("|") and "---" in stripped:
            continue
        m = JARGON_RE.search(raw)
        if not m:
            continue
        # Look for explanation on same line or next line
        next_line = lines[i] if i < len(lines) else ""
        if EXPLAIN_HINT.search(raw) or EXPLAIN_HINT.search(next_line):
            continue
        # Check if jargon appears in a heading or code block reference (often OK)
        if HEADING_RE.match(raw):
            continue
        term = m.group(1).lower()
        out.append(_vio(
            "pack-solo-builder-jargon-without-explain", "warn", file_path, i, raw,
            f"Jargon '{term}' used without 1-line plain-language explanation. "
            f"Suggest: '{term} ({JARGON_TERMS[term]})'."
        ))
    return out


def rule_multi_purpose_tool(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_tool_spec(file_path):
        return []
    # Look at H1 title + Problem section first paragraph
    title = ""
    for raw in lines:
        m = HEADING_RE.match(raw)
        if m and raw.lstrip().startswith("# "):
            title = m.group(1)
            break
    # Count " and " / " và " in title
    title_low = title.lower()
    and_count = title_low.count(" and ") + title_low.count(" và ") + title_low.count(" + ")
    if and_count >= 2:
        return [_vio(
            "pack-solo-builder-multi-purpose-tool", "warn", file_path, 1, title,
            f"Tool title contains {and_count}+ conjunctions ('and'/'và'/'+') — possibly multi-purpose. "
            f"Rule: 1 tool = 1 purpose. Consider splitting."
        )]
    return []


VAGUE_ACCEPT = re.compile(
    r"\b(hoạt động tốt|hoat dong tot|dễ dùng|de dung|"
    r"works well|easy to use|user[- ]friendly|stable|robust|"
    r"production[- ]ready|enterprise|scalable)\b",
    re.IGNORECASE,
)


def rule_vague_acceptance(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_tool_spec(file_path):
        return []
    out = []
    in_acceptance = False
    for i, raw in enumerate(lines, start=1):
        m = HEADING_RE.match(raw)
        if m:
            heading = m.group(1).lower()
            in_acceptance = "acceptance" in heading
            continue
        if not in_acceptance:
            continue
        m2 = VAGUE_ACCEPT.search(raw)
        if m2:
            out.append(_vio(
                "pack-solo-builder-vague-acceptance", "warn", file_path, i, raw,
                f"Vague acceptance criterion: '{m2.group(0)}'. Use testable form: "
                f"'When {{input}}, output is {{specific result}}'."
            ))
    return out


RULES = [
    rule_spec_missing_problem,
    rule_spec_missing_system_map,
    rule_spec_missing_stack,
    rule_spec_missing_acceptance,
    rule_spec_missing_setup,
    rule_recipe_not_in_library,
    rule_jargon_without_explain,
    rule_multi_purpose_tool,
    rule_vague_acceptance,
]
