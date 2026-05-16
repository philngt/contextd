#!/usr/bin/env python3
"""
repetition.py - Pure-function helpers for the UserPromptSubmit repetition
detector hook. No I/O side effects (except read_artifact_keywords which only
reads files). Designed for cheap re-execution on every prompt submit (<200ms
budget on a warm filesystem cache).

Concepts:
- observation: { ts, prompt_hash, tokens, prompt_preview }
- cluster: { id, representative_tokens, count, first_seen, last_seen,
             last_hinted_at, member_hashes }

Algorithm:
1. normalize(prompt) -> tokens (lowercased, stopword-stripped)
2. find cluster matching tokens by jaccard >= REP_JACCARD against
   representative_tokens
3. if found: bump count, update last_seen, extend representative tokens (union)
4. else: spawn new cluster

The detector is deliberately small and dumb. Tunables come from env vars so
users can adjust without code edits. No ML, no embeddings — keeps the hook
fast and dependency-free.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Stopwords — Vietnamese + English, intentionally small. Curated for the wiki
# domain (verbs/connectives that don't carry intent signal).
# ---------------------------------------------------------------------------

STOPWORDS: frozenset[str] = frozenset({
    # English
    "a", "an", "the", "and", "or", "but", "if", "then", "of", "in", "on",
    "at", "to", "from", "by", "with", "for", "is", "are", "was", "were",
    "be", "been", "being", "do", "does", "did", "doing", "have", "has",
    "had", "having", "i", "you", "he", "she", "it", "we", "they", "this",
    "that", "these", "those", "my", "your", "his", "her", "its", "our",
    "their", "can", "could", "would", "should", "will", "may", "might",
    "must", "shall", "into", "out", "up", "down", "over", "under", "all",
    "any", "each", "every", "some", "no", "not", "so", "than", "too",
    "very", "just", "also", "as", "about", "what", "which", "who", "whom",
    "where", "when", "why", "how", "please", "give", "show", "make",
    "want", "need", "let", "thanks", "thx", "ok", "okay",
    # Vietnamese
    "và", "hoặc", "nhưng", "nếu", "thì", "của", "trong", "trên", "ở", "tại",
    "đến", "từ", "với", "cho", "là", "có", "không", "được", "phải", "đã",
    "đang", "sẽ", "này", "đó", "kia", "tôi", "bạn", "anh", "chị", "em",
    "họ", "chúng", "ta", "mình", "nó", "ai", "gì", "nào", "đâu", "khi",
    "sao", "vì", "để", "thế", "rồi", "chỉ", "cũng", "đều", "vẫn", "lại",
    "cả", "mà", "thì", "thôi", "nhé", "ạ", "à", "ơi", "ừ", "vâng", "dạ",
    "hãy", "đi", "làm", "cần", "muốn", "biết", "thấy", "ra", "vào", "lên",
    "xuống", "qua", "về", "theo", "như", "giống", "khác", "nhau", "lần",
    "cái", "con", "chiếc", "việc", "điều", "thứ", "người", "nói", "bảo",
    "rất", "hơn", "nhất", "quá", "lắm", "ít", "nhiều", "một", "hai", "ba",
    "đây", "đấy", "ấy", "ờ", "ừm", "à", "thì", "là", "mà", "rằng", "bị",
    "do", "bởi", "nên", "vậy", "thế", "đó", "kia", "này",
})

# Default tunables. Override via env vars.
DEFAULT_JACCARD = 0.6
DEFAULT_MIN_COUNT = 3
DEFAULT_WINDOW_DAYS = 14
DEFAULT_COOLDOWN_HOURS = 6
DEFAULT_HISTORY = 200
DEFAULT_COVERAGE_JACCARD = 0.5
DEFAULT_MAX_CLUSTERS = 50
DEFAULT_GLOBAL_HINT_COOLDOWN_HOURS = 2
DEFAULT_MEMBERS_CAP = 5

# Minimum tokens after stopword removal to bother scoring.
MIN_PROMPT_TOKENS = 3

_WORD_RE = re.compile(r"[a-z0-9À-ỹà-ỹ_]+", re.IGNORECASE)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class Tunables:
    jaccard: float = DEFAULT_JACCARD
    min_count: int = DEFAULT_MIN_COUNT
    window_days: int = DEFAULT_WINDOW_DAYS
    cooldown_hours: int = DEFAULT_COOLDOWN_HOURS
    history: int = DEFAULT_HISTORY
    coverage_jaccard: float = DEFAULT_COVERAGE_JACCARD
    max_clusters: int = DEFAULT_MAX_CLUSTERS
    global_hint_cooldown_hours: int = DEFAULT_GLOBAL_HINT_COOLDOWN_HOURS
    members_cap: int = DEFAULT_MEMBERS_CAP

    @classmethod
    def from_env(cls) -> "Tunables":
        return cls(
            jaccard=_env_float("REP_JACCARD", DEFAULT_JACCARD),
            min_count=_env_int("REP_MIN_COUNT", DEFAULT_MIN_COUNT),
            window_days=_env_int("REP_WINDOW_DAYS", DEFAULT_WINDOW_DAYS),
            cooldown_hours=_env_int("REP_COOLDOWN_HOURS", DEFAULT_COOLDOWN_HOURS),
            history=_env_int("REP_HISTORY", DEFAULT_HISTORY),
            coverage_jaccard=_env_float("REP_COVERAGE_JACCARD", DEFAULT_COVERAGE_JACCARD),
            max_clusters=_env_int("REP_MAX_CLUSTERS", DEFAULT_MAX_CLUSTERS),
            global_hint_cooldown_hours=_env_int(
                "REP_GLOBAL_HINT_COOLDOWN_HOURS",
                DEFAULT_GLOBAL_HINT_COOLDOWN_HOURS,
            ),
            members_cap=_env_int("REP_MEMBERS_CAP", DEFAULT_MEMBERS_CAP),
        )


# ---------------------------------------------------------------------------
# Token / cluster primitives
# ---------------------------------------------------------------------------

def normalize(prompt: str) -> list[str]:
    """Lowercase, tokenize, drop stopwords and 1-char tokens. Order preserved."""
    if not prompt:
        return []
    tokens: list[str] = []
    for raw in _WORD_RE.findall(prompt.lower()):
        if len(raw) < 2:
            continue
        if raw in STOPWORDS:
            continue
        tokens.append(raw)
    return tokens


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8", errors="replace")).hexdigest()[:16]


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_iso(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def cluster_id_for(tokens: list[str]) -> str:
    """Stable id from the top-3 tokens, plus a short hash of the full token set."""
    top = "-".join(tokens[:3]) or "empty"
    digest = hashlib.sha1(" ".join(sorted(set(tokens))).encode("utf-8")).hexdigest()[:6]
    safe = re.sub(r"[^a-z0-9\-]+", "", top.lower())[:32] or "cluster"
    return f"{safe}-{digest}"


# ---------------------------------------------------------------------------
# Cluster update — the core scoring step
# ---------------------------------------------------------------------------

@dataclass
class Cluster:
    id: str
    representative_tokens: list[str]
    count: int = 0
    first_seen: str = ""
    last_seen: str = ""
    last_hinted_at: str = ""
    members: list[str] = field(default_factory=list)  # prompt_hashes

    def to_dict(self, members_cap: int = DEFAULT_MEMBERS_CAP) -> dict:
        return {
            "id": self.id,
            "representative_tokens": self.representative_tokens,
            "count": self.count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "last_hinted_at": self.last_hinted_at,
            "members": self.members[-members_cap:] if members_cap > 0 else [],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Cluster":
        return cls(
            id=d["id"],
            representative_tokens=list(d.get("representative_tokens", [])),
            count=int(d.get("count", 0)),
            first_seen=d.get("first_seen", ""),
            last_seen=d.get("last_seen", ""),
            last_hinted_at=d.get("last_hinted_at", ""),
            members=list(d.get("members", [])),
        )


def prune_old_clusters(
    clusters: list[Cluster], window_days: int, now: datetime | None = None
) -> list[Cluster]:
    """Drop clusters whose last_seen is older than window_days."""
    if now is None:
        now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)
    kept: list[Cluster] = []
    for c in clusters:
        last = _parse_iso(c.last_seen)
        if last and last >= cutoff:
            kept.append(c)
    return kept


def cap_clusters_lru(
    clusters: list[Cluster], max_clusters: int
) -> tuple[list[Cluster], list[Cluster]]:
    """If clusters exceed cap, drop the least-recently-seen.

    Returns (kept, evicted). High-count clusters tie-break in favor of keeping.
    """
    if len(clusters) <= max_clusters:
        return clusters, []
    # Sort: most recent first; ties broken by higher count.
    def _key(c: Cluster) -> tuple[str, int]:
        return (c.last_seen or "", c.count)
    sorted_c = sorted(clusters, key=_key, reverse=True)
    return sorted_c[:max_clusters], sorted_c[max_clusters:]


def assign_to_cluster(
    tokens: list[str],
    prompt_h: str,
    clusters: list[Cluster],
    tun: Tunables,
    now_ts: str | None = None,
) -> tuple[Cluster, bool]:
    """Find best-match cluster or create new one. Returns (cluster, is_new)."""
    if now_ts is None:
        now_ts = now_iso()

    best: Cluster | None = None
    best_score = 0.0
    for c in clusters:
        score = jaccard(tokens, c.representative_tokens)
        if score >= tun.jaccard and score > best_score:
            best, best_score = c, score

    if best is None:
        new = Cluster(
            id=cluster_id_for(tokens),
            representative_tokens=list(dict.fromkeys(tokens))[:20],
            count=1,
            first_seen=now_ts,
            last_seen=now_ts,
            members=[prompt_h],
        )
        clusters.append(new)
        return new, True

    best.count += 1
    best.last_seen = now_ts
    best.members.append(prompt_h)
    # Extend representative tokens with union, keep order, cap at 20.
    seen = set(best.representative_tokens)
    for t in tokens:
        if t not in seen:
            best.representative_tokens.append(t)
            seen.add(t)
            if len(best.representative_tokens) >= 20:
                break
    return best, False


def should_hint(
    cluster: Cluster,
    tun: Tunables,
    suppressed_ids: set[str],
    now: datetime | None = None,
) -> bool:
    """Decide whether to surface a hint for this cluster on this turn."""
    if cluster.id in suppressed_ids:
        return False
    if cluster.count < tun.min_count:
        return False
    if now is None:
        now = datetime.now(timezone.utc)
    last_hint = _parse_iso(cluster.last_hinted_at)
    if last_hint and (now - last_hint) < timedelta(hours=tun.cooldown_hours):
        return False
    return True


# ---------------------------------------------------------------------------
# Artifact inventory — load known skills/commands/agents to suppress hints
# that would just point at something already wired up.
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL
)
_DESC_RE = re.compile(r"^description:\s*(.+?)\s*$", re.MULTILINE)
_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)


def _extract_md_keywords(text: str) -> tuple[str, set[str]]:
    """Return (name, keyword_set) from a markdown file with front-matter."""
    m = _FRONTMATTER_RE.match(text)
    fm = m.group(1) if m else text[:500]
    name_m = _NAME_RE.search(fm)
    desc_m = _DESC_RE.search(fm)
    name = name_m.group(1).strip() if name_m else ""
    desc = desc_m.group(1).strip() if desc_m else ""
    # Keywords come from name + description tokens (already normalized).
    kw = set(normalize(name + " " + desc))
    return name, kw


def load_artifact_keywords(
    wiki_root: Path, workspace: str | None
) -> dict[str, set[str]]:
    """Scan known artifact locations for name + description tokens.

    Returns {artifact_label: token_set}. artifact_label = "{kind}:{name}".
    Errors on individual files are swallowed (we'd rather show false hints
    than crash the hook).
    """
    out: dict[str, set[str]] = {}
    locations: list[tuple[str, Path, str]] = [
        ("command", wiki_root / ".claude" / "commands", "*.md"),
        ("agent", wiki_root / ".claude" / "agents", "*.md"),
    ]
    # Pack-level artifacts.
    packs_dir = wiki_root / "packs"
    if packs_dir.is_dir():
        for pack in packs_dir.iterdir():
            if not pack.is_dir():
                continue
            locations.append(("pack-agent", pack / "agents", "*.md"))
            locations.append(("pack-command", pack / ".claude" / "commands", "*.md"))
            locations.append(("pack-skill", pack / "skills", "*.md"))
    # Workspace-level overrides.
    if workspace:
        ws_dir = wiki_root / "workspaces" / workspace
        locations.append(("ws-agent", ws_dir / "agents", "*.md"))
        locations.append(("ws-command", ws_dir / ".claude" / "commands", "*.md"))

    for kind, root, glob in locations:
        if not root.is_dir():
            continue
        for path in root.glob(glob):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            name, kw = _extract_md_keywords(text)
            if not kw:
                continue
            label = f"{kind}:{name or path.stem}"
            out[label] = kw
    return out


def cluster_covered_by(
    cluster: Cluster,
    artifact_keywords: dict[str, set[str]],
    threshold: float,
) -> str | None:
    """If any artifact matches cluster tokens by jaccard >= threshold, return its label."""
    rep = set(cluster.representative_tokens)
    if not rep:
        return None
    best_label = None
    best_score = threshold
    for label, kw in artifact_keywords.items():
        score = jaccard(rep, kw)
        if score >= best_score:
            best_label, best_score = label, score
    return best_label


# ---------------------------------------------------------------------------
# Hint message construction
# ---------------------------------------------------------------------------

def build_hint(cluster: Cluster, tun: Tunables) -> str:
    """One-line hint, < 120 chars. Keep terse to minimize per-turn token cost."""
    theme = " ".join(cluster.representative_tokens[:3]) or "?"
    return (
        f"[rep] '{cluster.id}' x{cluster.count} ({theme}) "
        f"-> /suggest-automation {cluster.id}"
    )


# ---------------------------------------------------------------------------
# Tiny perf helper — caller can budget itself.
# ---------------------------------------------------------------------------

def perf_now_ms() -> float:
    return time.monotonic() * 1000.0


__all__ = [
    "STOPWORDS",
    "Tunables",
    "Cluster",
    "MIN_PROMPT_TOKENS",
    "normalize",
    "prompt_hash",
    "jaccard",
    "now_iso",
    "cluster_id_for",
    "prune_old_clusters",
    "cap_clusters_lru",
    "assign_to_cluster",
    "should_hint",
    "load_artifact_keywords",
    "cluster_covered_by",
    "build_hint",
    "perf_now_ms",
]
