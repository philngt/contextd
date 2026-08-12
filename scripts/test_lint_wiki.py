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


def run_lint(wiki_root: Path, workspace: str, extra: list[str] | None = None) -> tuple[int, dict, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--workspace", workspace, "--wiki-root", str(wiki_root)]
        + (extra or []),
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
        (ws / "platform" / "patterns" / "p.md").write_text(
            "---\ntype: Pattern\ntitle: P\ndescription: D\n---\n# p", encoding="utf-8")
        (ws / "platform" / "contracts" / "c.md").write_text(
            "---\ntype: Contract\ntitle: C\ndescription: D\n---\n# c", encoding="utf-8")
        (ws / "workspace.md").write_text("# ws\n[p](patterns-index.md)\n", encoding="utf-8")
        (ws / "patterns-index.md").write_text(
            "# i\n[p](platform/patterns/p.md)\n[c](platform/contracts/c.md)\n",
            encoding="utf-8",
        )
        rc, data, _err = run_lint(root, "clean")
        assert data["summary"] == {"broken": 0, "orphaned": 0, "okf": 0}, data
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


def test_okf_missing_type_warns() -> None:
    """Concept file without frontmatter -> okf warning, exit code 0 (warn-only)."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = root / "workspaces" / "ws"
        (ws / "platform" / "patterns").mkdir(parents=True)
        (ws / "platform" / "patterns" / "p.md").write_text("# p", encoding="utf-8")
        (ws / "workspace.md").write_text("# ws\n[p](platform/patterns/p.md)\n", encoding="utf-8")
        (ws / "patterns-index.md").write_text("# i\n[p](platform/patterns/p.md)\n", encoding="utf-8")
        rc, data, _err = run_lint(root, "ws")
        kinds = [f["kind"] for f in data["okf"]]
        assert "okf_missing_frontmatter" in kinds, kinds
        assert rc == 0, rc


def test_okf_unknown_type_and_bad_status() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = root / "workspaces" / "ws"
        (ws / "platform" / "contracts").mkdir(parents=True)
        (ws / "platform" / "contracts" / "c.md").write_text(
            "---\ntype: TotallyUnknownThing\nstatus: pending\n---\n# c\n",
            encoding="utf-8",
        )
        (ws / "workspace.md").write_text("# ws\n[c](platform/contracts/c.md)\n", encoding="utf-8")
        (ws / "patterns-index.md").write_text("# i\n[c](platform/contracts/c.md)\n", encoding="utf-8")
        rc, data, _err = run_lint(root, "ws")
        kinds = {f["kind"] for f in data["okf"]}
        assert "okf_unknown_type" in kinds, kinds
        assert "okf_bad_status" in kinds, kinds
        assert rc == 0, rc


def test_okf_source_id_unreferenced() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = root / "workspaces" / "ws"
        (ws / "platform" / "contracts").mkdir(parents=True)
        (ws / "platform" / "contracts" / "c.md").write_text(
            "---\ntype: Contract\ntitle: T\ndescription: D\nsources:\n"
            "  - id: used-source\n    resource: https://example.com/a\n"
            "  - id: orphan-source\n    resource: https://example.com/b\n"
            "---\n# T\n\nClaim [^used-source].\n",
            encoding="utf-8",
        )
        (ws / "workspace.md").write_text("# ws\n[c](platform/contracts/c.md)\n", encoding="utf-8")
        (ws / "patterns-index.md").write_text("# i\n[c](platform/contracts/c.md)\n", encoding="utf-8")
        rc, data, _err = run_lint(root, "ws")
        kinds = [(f["kind"], f["detail"]) for f in data["okf"]]
        assert any("orphan-source" in d for k, d in kinds if k == "okf_source_id_unreferenced"), kinds
        assert rc == 0, rc


def test_okf_conformant_clean() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = root / "workspaces" / "ws"
        (ws / "platform" / "contracts").mkdir(parents=True)
        (ws / "platform" / "contracts" / "c.md").write_text(
            "---\ntype: Contract\ntitle: T\ndescription: D\ntags: [a, b]\n"
            "generated: { by: process:test, at: 2026-08-11T00:00:00Z }\n"
            "sources:\n  - id: s1\n    resource: https://example.com/a\n"
            "---\n# T\n\nClaim [^s1].\n",
            encoding="utf-8",
        )
        (ws / "requirements").mkdir(parents=True)
        (ws / "requirements" / "r.md").write_text(
            "---\ntype: Requirement\ntitle: R\ndescription: D\n---\n# R\n",
            encoding="utf-8",
        )
        (ws / "workspace.md").write_text("# ws\n[c](platform/contracts/c.md)\n", encoding="utf-8")
        (ws / "patterns-index.md").write_text("# i\n[c](platform/contracts/c.md)\n", encoding="utf-8")
        rc, data, _err = run_lint(root, "ws")
        assert data["okf"] == [], data["okf"]
        assert rc == 0, rc


def test_okf_skips_index_config_files() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = root / "workspaces" / "ws"
        ws.mkdir(parents=True)
        # Index/config files must not be flagged for missing frontmatter
        for name in ("README.md", "INDEX.md", "_index.md", "patterns-index.md",
                     "workspace.md", "knowledge-map.md"):
            (ws / name).write_text("# x", encoding="utf-8")
        (ws / "patterns-index.md").write_text("# i\n", encoding="utf-8")
        rc, data, _err = run_lint(root, "ws")
        assert data["okf"] == [], data["okf"]
        assert rc == 0, rc


def test_okf_strict_flag_fails() -> None:
    """Same warning with --strict -> exit code 2 (warnings-as-errors)."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = root / "workspaces" / "ws"
        (ws / "platform" / "contracts").mkdir(parents=True)
        (ws / "platform" / "contracts" / "c.md").write_text(
            "---\ntype: TotallyUnknownThing\nstatus: pending\n---\n# c\n",
            encoding="utf-8",
        )
        (ws / "workspace.md").write_text("# ws\n[c](platform/contracts/c.md)\n", encoding="utf-8")
        (ws / "patterns-index.md").write_text("# i\n[c](platform/contracts/c.md)\n", encoding="utf-8")
        rc, data, _err = run_lint(root, "ws", extra=["--strict"])
        assert data["summary"]["okf"] > 0, data
        assert rc == 2, rc


def test_okf_skips_evidence_runtime_artifacts() -> None:
    """Generated evidence artifacts (raw.md, analysis, qa) are not concepts."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = root / "workspaces" / "ws"
        (ws / "evidence" / "sources" / "2026-01-01-code-foo").mkdir(parents=True)
        (ws / "evidence" / "analysis" / "2026-01-01-code-foo").mkdir(parents=True)
        (ws / "evidence" / "qa" / "2026-01-01-code-foo").mkdir(parents=True)
        (ws / "evidence" / "sources" / "2026-01-01-code-foo" / "raw.md").write_text(
            "# Raw\nno frontmatter here", encoding="utf-8")
        (ws / "evidence" / "analysis" / "2026-01-01-code-foo" / "c01-proposals.md").write_text(
            "# c01\nno frontmatter", encoding="utf-8")
        (ws / "evidence" / "qa" / "2026-01-01-code-foo" / "recommendations.md").write_text(
            "# rec\nno frontmatter", encoding="utf-8")
        (ws / "workspace.md").write_text("# ws\n", encoding="utf-8")
        (ws / "patterns-index.md").write_text("# i\n", encoding="utf-8")
        rc, data, _err = run_lint(root, "ws")
        assert data["okf"] == [], data["okf"]
        assert rc == 0, rc


def main() -> int:
    test_broken_and_orphan()
    test_clean_workspace()
    test_orphan_only_exit_code()
    test_okf_missing_type_warns()
    test_okf_unknown_type_and_bad_status()
    test_okf_source_id_unreferenced()
    test_okf_conformant_clean()
    test_okf_skips_index_config_files()
    test_okf_skips_evidence_runtime_artifacts()
    test_okf_strict_flag_fails()
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
