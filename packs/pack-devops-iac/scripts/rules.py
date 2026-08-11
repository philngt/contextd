#!/usr/bin/env python3
"""pack-devops-iac — narrow Layer-1 infrastructure safety validators."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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


def _brace_block(lines: List[str], start: int) -> Tuple[int, List[str]]:
    """Return the inclusive end index and lines for a brace-delimited block."""
    depth = 0
    opened = False
    block: List[str] = []
    for index in range(start, len(lines)):
        line = lines[index]
        block.append(line)
        depth += line.count("{")
        if "{" in line:
            opened = True
        depth -= line.count("}")
        if opened and depth <= 0:
            return index, block
    return len(lines) - 1, block


def _assignment_block_start(lines: List[str], source_index: int) -> Optional[int]:
    for index in range(source_index, max(-1, source_index - 8), -1):
        if re.match(r"^\s*[A-Za-z0-9_-]+\s*=\s*{\s*$", lines[index]):
            return index
        if re.match(r"^\s*required_providers\s*{", lines[index]):
            break
    return None


def rule_terraform_unpinned_provider(file_path: Path, lines: List[str],
                                     ctx: Dict) -> List[Dict]:
    if file_path.suffix.lower() != ".tf":
        return []
    text = "\n".join(lines)
    if not re.search(r"\brequired_providers\s*{", text):
        return []
    out = []
    for index, raw in enumerate(lines):
        if not re.search(r"\bsource\s*=\s*[\"'][^\"']+[\"']", raw):
            continue
        start = _assignment_block_start(lines, index)
        if start is None:
            continue
        _, block = _brace_block(lines, start)
        if re.search(r"(?m)^\s*version\s*=\s*[\"'][^\"']+[\"']", "\n".join(block)):
            continue
        out.append(_vio(
            "pack-devops-iac-terraform-unpinned-provider", "error",
            file_path, index + 1, raw,
            "Terraform provider source has no version constraint in its provider block.",
        ))
    return out


MODULE_START = re.compile(r'^\s*module\s+[\"\'][^\"\']+[\"\']\s*{')
SOURCE_VALUE = re.compile(r'(?m)^\s*source\s*=\s*[\"\']([^\"\']+)[\"\']')


def rule_terraform_unpinned_module(file_path: Path, lines: List[str],
                                   ctx: Dict) -> List[Dict]:
    if file_path.suffix.lower() != ".tf":
        return []
    out = []
    index = 0
    while index < len(lines):
        if not MODULE_START.search(lines[index]):
            index += 1
            continue
        end, block_lines = _brace_block(lines, index)
        block = "\n".join(block_lines)
        source_match = SOURCE_VALUE.search(block)
        if source_match:
            source = source_match.group(1)
            local = source.startswith(("./", "../"))
            has_version = bool(re.search(
                r"(?m)^\s*version\s*=\s*[\"'][^\"']+[\"']", block
            ))
            has_git_ref = "?ref=" in source and not re.search(
                r"[?&]ref=(main|master|head)(?:&|$)", source, re.IGNORECASE
            )
            if not local and not has_version and not has_git_ref:
                source_line = index + next(
                    (offset for offset, line in enumerate(block_lines)
                     if SOURCE_VALUE.search(line)), 0
                )
                out.append(_vio(
                    "pack-devops-iac-terraform-unpinned-module", "error",
                    file_path, source_line + 1, lines[source_line],
                    f"Remote Terraform module '{source}' is not pinned to a version or immutable ref.",
                ))
        index = end + 1
    return out


def _is_yaml(file_path: Path) -> bool:
    return file_path.suffix.lower() in {".yaml", ".yml"}


def _is_k8s_workload(lines: List[str]) -> bool:
    text = "\n".join(lines)
    return bool(re.search(
        r"(?m)^\s*kind\s*:\s*(Deployment|StatefulSet|DaemonSet)\s*$", text
    )) and bool(re.search(r"(?m)^\s*containers\s*:\s*$", text))


LATEST_IMAGE = re.compile(
    r"^(\s*(?:-\s*)?image\s*:\s*)([\"']?[^\s\"']+:latest[\"']?)(?:\s+#.*)?$",
    re.IGNORECASE,
)


def rule_k8s_mutable_image_tag(file_path: Path, lines: List[str],
                                ctx: Dict) -> List[Dict]:
    if not _is_yaml(file_path) or not _is_k8s_workload(lines):
        return []
    out = []
    for lineno, raw in enumerate(lines, 1):
        if LATEST_IMAGE.match(raw):
            out.append(_vio(
                "pack-devops-iac-k8s-mutable-image-tag", "error",
                file_path, lineno, raw,
                "Kubernetes workload uses the mutable 'latest' image tag; use an immutable release tag or digest.",
            ))
    return out


def rule_k8s_missing_readiness_probe(file_path: Path, lines: List[str],
                                     ctx: Dict) -> List[Dict]:
    if not _is_yaml(file_path) or not _is_k8s_workload(lines):
        return []
    if re.search(r"(?m)^\s*readinessProbe\s*:\s*$", "\n".join(lines)):
        return []
    return [_vio(
        "pack-devops-iac-k8s-missing-readiness-probe", "warn", file_path, 1,
        lines[0] if lines else "",
        "Kubernetes workload has containers but no readinessProbe.",
    )]


def rule_k8s_missing_resource_requests(file_path: Path, lines: List[str],
                                       ctx: Dict) -> List[Dict]:
    if not _is_yaml(file_path) or not _is_k8s_workload(lines):
        return []
    text = "\n".join(lines)
    if re.search(r"(?m)^\s*requests\s*:\s*$", text):
        return []
    return [_vio(
        "pack-devops-iac-k8s-missing-resource-requests", "warn", file_path, 1,
        lines[0] if lines else "",
        "Kubernetes workload has containers but no resource requests.",
    )]


def _is_ci_workflow(file_path: Path) -> bool:
    path = file_path.as_posix().lower()
    return _is_yaml(file_path) and any(marker in path for marker in (
        "/.github/workflows/", "/.gitlab/", "/ci/", "/pipelines/"
    ))


def rule_terraform_apply_without_plan(file_path: Path, lines: List[str],
                                      ctx: Dict) -> List[Dict]:
    if not _is_ci_workflow(file_path):
        return []
    text = "\n".join(lines)
    apply_matches = list(re.finditer(r"\b(terraform|tofu)\s+apply\b([^\n]*)", text))
    if not apply_matches:
        return []
    has_plan_command = bool(re.search(r"\b(terraform|tofu)\s+plan\b", text))
    has_saved_plan = any(re.search(r"(?:^|\s)[^\s-]+\.tfplan(?:\s|$)", match.group(2))
                         for match in apply_matches)
    if has_plan_command or has_saved_plan:
        return []
    first = apply_matches[0]
    lineno = text[:first.start()].count("\n") + 1
    return [_vio(
        "pack-devops-iac-terraform-apply-without-plan", "error", file_path,
        lineno, lines[lineno - 1],
        "CI workflow applies infrastructure without a plan command or saved plan input.",
    )]


def rule_deployment_no_rollback(file_path: Path, lines: List[str],
                                ctx: Dict) -> List[Dict]:
    if file_path.suffix.lower() != ".md":
        return []
    path = file_path.as_posix().lower()
    if not any(marker in path for marker in (
        "deploy", "release", "/runbooks/", "/runbook/"
    )):
        return []
    text = "\n".join(lines)
    if not re.search(r"\b(deploy(?:ment)?|release|rollout)\b", text, re.IGNORECASE):
        return []
    if re.search(r"\b(rollback|roll\s+back|roll-forward|roll\s+forward|rollout\s+undo)\b",
                 text, re.IGNORECASE):
        return []
    return [_vio(
        "pack-devops-iac-deployment-no-rollback", "warn", file_path, 1,
        lines[0] if lines else "",
        "Deployment/release instructions do not describe a rollback or roll-forward path.",
    )]


RULES = [
    rule_terraform_unpinned_provider,
    rule_terraform_unpinned_module,
    rule_k8s_mutable_image_tag,
    rule_k8s_missing_readiness_probe,
    rule_k8s_missing_resource_requests,
    rule_terraform_apply_without_plan,
    rule_deployment_no_rollback,
]
