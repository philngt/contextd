#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small stdlib-only safety helpers for contextd runtime reads."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Dict, List, Tuple


SECRET_DIR_NAMES = {"secrets", "credentials", ".ssh", ".gnupg"}
SECRET_FILE_NAMES = {
    ".env",
    ".env.local",
    "vault.yaml",
    "vault.yml",
    "vault.properties",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}
SECRET_SUFFIXES = {".key", ".pem", ".p12", ".jks", ".pfx", ".crt", ".cer"}
SECRET_CONFIG_PATTERNS = [
    ".env.*",
    "*-prod.yaml",
    "*-prod.yml",
    "*-prod.properties",
    "*-production.yaml",
    "*-production.yml",
    "*-production.properties",
    "*secret*.yaml",
    "*secret*.yml",
    "*secret*.properties",
    "*credential*.yaml",
    "*credential*.yml",
    "*credential*.properties",
    "*keystore*",
    "*truststore*",
]

SAFE_CONTEXT_NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]*$")

REDACTION_PATTERNS = [
    (
        "url_credentials",
        re.compile(r"https?://[A-Za-z0-9._%+-]+:[^@\s]+@"),
        "<REDACTED-URL>",
    ),
    (
        "secret_assignment",
        re.compile(
            r"(?i)(?<![-\w])\b(password|token|api[-_]?key|secret|jwt[-_]?key)"
            r"(\s*[:=]\s*)([^<\s]+)"
        ),
        None,
    ),
]


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_context_name(value: object, label: str = "name") -> Tuple[str | None, str | None]:
    """Validate workspace/pack identifiers before using them as path segments."""
    if not isinstance(value, str):
        return None, f"{label} must be a string"
    name = value.strip()
    if not name:
        return None, f"{label} must not be empty"
    if "\x00" in name:
        return None, f"{label} must not contain NUL bytes"
    if name in {".", ".."} or ".." in name:
        return None, f"{label} must not contain parent traversal"
    if "/" in name or "\\" in name:
        return None, f"{label} must not contain path separators"
    if ":" in name:
        return None, f"{label} must not contain drive or URI separators"
    if not SAFE_CONTEXT_NAME_RE.fullmatch(name):
        return None, (
            f"{label} must start with a letter, digit, or '_' and contain only "
            "letters, digits, '.', '_', and '-'"
        )
    return name, None


def safe_child_path(root: Path, *parts: object) -> Path:
    """Resolve a child path and require it to stay under root after symlinks."""
    root_resolved = root.resolve()
    candidate = root_resolved
    for part in parts:
        candidate = candidate / str(part)
    candidate_resolved = candidate.resolve()
    if not is_relative_to(candidate_resolved, root_resolved):
        raise ValueError(
            f"path escapes allowed root: {candidate} is outside {root_resolved}"
        )
    return candidate_resolved


def safe_named_child(root: Path, name: object, label: str = "name") -> Path:
    safe_name, error = validate_context_name(name, label)
    if error or safe_name is None:
        raise ValueError(error or f"invalid {label}")
    return safe_child_path(root, safe_name)


def workspace_dir(knowledge_root: Path, workspace: object) -> Path:
    workspaces_root = safe_child_path(knowledge_root, "workspaces")
    return safe_named_child(workspaces_root, workspace, "workspace")


def pack_dir(knowledge_root: Path, pack_name: object) -> Path:
    packs_root = safe_child_path(knowledge_root, "packs")
    return safe_named_child(packs_root, pack_name, "pack")


def block_reason(path: Path) -> str | None:
    """Return a human-readable reason when a path should never be read."""
    parts = [part.lower() for part in path.parts]
    name = path.name.lower()
    suffix = path.suffix.lower()

    for part in parts:
        if part in SECRET_DIR_NAMES:
            return f"secret directory segment `{part}`"
    if name in SECRET_FILE_NAMES:
        return f"secret-like filename `{path.name}`"
    if suffix in SECRET_SUFFIXES:
        return f"secret-like suffix `{suffix}`"
    for pattern in SECRET_CONFIG_PATTERNS:
        if fnmatch.fnmatch(name, pattern):
            return f"secret-like filename pattern `{pattern}`"
    return None


def redact_text(text: str) -> Tuple[str, List[Dict[str, int]]]:
    """Redact suspicious inline secrets and return count metadata."""
    findings: List[Dict[str, int]] = []
    redacted = text

    for kind, pattern, replacement in REDACTION_PATTERNS:
        count = 0

        if kind == "secret_assignment":
            def repl(match: re.Match) -> str:
                nonlocal count
                count += 1
                return f"{match.group(1)}{match.group(2)}<REDACTED-SECRET>"

            redacted = pattern.sub(repl, redacted)
        else:
            redacted, count = pattern.subn(str(replacement), redacted)

        if count:
            findings.append({"kind": kind, "count": count})

    return redacted, findings


def reject_unsafe_entry(raw_entry: str) -> str | None:
    """Validate retrieval-map path syntax before resolving it."""
    value = raw_entry.strip()
    if not value:
        return "empty retrieval path"
    if value.startswith("~"):
        return "home-relative paths are not allowed"
    if Path(value).is_absolute():
        return "absolute paths are not allowed"
    segments = [
        seg for seg in value.replace("\\", "/").split("/")
        if seg and seg not in {"{ws}", "{domain}", "{project}"}
    ]
    if ".." in segments:
        return "parent traversal is not allowed"
    if value.startswith("workspaces/"):
        return "cross-workspace paths must use {ws}/ and stay in the active workspace"
    return None
