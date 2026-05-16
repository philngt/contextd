#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Dict, List


def _vio(rule, severity, file_path, lineno, snippet, message):
    return {"rule": rule, "severity": severity, "file": file_path.as_posix(), "line": lineno, "snippet": snippet.strip()[:200], "message": message}

def _is_md(p: Path) -> bool:
    return p.as_posix().lower().endswith('.md')

def rule_migration_no_rollback(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'migration' not in t and 'schema change' not in t and 'ddl' not in t: return []
    if 'rollback' in t or 'forward-fix' in t or 'forward fix' in t: return []
    return [_vio('pack-dba-migration-no-rollback','error',file_path,1,lines[0] if lines else '','Schema/migration doc should include rollback or forward-fix strategy.')]

def rule_query_no_evidence(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'query' not in t and 'index' not in t and 'optimiz' not in t: return []
    if 'explain' in t or 'execution plan' in t or 'p95' in t or 'slow query' in t or 'latency' in t: return []
    return [_vio('pack-dba-query-no-evidence','warn',file_path,1,lines[0] if lines else '','Query optimization should include plan/metric evidence.')]

def rule_backup_no_rpo_rto(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'backup' not in t and 'recovery' not in t and 'dr' not in t: return []
    if 'rpo' in t and 'rto' in t: return []
    return [_vio('pack-dba-backup-no-rpo-rto','error',file_path,1,lines[0] if lines else '','Backup/DR document should define both RPO and RTO.')]

def rule_no_restore_verification(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'backup' not in t and 'restore' not in t and 'recovery' not in t: return []
    if 'restore test' in t or 'restore verification' in t or 'recovery drill' in t or 'verification cadence' in t:
        return []
    return [_vio('pack-dba-no-restore-verification','warn',file_path,1,lines[0] if lines else '','Backup strategy should include periodic restore verification.')]

RULES=[rule_migration_no_rollback,rule_query_no_evidence,rule_backup_no_rpo_rto,rule_no_restore_verification]
