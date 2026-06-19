#!/usr/bin/env python3
"""
detect_repetition.py - UserPromptSubmit hook entrypoint.

Reads the hook payload from stdin, normalizes the user's prompt, assigns it
to a cluster of prior prompts in the active workspace, and emits a JSON
hookSpecificOutput.additionalContext when a recurring pattern is detected
that isn't already covered by an existing skill / command / agent / pack.

Design doc: agents/pipeline/repetition-detection.md.

Hard rules:
- NEVER blocks the user. All errors -> exit 0. Errors go to stderr only.
- NEVER reads/writes outside <knowledge_root>/workspaces/<active>/.observations/.
- Self-budget ~800ms; bails out early if exceeded.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.atomic_write import (  # noqa: E402
    LockTimeout,
    atomic_write_json,
    with_advisory_lock,
)
from lib import contextd_resolver  # noqa: E402
from lib.repetition import (  # noqa: E402
    MIN_PROMPT_TOKENS,
    Cluster,
    Tunables,
    assign_to_cluster,
    build_hint,
    cap_clusters_lru,
    cluster_covered_by,
    load_artifact_keywords,
    normalize,
    now_iso,
    prompt_hash,
    prune_old_clusters,
    should_hint,
)
from datetime import timedelta  # noqa: E402

SELF_BUDGET_MS = 800
ARTIFACT_CACHE_TTL_S = 60.0
PROMPTS_LOG_MAX_BYTES = 1_000_000   # ~1 MB
PROMPTS_LOG_KEEP_DAYS = 30

# Module-scope artifact cache (lives for one process, cleared by Claude Code
# each invocation since hooks are short-lived subprocesses; the TTL is there
# in case a future caller keeps the process warm).
_ARTIFACT_CACHE: dict[tuple[str, str], tuple[float, dict[str, set[str]]]] = {}


def warn(msg: str) -> None:
    print(f"[detect_repetition] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Workspace resolution — canonical contextd resolver.
# ---------------------------------------------------------------------------


def resolve_workspace(cwd: Path) -> tuple[Path, str] | None:
    """Return (knowledge_root, workspace_name) or None if not resolvable."""
    resolved = contextd_resolver.resolve(cwd)
    workspace = resolved.get("workspace")
    root = resolved.get("knowledge_root") or resolved.get("wiki_root")
    if not isinstance(workspace, str) or not workspace.strip() or not root:
        return None
    wiki_root = Path(str(root)).resolve()
    if not wiki_root or not wiki_root.is_dir():
        return None
    return wiki_root, workspace.strip()


# ---------------------------------------------------------------------------
# State files
# ---------------------------------------------------------------------------

def obs_dir(wiki_root: Path, workspace: str) -> Path:
    return wiki_root / "workspaces" / workspace / ".observations"


def load_clusters(path: Path) -> list[Cluster]:
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        warn(f"clusters.json unreadable, starting fresh: {e}")
        return []
    items = raw.get("clusters") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []
    out: list[Cluster] = []
    for d in items:
        if isinstance(d, dict) and "id" in d:
            try:
                out.append(Cluster.from_dict(d))
            except (KeyError, TypeError, ValueError):
                continue
    return out


def save_clusters(
    path: Path,
    clusters: list[Cluster],
    *,
    members_cap: int,
    last_hint_emitted_at: str = "",
) -> None:
    payload = {
        "stage": "observations",
        "updated_at": now_iso(),
        "last_hint_emitted_at": last_hint_emitted_at,
        "clusters": [c.to_dict(members_cap=members_cap) for c in clusters],
    }
    atomic_write_json(path, payload)


def load_clusters_with_meta(path: Path) -> tuple[list[Cluster], str]:
    """Return (clusters, last_hint_emitted_at)."""
    if not path.is_file():
        return [], ""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        warn(f"clusters.json unreadable: {e}")
        return [], ""
    if not isinstance(raw, dict):
        return load_clusters(path), ""
    items = raw.get("clusters", [])
    clusters: list[Cluster] = []
    if isinstance(items, list):
        for d in items:
            if isinstance(d, dict) and "id" in d:
                try:
                    clusters.append(Cluster.from_dict(d))
                except (KeyError, TypeError, ValueError):
                    continue
    last_hint = raw.get("last_hint_emitted_at", "") or ""
    return clusters, last_hint


def archive_clusters(path: Path, evicted: list[Cluster]) -> None:
    """Append evicted clusters to a sibling archive JSONL. Best-effort."""
    if not evicted:
        return
    archive = path.with_name("clusters.archive.jsonl")
    try:
        with open(archive, "a", encoding="utf-8") as f:
            for c in evicted:
                f.write(json.dumps(c.to_dict(members_cap=0), ensure_ascii=False) + "\n")
    except OSError as e:
        warn(f"failed to archive {len(evicted)} clusters: {e}")


def load_suppressions(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    ids = raw.get("dismissed") if isinstance(raw, dict) else raw
    if not isinstance(ids, list):
        return set()
    return {str(x) for x in ids if isinstance(x, (str, int))}


def append_observation(path: Path, record: dict) -> None:
    """Append a single JSON line. Best-effort; never raises."""
    line = json.dumps(record, ensure_ascii=False)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as e:
        warn(f"failed to append {path}: {e}")


def maybe_trim_prompts_log(path: Path) -> None:
    """If prompts.jsonl exceeds PROMPTS_LOG_MAX_BYTES, drop entries older than
    PROMPTS_LOG_KEEP_DAYS. Best-effort; never raises.

    This runs at most once per hook invocation and is cheap because we only
    check os.stat first.
    """
    try:
        size = path.stat().st_size
    except OSError:
        return
    if size < PROMPTS_LOG_MAX_BYTES:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=PROMPTS_LOG_KEEP_DAYS)
    cutoff_iso = cutoff.isoformat(timespec="seconds")
    tmp = path.with_suffix(path.suffix + ".trim.tmp")
    kept = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as src, \
                open(tmp, "w", encoding="utf-8") as dst:
            for line in src:
                line = line.rstrip("\n")
                if not line:
                    continue
                # Cheap prefix check before json.loads — `ts` is the first field.
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = rec.get("ts") or ""
                if ts >= cutoff_iso:
                    dst.write(line + "\n")
                    kept += 1
        os.replace(str(tmp), str(path))
        warn(f"trimmed {path.name}: kept {kept} entries newer than {PROMPTS_LOG_KEEP_DAYS}d")
    except OSError as e:
        warn(f"trim failed for {path}: {e}")
        try:
            tmp.unlink()
        except OSError:
            pass


def cached_artifact_keywords(
    wiki_root: Path, workspace: str
) -> dict[str, set[str]]:
    key = (str(wiki_root), workspace)
    now = time.monotonic()
    entry = _ARTIFACT_CACHE.get(key)
    if entry and (now - entry[0]) < ARTIFACT_CACHE_TTL_S:
        return entry[1]
    kw = load_artifact_keywords(wiki_root, workspace)
    _ARTIFACT_CACHE[key] = (now, kw)
    return kw


# ---------------------------------------------------------------------------
# Output — emit hookSpecificOutput per Claude Code hook contract.
# ---------------------------------------------------------------------------

def emit_hint(text: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": text,
        }
    }
    print(json.dumps(payload, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> int:
    started_ms = time.monotonic() * 1000.0

    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        warn(f"hook payload not JSON: {e}")
        return 0

    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return 0
    if prompt.strip().startswith("/"):
        # Slash commands are explicit user intent already — skip detection.
        return 0

    cwd = Path(payload.get("cwd") or os.getcwd())
    resolved = resolve_workspace(cwd)
    if not resolved:
        return 0
    wiki_root, workspace = resolved

    tokens = normalize(prompt)
    if len(tokens) < MIN_PROMPT_TOKENS:
        return 0

    tun = Tunables.from_env()
    base = obs_dir(wiki_root, workspace)
    prompts_log = base / "prompts.jsonl"
    clusters_file = base / "clusters.json"
    suppressions_file = base / "suppressions.json"

    p_hash = prompt_hash(prompt)
    ts = now_iso()

    append_observation(
        prompts_log,
        {
            "ts": ts,
            "prompt_hash": p_hash,
            "tokens": tokens[:40],
            "prompt_preview": prompt[:120],
            "cwd": str(cwd),
        },
    )
    maybe_trim_prompts_log(prompts_log)

    # Budget check #1
    if (time.monotonic() * 1000.0 - started_ms) > SELF_BUDGET_MS:
        return 0

    try:
        with with_advisory_lock(clusters_file, timeout_ms=400):
            clusters, last_hint_emitted_at = load_clusters_with_meta(clusters_file)
            clusters = prune_old_clusters(clusters, tun.window_days)
            cluster, _is_new = assign_to_cluster(tokens, p_hash, clusters, tun, ts)
            suppressed = load_suppressions(suppressions_file)

            hint_text: str | None = None

            # Global per-turn cap: at most 1 hint per global cooldown window,
            # across ALL clusters. Prevents 5+ hints stacking in one session.
            now_dt = datetime.now(timezone.utc)
            last_global = None
            if last_hint_emitted_at:
                try:
                    last_global = datetime.fromisoformat(
                        last_hint_emitted_at.replace("Z", "+00:00")
                    )
                except ValueError:
                    last_global = None
            global_cooldown_ok = (
                last_global is None
                or (now_dt - last_global) >= timedelta(
                    hours=tun.global_hint_cooldown_hours
                )
            )

            if global_cooldown_ok and should_hint(cluster, tun, suppressed):
                artifact_kw = cached_artifact_keywords(wiki_root, workspace)
                covered_by = cluster_covered_by(cluster, artifact_kw, tun.coverage_jaccard)
                if covered_by:
                    # Existing artifact already targets this intent — stay silent.
                    # Don't bump last_hinted_at so we can revisit if user keeps deviating.
                    pass
                else:
                    cluster.last_hinted_at = ts
                    hint_text = build_hint(cluster, tun)
                    last_hint_emitted_at = ts

            # LRU cap to keep clusters.json bounded.
            kept, evicted = cap_clusters_lru(clusters, tun.max_clusters)
            archive_clusters(clusters_file, evicted)

            save_clusters(
                clusters_file,
                kept,
                members_cap=tun.members_cap,
                last_hint_emitted_at=last_hint_emitted_at,
            )
    except LockTimeout:
        warn("clusters.json lock contention - skipping update")
        return 0
    except OSError as e:
        warn(f"clusters.json update failed: {e}")
        return 0

    if hint_text:
        emit_hint(hint_text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # never let exceptions reach Claude Code
        warn(f"unhandled error: {e}")
        sys.exit(0)
