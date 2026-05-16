#!/usr/bin/env python3
"""
Self-contained tests for lint-wiki.py — uses tmp dirs only, never touches real wiki content.

Run:
    python scripts/test_lint_wiki.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "lint-wiki.py"


def make_fake_wiki(root: Path, ws_name: str = "fixture-ws") -> Path:
    """Build a minimal fake wiki tree with a known set of broken/orphan issues."""
    ws = root / "workspaces" / ws_name
    (ws / "platform" / "patterns").mkdir(parents=True)
    (ws / "platform" / "contracts").mkdir(parents=True)
    (ws / "projects" / "svc-a").mkdir(parents=True)
    (ws / "domains" / "x").mkdir(parents=True)

    # Existing pattern + contract + domain
    (ws / "platform" / "patterns" / "good.md").write_text("# good", encoding="utf-8")
    (ws / "platform" / "patterns" / "orphan-pattern.md").write_text(
        "# orphan", encoding="utf-8"
    )
    (ws / "platform" / "contracts" / "good-contract.md").write_text("# c", encoding="utf-8")
    (ws / "domains" / "x" / "workflow.md").write_text("# wf", encoding="utf-8")

    (ws / "workspace.md").write_text(
        "# WS\n[contracts](platform/contracts/)\n[patterns](patterns-index.md)\n",
        encoding="utf-8",
    )

    # patterns-index references one missing file (broken) and skips orphan-pattern.md
    (ws / "patterns-index.md").write_text(
        "# Index\n"
        "[good](platform/patterns/good.md)\n"
        "[contract](platform/contracts/good-contract.md)\n"
        "[missing](platform/patterns/does-not-exist.md)\n"
        "[external](https://example.com/x.md)\n"
        "[anchor](#section)\n",
        encoding="utf-8",
    )

    # knowledge-map references workflow + a missing service
    (ws / "projects" / "svc-a" / "knowledge-map.md").write_text(
        "# KM\n"
        "[wf](../../domains/x/workflow.md)\n"
        "[svc](./services/missing.md)\n",
        encoding="utf-8",
    )
    return ws


def run_lint(wiki_root: Path, workspace: str) -> tuple[int, dict, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--workspace", workspace, "--wiki-root", str(wiki_root)],
        capture_output=True, text=True,
    )
    data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, data, proc.stderr


def test_broken_and_orphan() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_fake_wiki(root)
        rc, data, _err = run_lint(root, "fixture-ws")

        # Expect 2 broken links: does-not-exist.md and ./services/missing.md
        targets = sorted(b["target"] for b in data["broken_links"])
        assert "platform/patterns/does-not-exist.md" in targets, targets
        assert "./services/missing.md" in targets, targets
        assert data["summary"]["broken"] == 2, data

        # Expect 1 orphan: orphan-pattern.md
        orphan_files = [o["file"] for o in data["orphans"]]
        assert any("orphan-pattern.md" in f for f in orphan_files), orphan_files
        assert data["summary"]["orphaned"] == 1, data

        # Exit code 1 because broken links present
        assert rc == 1, rc


def test_clean_workspace() -> None:
    """Build a wiki where everything resolves cleanly."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = root / "workspaces" / "clean"
        (ws / "platform" / "patterns").mkdir(parents=True)
        (ws / "platform" / "contracts").mkdir(parents=True)
        (ws / "platform" / "patterns" / "p.md").write_text("# p", encoding="utf-8")
        (ws / "platform" / "contracts" / "c.md").write_text("# c", encoding="utf-8")
        (ws / "workspace.md").write_text("# ws\n[p](patterns-index.md)\n", encoding="utf-8")
        (ws / "patterns-index.md").write_text(
            "# i\n[p](platform/patterns/p.md)\n[c](platform/contracts/c.md)\n",
            encoding="utf-8",
        )
        rc, data, _err = run_lint(root, "clean")
        assert data["summary"] == {"broken": 0, "orphaned": 0}, data
        assert rc == 0, rc


def test_orphan_only_exit_code() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = root / "workspaces" / "orph"
        (ws / "platform" / "patterns").mkdir(parents=True)
        (ws / "platform" / "patterns" / "lonely.md").write_text("# l", encoding="utf-8")
        (ws / "workspace.md").write_text("# ws\n[idx](patterns-index.md)\n", encoding="utf-8")
        (ws / "patterns-index.md").write_text("# i\n", encoding="utf-8")
        rc, data, _err = run_lint(root, "orph")
        assert data["summary"]["broken"] == 0, data
        assert data["summary"]["orphaned"] == 1, data
        assert rc == 2, rc


def main() -> int:
    test_broken_and_orphan()
    test_clean_workspace()
    test_orphan_only_exit_code()
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
