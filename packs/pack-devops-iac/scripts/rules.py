#!/usr/bin/env python3
"""pack-devops-iac — narrow Layer-1 infrastructure safety validators."""

from __future__ import annotations

import re
import shlex
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
    for index in range(source_index, -1, -1):
        if re.match(r"^\s*[A-Za-z0-9_-]+\s*=\s*{\s*$", lines[index]):
            return index
        if re.match(r"^\s*required_providers\s*{", lines[index]):
            break
    return None


def rule_terraform_unpinned_provider(file_path: Path, lines: List[str],
                                     ctx: Dict) -> List[Dict]:
    if file_path.suffix.lower() != ".tf":
        return []
    out = []
    index = 0
    while index < len(lines):
        if not re.search(r"\brequired_providers\s*{", lines[index]):
            index += 1
            continue
        required_end, required_lines = _brace_block(lines, index)
        for offset, raw in enumerate(required_lines):
            if not re.search(r"\bsource\s*=\s*[\"'][^\"']+[\"']", raw):
                continue
            start = _assignment_block_start(required_lines, offset)
            if start is None:
                continue
            _, provider_block = _brace_block(required_lines, start)
            if re.search(
                r"(?m)^\s*version\s*=\s*[\"'][^\"']+[\"']",
                "\n".join(provider_block),
            ):
                continue
            source_line = index + offset
            out.append(_vio(
                "pack-devops-iac-terraform-unpinned-provider", "error",
                file_path, source_line + 1, raw,
                "Terraform provider source has no version constraint in its provider block.",
            ))
        index = required_end + 1
    return out


MODULE_START = re.compile(r'^\s*module\s+[\"\'][^\"\']+[\"\']\s*{')
SOURCE_VALUE = re.compile(r'(?m)^\s*source\s*=\s*[\"\']([^\"\']+)[\"\']')
FULL_COMMIT_REF = re.compile(r"[?&]ref=[0-9a-fA-F]{40}(?:&|$)")


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
            has_full_commit_ref = bool(FULL_COMMIT_REF.search(source))
            source_without_query = source.split("?", 1)[0].lower()
            is_git_source = (
                source.startswith("git::")
                or source.startswith(("github.com/", "bitbucket.org/"))
                or source_without_query.endswith(".git")
            )
            dependency_is_pinned = (has_full_commit_ref if is_git_source
                                    else has_version)
            if not local and not dependency_is_pinned:
                source_line = index + next(
                    (offset for offset, line in enumerate(block_lines)
                     if SOURCE_VALUE.search(line)), 0
                )
                out.append(_vio(
                    "pack-devops-iac-terraform-unpinned-module", "error",
                    file_path, source_line + 1, lines[source_line],
                    f"Remote Terraform module '{source}' is not pinned to a registry version or full Git commit SHA.",
                ))
        index = end + 1
    return out


def _is_yaml(file_path: Path) -> bool:
    return file_path.suffix.lower() in {".yaml", ".yml"}


YAML_DOCUMENT_SEPARATOR = re.compile(r"^\s*---(?:\s+#.*)?\s*$")
WORKLOAD_KIND = re.compile(
    r"(?m)^\s*kind\s*:\s*(Deployment|StatefulSet|DaemonSet)\s*$"
)
CONTAINERS_KEY = re.compile(r"^(\s*)containers\s*:\s*(?:#.*)?$")
CONTAINER_ITEM = re.compile(r"^(\s*)-\s*(?:[^#].*)?$")
IMAGE_VALUE = re.compile(r"^\s*(?:-\s*)?image\s*:\s*([^#]+?)(?:\s+#.*)?$")
DIGEST_PINNED_IMAGE = re.compile(r"^\S+@sha256:[0-9a-fA-F]{64}$")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _yaml_documents(lines: List[str]) -> List[Tuple[int, List[str]]]:
    documents = []
    start = 0
    for index, raw in enumerate(lines):
        if not YAML_DOCUMENT_SEPARATOR.match(raw):
            continue
        if any(line.strip() for line in lines[start:index]):
            documents.append((start, lines[start:index]))
        start = index + 1
    if any(line.strip() for line in lines[start:]):
        documents.append((start, lines[start:]))
    return documents


def _workload_containers(lines: List[str]) -> List[Tuple[int, str, List[str]]]:
    """Return (zero-based line, display name, block) per workload container."""
    containers = []
    for document_start, document in _yaml_documents(lines):
        if not WORKLOAD_KIND.search("\n".join(document)):
            continue
        for section_index, raw in enumerate(document):
            section_match = CONTAINERS_KEY.match(raw)
            if not section_match:
                continue
            section_indent = len(section_match.group(1))
            section_end = len(document)
            for index in range(section_index + 1, len(document)):
                candidate = document[index]
                if not candidate.strip() or candidate.lstrip().startswith("#"):
                    continue
                if _indent(candidate) <= section_indent:
                    section_end = index
                    break

            item_indent = None
            item_starts = []
            for index in range(section_index + 1, section_end):
                item_match = CONTAINER_ITEM.match(document[index])
                if not item_match:
                    continue
                indent = len(item_match.group(1))
                if item_indent is None:
                    item_indent = indent
                if indent == item_indent:
                    item_starts.append(index)

            for position, item_start in enumerate(item_starts):
                item_end = (item_starts[position + 1]
                            if position + 1 < len(item_starts) else section_end)
                block = document[item_start:item_end]
                name = "<unnamed>"
                for block_line in block:
                    name_match = re.match(
                        r"^\s*(?:-\s*)?name\s*:\s*[\"']?([^\s\"'#]+)",
                        block_line,
                    )
                    if name_match:
                        name = name_match.group(1)
                        break
                containers.append((document_start + item_start, name, block))
    return containers


