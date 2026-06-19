#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime-neutral contextd tests.

Run:
    python scripts/test_contextd_runtime.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "lib"))

import cmd_resolve  # noqa: E402
from lib import contextd_resolver, task_context_engine  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _workspace(root: Path, name: str = "default") -> Path:
    ws = root / "workspaces" / name
    _write(ws / "workspace.md", "# Workspace\n\n## Packs\n\n- pack-demo\n")
    _write(ws / "platform" / "contracts" / "contract-index.json",
           json.dumps({"contracts": {"demo.v1": "demo.contract.json"}}))
    _write(ws / "platform" / "contracts" / "demo.contract.json",
           '{"title":"demo"}\n')
    _write(ws / "platform" / "contracts" / "citation-format.md",
           "# Contract: citation-format\n\n## Rule\n\nCite things.\n")
    _write(ws / "platform" / "patterns" / "demo-pattern.md",
           "# Pattern: demo-pattern\n\n## Flow\n\nDo it.\n\n## Default Config\n\nnone\n\n## Failure Strategy\n\nStop.\n\n## Implementation Rules\n\nStay deterministic.\n")
    _write(ws / "projects" / "app" / "knowledge-map.md",
           "# Knowledge Map\n\n## Purpose\n\nDemo app.\n")
    _write(ws / "runbooks" / "README.md", "# Runbooks\n")
    _write(ws / "platform" / "architecture" / "README.md", "# Architecture\n")
    return ws


def _pack(root: Path) -> None:
    _write(root / "packs" / "pack-demo" / "pack.yaml",
           "name: pack-demo\nversion: 1.0.0\nkeywords:\n  demo: [demo, sample]\n")
    _write(root / "packs" / "pack-demo" / "agents" / "common-pitfalls.md",
           "# Common Pitfalls\n\n## Rules\n\nDo not guess.\n")


def test_contextd_config_wins() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root, "canonical")
        _workspace(root, "legacy")
        _write(root / ".contextd" / "config.json",
               json.dumps({"workspace": "canonical", "knowledge_root": "."}))
        _write(root / ".claude" / "wiki.json",
               json.dumps({"workspace": "legacy", "wiki_root": "."}))
        resolved = contextd_resolver.resolve(root)
        assert resolved["workspace"] == "canonical", resolved
        assert resolved["config_kind"] == "contextd", resolved
        assert any("Ignoring lower-priority config" in w for w in resolved["warnings"])
        print("  ok contextd_config_wins")


def test_legacy_claude_still_resolves() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root, "legacy")
        _write(root / ".claude" / "wiki.json",
               json.dumps({"workspace": "legacy", "wiki_root": "."}))
        resolved = contextd_resolver.resolve(root)
        assert resolved["workspace"] == "legacy", resolved
        assert resolved["knowledge_root"] == str(root.resolve())
        assert resolved["config_kind"] == "claude-legacy"
        print("  ok legacy_claude_still_resolves")


def test_pack_override_replace_semantics() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root, "default")
        _write(root / ".contextd" / "config.json",
               json.dumps({"workspace": "default", "knowledge_root": ".", "packs": []}))
        resolved = contextd_resolver.resolve(root)
        assert resolved["packs"] == [], resolved
        assert resolved["pack_source"] == "config"
        print("  ok pack_override_replace_semantics")


def test_missing_workspace_lists_available() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root, "available")
        _write(root / ".contextd" / "config.json",
               json.dumps({"workspace": "missing", "knowledge_root": "."}))
        resolved = contextd_resolver.resolve(root, require_workspace=True)
        assert resolved["error"] == "missing-workspace-dir", resolved
        assert any("Available workspaces: available" in w for w in resolved["warnings"])
        print("  ok missing_workspace_lists_available")


