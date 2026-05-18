#!/usr/bin/env python3
"""
test_detect_repetition.py - Unit tests for the repetition detector.

Run:
    python scripts/test_detect_repetition.py

Tests:
    1. normalize() drops stopwords + short tokens
    2. jaccard() basic correctness
    3. assign_to_cluster() creates new cluster on first prompt
    4. assign_to_cluster() merges similar prompts into one cluster
    5. should_hint() respects min_count + cooldown + suppression
    6. cluster_covered_by() suppresses hint when an artifact already matches
    7. End-to-end: 3 similar prompts via the hook entrypoint produce a hint
       on the 3rd call (when no covering artifact exists in the workspace)
    8. Slash-command prompts are ignored
    9. Missing wiki.json -> silent (no output, exit 0)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.repetition import (  # noqa: E402
    Cluster,
    Tunables,
    assign_to_cluster,
    cap_clusters_lru,
    cluster_covered_by,
    jaccard,
    normalize,
    now_iso,
    should_hint,
)


HOOK_SCRIPT = HERE / "detect_repetition.py"


# ---------------------------------------------------------------------------
# Pure-function tests
# ---------------------------------------------------------------------------

def test_normalize_drops_stopwords():
    toks = normalize("Please rebase the wiki sau khi merge nhé")
    assert "please" not in toks, toks
    assert "the" not in toks
    assert "nhé" not in toks  # confirmed Vietnamese stopword
    assert "rebase" in toks and "wiki" in toks and "merge" in toks
    print("  ok normalize_drops_stopwords")


def test_normalize_short_input():
    assert normalize("") == []
    assert normalize("a b c") == []  # all 1-char
    print("  ok normalize_short_input")


def test_jaccard():
    assert jaccard([], []) == 0.0
    assert jaccard(["a"], ["a"]) == 1.0
    assert abs(jaccard(["a", "b"], ["b", "c"]) - 1 / 3) < 1e-9
    print("  ok jaccard")


def test_assign_creates_new():
    tun = Tunables()
    clusters: list[Cluster] = []
    toks = normalize("rebase wiki sau khi merge xong")
    c, is_new = assign_to_cluster(toks, "h1", clusters, tun)
    assert is_new and c.count == 1 and len(clusters) == 1
    print("  ok assign_creates_new")


def test_assign_merges_similar():
    tun = Tunables(jaccard=0.4)
    clusters: list[Cluster] = []
    a = normalize("rebase wiki merge code")
    b = normalize("rebase lai wiki merge")
    c = normalize("rebase wiki merge code review")
    assign_to_cluster(a, "h1", clusters, tun)
    assign_to_cluster(b, "h2", clusters, tun)
    assign_to_cluster(c, "h3", clusters, tun)
    assert len(clusters) == 1, [cl.representative_tokens for cl in clusters]
    assert clusters[0].count == 3
    print("  ok assign_merges_similar")


def test_should_hint_min_count():
    tun = Tunables(min_count=3)
    cl = Cluster(id="x", representative_tokens=["a"], count=2,
                 first_seen=now_iso(), last_seen=now_iso())
    assert not should_hint(cl, tun, set())
    cl.count = 3
    assert should_hint(cl, tun, set())
    print("  ok should_hint_min_count")


def test_should_hint_suppressed():
    tun = Tunables(min_count=3)
    cl = Cluster(id="x", representative_tokens=["a"], count=5,
                 first_seen=now_iso(), last_seen=now_iso())
    assert not should_hint(cl, tun, {"x"})
    print("  ok should_hint_suppressed")


def test_should_hint_cooldown():
    tun = Tunables(min_count=3, cooldown_hours=6)
    recent = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds")
    cl = Cluster(id="x", representative_tokens=["a"], count=5,
                 first_seen=now_iso(), last_seen=now_iso(),
                 last_hinted_at=recent)
    assert not should_hint(cl, tun, set())
    old = (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat(timespec="seconds")
    cl.last_hinted_at = old
    assert should_hint(cl, tun, set())
    print("  ok should_hint_cooldown")


def test_cluster_covered_by():
    cl = Cluster(id="x", representative_tokens=["rebase", "wiki", "merge"],
                 count=4, first_seen=now_iso(), last_seen=now_iso())
    artifact_kw = {
        "command:contextd-rebase": {"rebase", "wiki", "sync", "merge"},
        "command:unrelated": {"foo", "bar"},
    }
    label = cluster_covered_by(cl, artifact_kw, 0.5)
    assert label == "command:contextd-rebase", label

    # No coverage when overlap is low.
    cl2 = Cluster(id="y", representative_tokens=["deploy", "kubernetes", "rollout"],
                  count=4, first_seen=now_iso(), last_seen=now_iso())
    assert cluster_covered_by(cl2, artifact_kw, 0.5) is None
    print("  ok cluster_covered_by")


def test_cap_clusters_lru_keeps_most_recent():
    from datetime import datetime, timedelta, timezone
    base = datetime.now(timezone.utc)
    clusters = []
    for i in range(10):
        clusters.append(Cluster(
            id=f"c{i}",
            representative_tokens=[f"t{i}"],
            count=1,
            first_seen=(base - timedelta(days=i)).isoformat(timespec="seconds"),
            last_seen=(base - timedelta(days=i)).isoformat(timespec="seconds"),
        ))
    kept, evicted = cap_clusters_lru(clusters, max_clusters=3)
    assert len(kept) == 3 and len(evicted) == 7
    kept_ids = sorted(c.id for c in kept)
    assert kept_ids == ["c0", "c1", "c2"], kept_ids
    print("  ok cap_clusters_lru_keeps_most_recent")


def test_cap_clusters_lru_noop_below_cap():
    clusters = [
        Cluster(id="a", representative_tokens=["x"], count=1,
                first_seen=now_iso(), last_seen=now_iso()),
    ]
    kept, evicted = cap_clusters_lru(clusters, max_clusters=10)
    assert len(kept) == 1 and evicted == []
    print("  ok cap_clusters_lru_noop_below_cap")


def test_hint_text_is_short():
    """Per-turn token cost — hint must stay terse (<120 chars)."""
    from lib.repetition import build_hint
    cl = Cluster(
        id="contextd-rebase-merge-a1b2c3",
        representative_tokens=["rebase", "wiki", "merge", "code", "review"],
        count=7, first_seen=now_iso(), last_seen=now_iso(),
    )
    tun = Tunables()
    hint = build_hint(cl, tun)
    assert len(hint) < 120, f"hint too long ({len(hint)} chars): {hint}"
    assert "/suggest-automation" in hint
    print(f"  ok hint_text_is_short (len={len(hint)})")


# ---------------------------------------------------------------------------
# End-to-end hook tests
# ---------------------------------------------------------------------------

def _run_hook(payload: dict, cwd: Path, extra_env: dict | None = None) -> tuple[str, str, int]:
    """Invoke detect_repetition.py as a subprocess. Returns (stdout, stderr, rc)."""
    env = os.environ.copy()
    env["REP_MIN_COUNT"] = "3"
    env["REP_JACCARD"] = "0.4"
    env["REP_COOLDOWN_HOURS"] = "0"  # disable per-cluster cooldown for tests
    env["REP_GLOBAL_HINT_COOLDOWN_HOURS"] = "0"  # disable global cap by default
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        cwd=str(cwd),
    )
    return proc.stdout, proc.stderr, proc.returncode


def _setup_workspace(tmp: Path, workspace_name: str = "_test-ws") -> Path:
    """Build a minimal wiki-template-shaped tree under tmp."""
    (tmp / ".claude").mkdir(parents=True)
    (tmp / ".claude" / "wiki.json").write_text(
        json.dumps({"workspace": workspace_name, "wiki_root": "."}),
        encoding="utf-8",
    )
    (tmp / "workspaces" / workspace_name).mkdir(parents=True)
    return tmp


def test_e2e_three_similar_prompts_emit_hint():
    with tempfile.TemporaryDirectory() as td:
        root = _setup_workspace(Path(td))
        prompts = [
            "rebase wiki merge code review",
            "rebase wiki merge code",
            "rebase wiki merge review",
        ]
        last_stdout = ""
        stderr = ""
        for p in prompts:
            stdout, stderr, rc = _run_hook({"prompt": p, "cwd": str(root)}, root)
            assert rc == 0, f"rc={rc} stderr={stderr}"
            last_stdout = stdout

        # 3rd call should emit hint (no covering artifact in empty repo).
        assert last_stdout.strip(), f"expected hint on 3rd call, got empty. stderr={stderr}"
        payload = json.loads(last_stdout)
        ctx = payload["hookSpecificOutput"]["additionalContext"]
        assert ctx.startswith("[rep]") and "/suggest-automation" in ctx, ctx
        print("  ok e2e_three_similar_prompts_emit_hint")


def test_e2e_slash_command_ignored():
    with tempfile.TemporaryDirectory() as td:
        root = _setup_workspace(Path(td))
        for _ in range(5):
            stdout, _, rc = _run_hook(
                {"prompt": "/foo bar baz quux", "cwd": str(root)}, root
            )
            assert rc == 0 and stdout.strip() == ""
        print("  ok e2e_slash_command_ignored")


def test_e2e_missing_wiki_json_silent():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        stdout, _, rc = _run_hook(
            {"prompt": "rebase wiki sau merge code xong",
             "cwd": str(root)}, root,
        )
        assert rc == 0 and stdout.strip() == ""
        print("  ok e2e_missing_wiki_json_silent")


def test_e2e_global_cooldown_caps_second_cluster():
    """After cluster A fires a hint, cluster B in the same window stays silent."""
    with tempfile.TemporaryDirectory() as td:
        root = _setup_workspace(Path(td))
        # Promote cluster A
        for p in ["rebase wiki merge code review",
                  "rebase wiki merge code",
                  "rebase wiki merge review"]:
            out_a, _, rc = _run_hook({"prompt": p, "cwd": str(root)}, root,
                                     extra_env={"REP_GLOBAL_HINT_COOLDOWN_HOURS": "6"})
            assert rc == 0
        assert out_a.strip(), "cluster A should have emitted hint"

        # Different theme — 3 prompts should normally fire, but global cap blocks.
        last_out_b = ""
        for p in ["deploy staging kubernetes pod",
                  "deploy staging kubernetes",
                  "deploy staging kubernetes rollout"]:
            last_out_b, _, rc = _run_hook(
                {"prompt": p, "cwd": str(root)}, root,
                extra_env={"REP_GLOBAL_HINT_COOLDOWN_HOURS": "6"},
            )
            assert rc == 0
        assert last_out_b.strip() == "", (
            f"global cooldown should have silenced cluster B, got: {last_out_b!r}"
        )
        print("  ok e2e_global_cooldown_caps_second_cluster")


def test_e2e_covered_by_artifact():
    """If a workspace command already covers the cluster, no hint should fire."""
    with tempfile.TemporaryDirectory() as td:
        root = _setup_workspace(Path(td))
        # Install a workspace-level slash command whose description matches.
        ws_cmd_dir = root / "workspaces" / "_test-ws" / ".claude" / "commands"
        ws_cmd_dir.mkdir(parents=True)
        (ws_cmd_dir / "contextd-rebase.md").write_text(
            "---\nname: contextd-rebase\ndescription: rebase wiki sau khi merge code\n---\n",
            encoding="utf-8",
        )
        prompts = [
            "rebase wiki merge code review",
            "rebase wiki merge code",
            "rebase wiki merge review",
        ]
        last_stdout = ""
        for p in prompts:
            last_stdout, _, rc = _run_hook({"prompt": p, "cwd": str(root)}, root)
            assert rc == 0
        assert last_stdout.strip() == "", (
            f"expected silent (covered by artifact), got: {last_stdout!r}"
        )
        print("  ok e2e_covered_by_artifact")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run() -> int:
    tests = [
        test_normalize_drops_stopwords,
        test_normalize_short_input,
        test_jaccard,
        test_assign_creates_new,
        test_assign_merges_similar,
        test_should_hint_min_count,
        test_should_hint_suppressed,
        test_should_hint_cooldown,
        test_cluster_covered_by,
        test_cap_clusters_lru_keeps_most_recent,
        test_cap_clusters_lru_noop_below_cap,
        test_hint_text_is_short,
        test_e2e_three_similar_prompts_emit_hint,
        test_e2e_slash_command_ignored,
        test_e2e_missing_wiki_json_silent,
        test_e2e_global_cooldown_caps_second_cluster,
        test_e2e_covered_by_artifact,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}", file=sys.stderr)
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}", file=sys.stderr)
            failed += 1
    if failed:
        print(f"\n{failed} test(s) failed", file=sys.stderr)
        return 1
    print(f"\nAll {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(run())
