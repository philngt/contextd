#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import re


def _vio(rule, severity, file_path, lineno, snippet, message):
    return {"rule": rule, "severity": severity, "file": file_path.as_posix(), "line": lineno, "snippet": snippet.strip()[:200], "message": message}

def _is_md(p: Path) -> bool:
    return p.as_posix().lower().endswith('.md')

def rule_missing_threat_model(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'security' not in t and 'design' not in t: return []
    if 'threat' in t or 'abuse case' in t: return []
    return [_vio('pack-security-missing-threat-model','error',file_path,1,lines[0] if lines else '','Missing threat assumptions/abuse cases.')]

def rule_secrets_in_config(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    out=[]
    pat=re.compile(r'(api[_-]?key|secret|token|password)\s*[:=]\s*["\'][^"\']{8,}["\']',re.I)
    for i,l in enumerate(lines,1):
        if pat.search(l): out.append(_vio('pack-security-secrets-in-config','error',file_path,i,l,'Potential hardcoded secret found.'))
    return out

def rule_missing_authz_boundary(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'endpoint' not in t and 'flow' not in t: return []
    if 'authz' in t or 'authorization' in t or 'permission' in t: return []
    return [_vio('pack-security-missing-authz-boundary','warn',file_path,1,lines[0] if lines else '','Sensitive flow should document authorization boundary.')]

def rule_no_logging_redaction(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
    if not _is_md(file_path): return []
    t='\n'.join(lines).lower()
    if 'log' not in t: return []
    if 'redact' in t or 'mask' in t: return []
    return [_vio('pack-security-no-logging-redaction','warn',file_path,1,lines[0] if lines else '','Logging guidance should include redaction/masking for sensitive data.')]

RULES=[rule_missing_threat_model,rule_secrets_in_config,rule_missing_authz_boundary,rule_no_logging_redaction]
