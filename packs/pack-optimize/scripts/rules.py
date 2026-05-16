#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Dict, List


def _vio(rule, severity, file_path, lineno, snippet, message):
    return {"rule": rule, "severity": severity, "file": file_path.as_posix(), "line": lineno, "snippet": snippet.strip()[:200], "message": message}

def _is_md(p: Path) -> bool:
    return p.as_posix().lower().endswith('.md')

def rule_no_baseline_metric(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'optimiz' not in t and 'performance' not in t: return []
    if 'baseline' in t and ('target' in t or 'goal' in t): return []
    return [_vio('pack-optimize-no-baseline-metric','error',file_path,1,lines[0] if lines else '','Optimization doc missing baseline/target metric.')]

def rule_no_measure_loop(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'before' in t and 'after' in t: return []
    if 'optimiz' not in t and 'performance' not in t: return []
    return [_vio('pack-optimize-no-measure-loop','warn',file_path,1,lines[0] if lines else '','Include before/after measurement loop.')]

def rule_premature_tuning(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'tuning' not in t and 'optimiz' not in t: return []
    if 'profil' in t or 'bottleneck' in t or 'hotspot' in t: return []
    return [_vio('pack-optimize-premature-tuning','warn',file_path,1,lines[0] if lines else '','Tuning proposal should include profiling/bottleneck evidence.')]

def rule_no_regression_check(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'optimiz' not in t and 'performance' not in t: return []
    if 'regression' in t or 'rollback' in t or 'guardrail' in t: return []
    return [_vio('pack-optimize-no-regression-check','warn',file_path,1,lines[0] if lines else '','Add regression check/rollback plan for optimization.')]

RULES=[rule_no_baseline_metric,rule_no_measure_loop,rule_premature_tuning,rule_no_regression_check]