def _has_resource_requests(block: List[str]) -> bool:
    for index, raw in enumerate(block):
        if not re.match(r"^\s*resources\s*:\s*(?:#.*)?$", raw):
            continue
        resources_indent = _indent(raw)
        for nested in block[index + 1:]:
            if not nested.strip() or nested.lstrip().startswith("#"):
                continue
            if _indent(nested) <= resources_indent:
                break
            if re.match(r"^\s*requests\s*:\s*(?:#.*)?$", nested):
                return True
    return False


def rule_k8s_image_not_digest_pinned(file_path: Path, lines: List[str],
                                     ctx: Dict) -> List[Dict]:
    if not _is_yaml(file_path):
        return []
    out = []
    for start, name, block in _workload_containers(lines):
        for offset, raw in enumerate(block):
            image_match = IMAGE_VALUE.match(raw)
            if not image_match:
                continue
            image = image_match.group(1).strip().strip("\"'")
            if DIGEST_PINNED_IMAGE.match(image):
                continue
            out.append(_vio(
                "pack-devops-iac-k8s-image-not-digest-pinned", "error",
                file_path, start + offset + 1, raw,
                f"Kubernetes container '{name}' image is not pinned by sha256 digest.",
            ))
    return out


def rule_k8s_missing_readiness_probe(file_path: Path, lines: List[str],
                                     ctx: Dict) -> List[Dict]:
    if not _is_yaml(file_path):
        return []
    out = []
    for start, name, block in _workload_containers(lines):
        if re.search(r"(?m)^\s*readinessProbe\s*:\s*$", "\n".join(block)):
            continue
        out.append(_vio(
            "pack-devops-iac-k8s-missing-readiness-probe", "warn",
            file_path, start + 1, block[0],
            f"Kubernetes container '{name}' has no readinessProbe.",
        ))
    return out


def rule_k8s_missing_resource_requests(file_path: Path, lines: List[str],
                                       ctx: Dict) -> List[Dict]:
    if not _is_yaml(file_path):
        return []
    out = []
    for start, name, block in _workload_containers(lines):
        if _has_resource_requests(block):
            continue
        out.append(_vio(
            "pack-devops-iac-k8s-missing-resource-requests", "warn",
            file_path, start + 1, block[0],
            f"Kubernetes container '{name}' has no resource requests.",
        ))
    return out


def _is_ci_workflow(file_path: Path) -> bool:
    path = file_path.as_posix().lower()
    return _is_yaml(file_path) and any(marker in path for marker in (
        "/.github/workflows/", "/.gitlab/", "/ci/", "/pipelines/"
    ))


APPLY_COMMAND = re.compile(
    r"\b(terraform|tofu)\s+apply\b((?:\\\s*\n\s*|[^\n])*)"
)
OPTIONS_WITH_SEPARATE_VALUE = {
    "-backup", "-lock-timeout", "-parallelism", "-state", "-state-out",
    "-var", "-var-file",
}
REDIRECT_WITH_SEPARATE_TARGET = re.compile(r"^(?:\d*|&)(?:>>?|<<?)$")
REDIRECT_WITH_INLINE_TARGET = re.compile(r"^(?:\d*|&)(?:>>?|<<?).+$")


def _apply_consumes_saved_plan(arguments: str) -> bool:
    arguments = re.sub(r"\\\s*\n\s*", " ", arguments)
    try:
        tokens = shlex.split(arguments, comments=True)
    except ValueError:
        return False
    skip_value = False
    for token in tokens:
        if skip_value:
            skip_value = False
            continue
        if token in {"&&", "||", ";", "|"}:
            break
        if token in OPTIONS_WITH_SEPARATE_VALUE:
            skip_value = True
            continue
        if REDIRECT_WITH_SEPARATE_TARGET.match(token):
            skip_value = True
            continue
        if REDIRECT_WITH_INLINE_TARGET.match(token):
            continue
        if token.startswith("-"):
            continue
        return True
    return False


def rule_terraform_apply_without_saved_plan(file_path: Path, lines: List[str],
                                            ctx: Dict) -> List[Dict]:
    if not _is_ci_workflow(file_path):
        return []
    text = "\n".join(lines)
    out = []
    for match in APPLY_COMMAND.finditer(text):
        if _apply_consumes_saved_plan(match.group(2)):
            continue
        lineno = text[:match.start()].count("\n") + 1
        out.append(_vio(
            "pack-devops-iac-terraform-apply-without-saved-plan", "error",
            file_path, lineno, lines[lineno - 1],
            "CI apply command does not consume an explicit saved plan argument.",
        ))
    return out


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
    rule_k8s_image_not_digest_pinned,
    rule_k8s_missing_readiness_probe,
    rule_k8s_missing_resource_requests,
    rule_terraform_apply_without_saved_plan,
    rule_deployment_no_rollback,
]