def test_context_artifact_and_materialized_pack() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack(root)
        artifact = task_context_engine.build_context_artifact(
            task="Implement demo feature",
            wiki_root=root,
            workspace="default",
            packs=["pack-demo"],
            project_dir=root,
        )
        assert artifact["artifact_type"] == "contextd_task_context.v1"
        assert artifact["intent"]["components"] == ["demo"]
        assert artifact["referenced_docs"], artifact
        assert all(doc["path"].startswith("workspaces/default/") or doc["path"].startswith("packs/")
                   for doc in artifact["referenced_docs"])
        assert any(doc["path"] == "workspaces/default/workspace.md"
                   for doc in artifact["static_context"])
        assert any(doc["path"] == "packs/pack-demo/pack.yaml"
                   for doc in artifact["static_context"])
        assert any(doc["path"].endswith("demo.contract.json")
                   for doc in artifact["referenced_docs"])
        first_key = artifact["contextPack"]["packKey"]
        materialized = task_context_engine.materialize_context(artifact, root)
        assert materialized["contextPack"]["status"] == "materialized"
        assert (root / ".contextd" / "context" / "current-task.json").is_file()
        assert (root / materialized["contextPack"]["compiledRef"]).is_file()
        pack_text = (root / materialized["contextPack"]["compiledRef"]).read_text(encoding="utf-8")
        assert "workspaces/default/workspace.md" in pack_text
        assert "packs/pack-demo/pack.yaml" in pack_text

        artifact_again = task_context_engine.build_context_artifact(
            task="Implement demo feature",
            wiki_root=root,
            workspace="default",
            packs=["pack-demo"],
            project_dir=root,
        )
        assert artifact_again["contextPack"]["packKey"] == first_key

        _write(root / "workspaces" / "default" / "platform" / "patterns" / "demo-pattern.md",
               "# Pattern: demo-pattern\n\n## Flow\n\nChanged.\n")
        changed = task_context_engine.build_context_artifact(
            task="Implement demo feature",
            wiki_root=root,
            workspace="default",
            packs=["pack-demo"],
            project_dir=root,
        )
        assert changed["contextPack"]["packKey"] != first_key
        print("  ok context_artifact_and_materialized_pack")


def test_contract_index_missing_target_is_gap() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _write(root / "workspaces" / "default" / "platform" / "contracts" / "contract-index.json",
               json.dumps({"contracts": {"missing.v1": "missing.contract.json"}}))
        artifact = task_context_engine.build_context_artifact(
            task="Implement demo feature",
            wiki_root=root,
            workspace="default",
            packs=[],
            project_dir=root,
        )
        assert any(g["category"] == "contract-index" and g["blocking_hint"]
                   for g in artifact["gaps"]), artifact["gaps"]
        print("  ok contract_index_missing_target_is_gap")


def test_contract_path_index_and_fallback() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        path, warnings = task_context_engine.resolve_contract_path("demo.v1", root, "default", [])
        assert path and path.name == "demo.contract.json", (path, warnings)
        fallback, warnings = task_context_engine.resolve_contract_path("citation-format", root, "default", [])
        assert fallback and fallback.name == "citation-format.md", (fallback, warnings)
        print("  ok contract_path_index_and_fallback")


def test_cli_smoke() -> None:
    commands = [
        [sys.executable, "-m", "scripts.cli", "resolve", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "find", "citation", "--limit", "1", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "context", "design context", "--format", "json", "--no-materialize"],
        [sys.executable, "-m", "scripts.cli", "contract-path", "citation-format", "--format", "json"],
    ]
    with tempfile.TemporaryDirectory() as td:
        commands.append([
            sys.executable, "-m", "scripts.cli", "export", "--runtime", "cursor", "--output", td,
        ])
        for cmd in commands:
            proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
            assert proc.returncode == 0, (cmd, proc.stdout, proc.stderr)
    print("  ok cli_smoke")


def run() -> int:
    tests = [
        test_contextd_config_wins,
        test_legacy_claude_still_resolves,
        test_pack_override_replace_semantics,
        test_missing_workspace_lists_available,
        test_context_artifact_and_materialized_pack,
        test_contract_index_missing_target_is_gap,
        test_contract_path_index_and_fallback,
        test_cli_smoke,
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"  FAIL {test.__name__}: {e}", file=sys.stderr)
            failed += 1
        except Exception as e:
            print(f"  ERROR {test.__name__}: {type(e).__name__}: {e}", file=sys.stderr)
            failed += 1
    if failed:
        print(f"\n{failed} test(s) failed", file=sys.stderr)
        return 1
    print(f"\nAll {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(run())
