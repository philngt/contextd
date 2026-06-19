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
