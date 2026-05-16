#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack-product — Layer 1 validator rules. Prefix: pack-product-.

Applies to markdown docs under {ws}/product/. Checks structural completeness
of briefs/OKRs and flags jargon leaks / vague dates / impl prescriptions.
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


def _is_brief(file_path: Path) -> bool:
    parts = file_path.as_posix().lower()
    return "/product/briefs/" in parts and parts.endswith(".md")


def _is_okr(file_path: Path) -> bool:
    parts = file_path.as_posix().lower()
    return "/product/okrs/" in parts and parts.endswith(".md")


def _is_roadmap(file_path: Path) -> bool:
    parts = file_path.as_posix().lower()
    return parts.endswith("/product/roadmap.md")


def _is_product_doc(file_path: Path) -> bool:
    return "/product/" in file_path.as_posix().lower() and file_path.as_posix().endswith(".md")


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


def rule_brief_missing_metric(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_brief(file_path):
        return []
    if _has_section(_headings(lines), ["metric", "success metric", "kpi"]):
        return []
    return [_vio(
        "pack-product-brief-missing-metric", "error", file_path, 1, lines[0] if lines else "",
        "Product brief missing 'Success Metric' / 'Metric' section — every brief must declare how success is measured."
    )]


def rule_brief_missing_acceptance(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_brief(file_path):
        return []
    if _has_section(_headings(lines), ["acceptance", "acceptance criteria", "done criteria"]):
        return []
    return [_vio(
        "pack-product-brief-missing-acceptance", "error", file_path, 1, lines[0] if lines else "",
        "Product brief missing 'Acceptance Criteria' section — what does 'done' look like?"
    )]


def rule_brief_missing_problem(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_brief(file_path):
        return []
    if _has_section(_headings(lines), ["problem", "problem statement", "context"]):
        return []
    return [_vio(
        "pack-product-brief-missing-problem", "error", file_path, 1, lines[0] if lines else "",
        "Product brief missing 'Problem' / 'Problem Statement' section — lead with the problem, not the solution."
    )]


KR_LINE = re.compile(r"^\s*(?:-|\*|\d+\.)\s+(?:KR\d?|Key Result)[:\.]?\s*(.+)$", re.IGNORECASE)
HAS_NUMBER = re.compile(r"(\d+(?:[.,]\d+)?\s*%|\$\d|\d{2,}|by\s+\d{4})")


def rule_okr_missing_number(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_okr(file_path):
        return []
    out = []
    for i, raw in enumerate(lines, start=1):
        m = KR_LINE.match(raw)
        if not m:
            continue
        body = m.group(1)
        if not HAS_NUMBER.search(body):
            out.append(_vio(
                "pack-product-okr-missing-number", "warn", file_path, i, raw,
                "Key Result has no measurable number — KRs must be quantitative (%, count, currency, or deadline)."
            ))
    return out


JARGON_TERMS = [
    "controller", "schema", "deployment", "container", "microservice",
    "refactor", "endpoint", "payload", "orm", "jpa", "dto",
    "kubernetes", "docker", "kafka topic", "graphql resolver",
    "rest api", "grpc", "middleware",
]
JARGON_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in JARGON_TERMS) + r")\b", re.IGNORECASE)
TECH_REF_MARKER = re.compile(r"technical reference|tech ref|implementation note", re.IGNORECASE)


def rule_jargon_leak(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_product_doc(file_path):
        return []
    out = []
    in_tech_ref = False
    for i, raw in enumerate(lines, start=1):
        if TECH_REF_MARKER.search(raw):
            in_tech_ref = True
            continue
        if in_tech_ref:
            continue
        # skip code fences (very rough)
        if raw.lstrip().startswith("```"):
            continue
        m = JARGON_RE.search(raw)
        if m:
            out.append(_vio(
                "pack-product-jargon-leak", "warn", file_path, i, raw,
                f"Technical jargon '{m.group(1)}' in product doc — translate to business language or move to 'Technical reference' footnote."
            ))
    return out


VAGUE_DATE = re.compile(r"\b(soon|next sprint|tbd|q\?|sometime|asap|eventually)\b", re.IGNORECASE)


def rule_roadmap_vague_date(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_roadmap(file_path):
        return []
    out = []
    for i, raw in enumerate(lines, start=1):
        m = VAGUE_DATE.search(raw)
        if m:
            out.append(_vio(
                "pack-product-roadmap-vague-date", "warn", file_path, i, raw,
                f"Vague date '{m.group(1)}' — use YYYY-Qx (quarter) or YYYY-MM (month) instead."
            ))
    return out


IMPL_DICTATE = re.compile(
    r"\b(use\s+(postgres|mysql|mongo(db)?|redis|kafka|rabbitmq|elasticsearch)|"
    r"build\s+(rest|graphql|grpc)\s+api|"
    r"deploy\s+on\s+(aws|gcp|azure|k8s|kubernetes)|"
    r"use\s+(react|vue|angular|next\.?js))\b",
    re.IGNORECASE,
)


def rule_brief_dictates_impl(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_brief(file_path):
        return []
    out = []
    for i, raw in enumerate(lines, start=1):
        m = IMPL_DICTATE.search(raw)
        if m:
            out.append(_vio(
                "pack-product-brief-dictates-impl", "warn", file_path, i, raw,
                f"Brief dictates implementation ('{m.group(0)}') — express as constraint (latency, cost, compliance), let engineering choose tech."
            ))
    return out


RULES = [
    rule_brief_missing_metric,
    rule_brief_missing_acceptance,
    rule_brief_missing_problem,
    rule_okr_missing_number,
    rule_jargon_leak,
    rule_roadmap_vague_date,
    rule_brief_dictates_impl,
]
