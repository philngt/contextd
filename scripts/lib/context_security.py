#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small stdlib-only safety helpers for contextd runtime reads."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
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
WINDOWS_RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    *(f"com{idx}" for idx in range(1, 10)),
    *(f"lpt{idx}" for idx in range(1, 10)),
}

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
    except (OSError, RuntimeError, ValueError):
        return False


def _resolved(path: Path, label: str) -> Path:
    try:
        return path.resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"could not resolve {label}: {exc}") from exc


def root_relative_posix(path: Path, root: Path) -> str:
    """Return a canonical root-relative POSIX path, never an absolute fallback."""
    root_resolved = _resolved(Path(root), "root")
    path_resolved = _resolved(Path(path), "path")
    try:
        return path_resolved.relative_to(root_resolved).as_posix()
    except ValueError as exc:
        raise ValueError(
            f"path is outside allowed root: {path_resolved} is outside {root_resolved}"
        ) from exc


def _relative_path_reason(relative: str) -> str | None:
    if not relative:
        return "must not be empty"
    if "\x00" in relative:
        return "must not contain NUL bytes"
    if any(ord(char) < 32 for char in relative):
        return "must not contain control characters"
    if relative.startswith("~"):
        return "home-relative paths are not allowed"

    posix_path = PurePosixPath(relative)
    windows_path = PureWindowsPath(relative)
    if posix_path.is_absolute():
        return "absolute paths are not allowed"
    if windows_path.is_absolute() or windows_path.drive or windows_path.root:
        return "Windows drive, rooted, and UNC paths are not allowed"
    if "\\" in relative:
        return "backslash path separators are not allowed"
    if ":" in relative:
        return "drive, URI, and alternate-stream separators are not allowed"

    segments = relative.split("/")
    if ".." in segments:
        return "parent traversal is not allowed"
    if "." in segments:
        return "current-directory path segments are not allowed"
    for segment in segments:
        if not segment:
            continue
        if segment.endswith((".", " ")):
            return "path segments must not end with a dot or space"
        if segment.split(".", 1)[0].lower() in WINDOWS_RESERVED_NAMES:
            return "Windows reserved device path segments are not allowed"
    return None


def confined_child(
    root: Path,
    relative: str | Path,
    label: str = "path",
    allow_symlink: bool = True,
) -> Path:
    """Resolve one portable relative child and require exact root confinement.

    ``allow_symlink=False`` additionally rejects a symlink/junction/alias in any
    child component. The supplied root is the trust boundary and may itself be
    a caller-selected canonical path.
    """
    if isinstance(relative, Path):
        raw_relative = relative.as_posix()
    elif isinstance(relative, str):
        raw_relative = relative
    else:
        raise ValueError(f"{label} must be a string or Path")

    reason = _relative_path_reason(raw_relative)
    if reason:
        raise ValueError(f"invalid {label}: {reason}")

    root_resolved = _resolved(Path(root), f"{label} root")
    candidate = root_resolved.joinpath(*PurePosixPath(raw_relative).parts)
    candidate_resolved = _resolved(candidate, label)
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(
            f"{label} escapes allowed root: {candidate} is outside {root_resolved}"
        ) from exc

    if not allow_symlink and candidate_resolved != candidate:
        raise ValueError(f"{label} must not contain symlink or junction aliases")
    return candidate_resolved


def validate_context_name(value: object, label: str = "name") -> Tuple[str | None, str | None]:
    """Validate workspace/pack identifiers before using them as path segments."""
    if not isinstance(value, str):
        return None, f"{label} must be a string"
    name = value.strip()
    if not name:
        return None, f"{label} must not be empty"
    if name != value:
        return None, f"{label} must not contain surrounding whitespace"
    if "\x00" in name:
        return None, f"{label} must not contain NUL bytes"
    if name in {".", ".."} or ".." in name:
        return None, f"{label} must not contain parent traversal"
    if "/" in name or "\\" in name:
        return None, f"{label} must not contain path separators"
    if ":" in name:
        return None, f"{label} must not contain drive or URI separators"
    if name.endswith("."):
        return None, f"{label} must not end with a dot"
    if name.split(".", 1)[0].lower() in WINDOWS_RESERVED_NAMES:
        return None, f"{label} must not use a Windows reserved device name"
    if not SAFE_CONTEXT_NAME_RE.fullmatch(name):
        return None, (
            f"{label} must start with a letter, digit, or '_' and contain only "
            "letters, digits, '.', '_', and '-'"
        )
    return name, None


def safe_child_path(root: Path, *parts: object) -> Path:
    """Resolve a child path and require it to stay under root after symlinks."""
    if not parts:
        return _resolved(Path(root), "root")
    rendered_parts = [
        part.as_posix() if isinstance(part, Path) else str(part)
        for part in parts
    ]
    return confined_child(root, "/".join(rendered_parts))


def safe_named_child(root: Path, name: object, label: str = "name") -> Path:
    safe_name, error = validate_context_name(name, label)
    if error or safe_name is None:
        raise ValueError(error or f"invalid {label}")
    return confined_child(root, safe_name, label, allow_symlink=False)


def workspace_dir(knowledge_root: Path, workspace: object) -> Path:
    workspaces_root = confined_child(
        knowledge_root, "workspaces", "workspaces root", allow_symlink=False
    )
    return safe_named_child(workspaces_root, workspace, "workspace")


def pack_dir(knowledge_root: Path, pack_name: object) -> Path:
    packs_root = confined_child(
        knowledge_root, "packs", "packs root", allow_symlink=False
    )
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


def _raw_evidence_reason(path: Path) -> str | None:
    parts = [part.lower() for part in path.parts]
    return (
        "raw evidence source path `evidence/sources`"
        if any(
            parts[idx] == "evidence" and parts[idx + 1] == "sources"
            for idx in range(len(parts) - 1)
        )
        else None
    )


def _single_path_policy_reason(path: Path) -> str | None:
    return block_reason(path) or _raw_evidence_reason(path)


def path_policy_reason(
    path: Path,
    *,
    logical_path: Path | None = None,
) -> str | None:
    """Check secret/raw-evidence policy on logical and canonical path forms."""
    logical = Path(logical_path) if logical_path is not None else Path(path)
    logical_reason = _single_path_policy_reason(logical)
    if logical_reason:
        prefix = "logical path: " if logical_path is not None else ""
        return prefix + logical_reason

    try:
        resolved = Path(path).resolve()
    except (OSError, RuntimeError) as exc:
        return f"unresolvable path: {type(exc).__name__}: {exc}"
    resolved_reason = _single_path_policy_reason(resolved)
    if resolved_reason:
        return f"resolved target: {resolved_reason}"
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
    if not isinstance(raw_entry, str):
        return "retrieval path must be a string"
    value = raw_entry.strip()
    if not value:
        return "empty retrieval path"
    unsafe = _relative_path_reason(value)
    if unsafe:
        return unsafe
    if value.startswith("workspaces/"):
        return "cross-workspace paths must use {ws}/ and stay in the active workspace"
    return None
