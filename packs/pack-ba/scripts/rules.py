#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack-ba — Layer 1 validator rules. Prefix: pack-ba-."""

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


def _is_md(file_path: Path) -> bool:
    return file_path.as_posix().lower().endswith(".md")


def _looks_like_requirement_doc(path: Path, lines: List[str]) -> bool:
    p = path.as_posix().lower()
    if any(k in p for k in ["requirement", "brd", "story", "spec"]):
        return True
    text = "\n".join(lines[:60]).lower()
    return any(k in text for k in ["requirement", "acceptance criteria", "business outcome"])


def _looks_like_process_doc(path: Path, lines: List[str]) -> bool:
    p = path.as_posix().lower()
    if any(k in p for k in ["process", "workflow", "journey"]):
        return True
    text = "\n".join(lines[:60]).lower()
    return any(k in text for k in ["as-is", "to-be", "workflow"])


def _looks_like_stakeholder_doc(path: Path, lines: List[str]) -> bool:
    p = path.as_posix().lower()
    if "stakeholder" in p or "dependency" in p:
        return True
    text = "\n".join(lines[:60]).lower()
    return any(k in text for k in ["stakeholder", "owner", "sign-off", "dependency"])


def rule_requirement_missing_actor_or_outcome(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path) or not _looks_like_requirement_doc(file_path, lines):
        return []
    text = "\n".join(lines).lower()
    has_actor = any(k in text for k in ["actor", "user", "customer", "operator"])
    has_outcome = any(k in text for k in ["outcome", "business value", "result", "goal"])
    if has_actor and has_outcome:
        return []
    return [_vio(
        "pack-ba-requirement-missing-actor-or-outcome", "error", file_path, 1, lines[0] if lines else "",
        "Requirement should state both actor and business outcome."
    )]


VAGUE_LANG = re.compile(r"\b(fast|easy|better|user-friendly|efficient|quick|simple)\b", re.IGNORECASE)


def rule_acceptance_vague_language(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path) or not _looks_like_requirement_doc(file_path, lines):
        return []
    out = []
    for i, raw in enumerate(lines, start=1):
        if "acceptance" not in raw.lower() and not raw.strip().startswith(("-", "*", "1.", "2.", "3.")):
            continue
        m = VAGUE_LANG.search(raw)
        if m:
            out.append(_vio(
                "pack-ba-acceptance-vague-language", "warn", file_path, i, raw,
                f"Acceptance language is vague ('{m.group(1)}'); add measurable criteria."
            ))
    return out


def rule_process_missing_asis_tobe(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path) or not _looks_like_process_doc(file_path, lines):
        return []
    text = "\n".join(lines).lower()
    has_asis = "as-is" in text or "asis" in text
    has_tobe = "to-be" in text or "tobe" in text
    if has_asis and has_tobe:
        return []
    return [_vio(
        "pack-ba-process-missing-asis-tobe", "warn", file_path, 1, lines[0] if lines else "",
        "Process mapping should distinguish As-Is and To-Be states."
    )]


def rule_stakeholder_missing_owner(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path) or not _looks_like_stakeholder_doc(file_path, lines):
        return []
    text = "\n".join(lines).lower()
    has_owner = "owner" in text or "responsible" in text
    if has_owner:
        return []
    return [_vio(
        "pack-ba-stakeholder-missing-owner", "warn", file_path, 1, lines[0] if lines else "",
        "Stakeholder/dependency doc should identify owner/responsible party."
    )]


RULES = [
    rule_requirement_missing_actor_or_outcome,
    rule_acceptance_vague_language,
    rule_process_missing_asis_tobe,
    rule_stakeholder_missing_owner,
]
