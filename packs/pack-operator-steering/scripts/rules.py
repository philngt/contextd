#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack-operator-steering — Layer 1 validator rules."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List


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


def _is_md(file_path: Path) -> bool:
    return file_path.suffix.lower() == ".md"


def _text(lines: List[str]) -> str:
    return "\n".join(lines)


def _has_any(text: str, needles: List[str]) -> bool:
    lower = text.lower()
    return any(needle.lower() in lower for needle in needles)


def _looks_operator_doc(file_path: Path, lines: List[str]) -> bool:
    haystack = (file_path.as_posix() + "\n" + "\n".join(lines[:80])).lower()
    return any(
        token in haystack
        for token in [
            "audit", "drift", "remediation", "finding", "handoff",
            "session brief", "decision", "adr", "context quality",
            "đánh giá", "nghiệm thu", "bàn giao", "quyết định",
        ]
    )


def _looks_decision_doc(file_path: Path, lines: List[str]) -> bool:
    name = file_path.name.lower()
    if "decision" in name or name.startswith("adr-") or "-adr-" in name:
        return True
    for raw in lines[:30]:
        stripped = raw.strip().lower()
        if stripped == "type: decision":
            return True
        if not stripped.startswith("# "):
            continue
        title = stripped[2:].strip()
        if title in {
            "decision", "decision note", "decision record",
            "architecture decision record", "adr", "quyết định",
        }:
            return True
    return False


def _looks_wayfinding_doc(file_path: Path, lines: List[str]) -> bool:
    haystack = (file_path.as_posix() + "\n" + "\n".join(lines[:40])).lower()
    return any(
        token in haystack
        for token in [
            "wayfinding checkpoint", "operator wayfinding",
            "steering checkpoint", "orientation checkpoint",
            "điểm định hướng", "diem dinh huong",
        ]
    )


def rule_report_missing_evidence(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path) or not _looks_operator_doc(file_path, lines):
        return []
    text = _text(lines)
    if _has_any(text, ["## Evidence", "## Bằng chứng", "Evidence:", "Bằng chứng:"]):
        return []
    return [_vio(
        "pack-operator-steering-report-missing-evidence", "error", file_path, 1,
        lines[0] if lines else "",
        "Operator steering artifact should include an Evidence/Bằng chứng section before judgment."
    )]


def rule_remediation_missing_verification(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path):
        return []
    text = _text(lines)
    if not _has_any(text, ["remediation", "khắc phục", "khac phuc"]):
        return []
    has_acceptance = _has_any(text, ["Acceptance Criteria", "Tiêu chí nghiệm thu", "Nghiệm thu"])
    has_verification = _has_any(text, ["Verification Method", "Verification", "Cách kiểm chứng", "Kiểm chứng"])
    if has_acceptance and has_verification:
        return []
    return [_vio(
        "pack-operator-steering-remediation-missing-verification", "error", file_path, 1,
        lines[0] if lines else "",
        "Remediation artifact should include acceptance criteria and verification method."
    )]


def rule_decision_missing_ledger_fields(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path):
        return []
    if not _looks_decision_doc(file_path, lines):
        return []
    text = _text(lines)
    missing = []
    if not _has_any(text, ["Status", "Trạng thái"]):
        missing.append("status")
    if not _has_any(text, ["Owner", "DRI", "Người chịu trách nhiệm"]):
        missing.append("owner")
    if not _has_any(text, ["Revisit", "Review trigger", "Khi xem lại"]):
        missing.append("revisit trigger")
    if not missing:
        return []
    return [_vio(
        "pack-operator-steering-decision-missing-ledger-fields", "warn", file_path, 1,
        lines[0] if lines else "",
        "Decision artifact should include: " + ", ".join(missing) + "."
    )]


def rule_handoff_missing_next_action(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path):
        return []
    haystack = (file_path.as_posix() + "\n" + _text(lines[:80])).lower()
    if "handoff" not in haystack and "session brief" not in haystack and "bàn giao" not in haystack:
        return []
    text = _text(lines)
    missing = []
    if not _has_any(text, ["Next Action", "Next step", "Hành động tiếp theo"]):
        missing.append("next action")
    if not _has_any(text, ["Stop Condition", "Stop condition", "Điều kiện dừng"]):
        missing.append("stop condition")
    if not missing:
        return []
    return [_vio(
        "pack-operator-steering-handoff-missing-next-action", "warn", file_path, 1,
        lines[0] if lines else "",
        "Handoff artifact should include: " + ", ".join(missing) + "."
    )]


def rule_wayfinding_missing_control_fields(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path) or not _looks_wayfinding_doc(file_path, lines):
        return []
    text = _text(lines)
    required = {
        "current orientation": ["## Current Orientation", "## Định hướng hiện tại"],
        "primary gap": ["## Primary Gap", "## Gap chính", "## Khoảng trống chính"],
        "knowledge recovery": ["## Knowledge Recovery", "## Khôi phục kiến thức"],
        "decision frontier": ["## Decision Frontier", "## Các quyết định đang mở"],
        "recommended next step": ["## Recommended Next Step", "## Bước tiếp theo đề xuất"],
        "continue/pause/pivot/stop gate": [
            "## Continue, Pause, Pivot, Or Stop",
            "## Tiếp tục, Tạm dừng, Chuyển hướng, Hoặc dừng",
        ],
        "operator decision": ["## Operator Decision", "## Quyết định của người dùng"],
    }
    missing = [label for label, needles in required.items() if not _has_any(text, needles)]
    if not missing:
        return []
    return [_vio(
        "pack-operator-steering-wayfinding-missing-control-fields", "error",
        file_path, 1, lines[0] if lines else "",
        "Wayfinding checkpoint missing: " + ", ".join(missing) + ".",
    )]


RULES: List = [
    rule_report_missing_evidence,
    rule_remediation_missing_verification,
    rule_decision_missing_ledger_fields,
    rule_handoff_missing_next_action,
    rule_wayfinding_missing_control_fields,
]
