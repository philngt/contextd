#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime-neutral contextd tests.

Run:
    python scripts/test_contextd_runtime.py
"""

from __future__ import annotations

from collections import Counter
import json
import contextlib
import hashlib
import io
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import cmd_doctor  # noqa: E402
import cmd_eval  # noqa: E402
import cmd_migrate_config  # noqa: E402
import generate_manifest  # noqa: E402
import cmd_resolve  # noqa: E402
import render_runtime  # noqa: E402
import test_pack_devops_iac  # noqa: E402
from lib import (  # noqa: E402
    contextd_resolver,
    contextd_version,
    pack_validation,
    synapse_engine,
    task_context_engine,
)


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
           "name: pack-demo\nversion: 1.0.0\ndescription: Demo pack\ncomponents:\n  - demo\nkeywords:\n  demo: [demo, sample]\n")
    _write(root / "packs" / "pack-demo" / "agents" / "common-pitfalls.md",
           "# Common Pitfalls\n\n## Rules\n\nDo not guess.\n")
    _write(root / "packs" / "pack-demo" / "agents" / "pipeline" / "retrieval-map.md",
           "# Retrieval Map\n\n| Component | Docs to retrieve |\n|---|---|\n| `demo` | platform/contracts/, platform/patterns/ |\n")


def _pack_v3(root: Path, name: str = "pack-demo-v3") -> None:
    pack = root / "packs" / name
    _write(
        pack / "pack.yaml",
        "manifest_version: 3\n"
        f"name: {name}\n"
        "version: 0.1.0\n"
        "description: Canonical component-scoped guidance for deterministic runtime tests.\n"
        "status: experimental\n"
        "category: engineering\n"
        "reviewed_on: 2025-01-01\n"
        "audiences: [engineering]\n"
        "task_types: [implement_feature, review]\n"
        "scope_includes: [demo component guidance]\n"
        "scope_excludes: [unrelated production guidance]\n"
        "components:\n  - demo-v3\n  - unused-v3\n"
        "keywords:\n"
        "  demo-v3: [demo-v3, demo canonical, scoped demo]\n"
        "  unused-v3: [unused-v3, dormant canonical, unrelated scoped demo]\n"
        "retrieval:\n"
        "  demo-v3: [platform/contracts/, platform/patterns/]\n"
        "  unused-v3: [platform/architecture/]\n"
        "files:\n"
        "  knowledge: knowledge.md\n"
        "  validator_script: scripts/rules.py\n"
        "conflicts_with: []\n",
    )
    _write(
        pack / "knowledge.md",
        f"# {name} — Canonical Knowledge\n\n"
        "## Global Principles\n\n"
        f"- `{name}-evidence-first` — Use inspected evidence.\n\n"
        "## Component: demo-v3\n\n"
        "### Mental Model\n\nRoute only demo knowledge.\n\n"
        "### Standards\n\n"
        f"- `{name}-demo-standard` — Keep the demo bounded.\n\n"
        "### Failure Signals\n\n- Unbounded demo context.\n\n"
        "### Evidence And Stop Conditions\n\nStop when evidence is missing.\n\n"
        "## Component: unused-v3\n\n"
        "### Mental Model\n\nThis section must stay unloaded.\n\n"
        "### Standards\n\n"
        f"- `{name}-unused-standard` — Never leak dormant guidance.\n\n"
        "### Failure Signals\n\n- Unrelated context was loaded.\n\n"
        "### Evidence And Stop Conditions\n\nStop when routing is unrelated.\n",
    )
    _write(
        pack / "README.md",
        f"# {name}\n\n"
        "## When to enable\n\n- Demo-v3 tasks.\n\n"
        "## When not to enable\n\n- Unrelated tasks.\n\n"
        "## Retrieval behavior\n\nRoutes by component.\n\n"
        "## Verification\n\nRun pack-validate.\n",
    )
    _write(pack / "scripts" / "rules.py", "RULES = []\n")


def _pack_with_retrieval(root: Path, name: str, keywords: dict, rows: dict) -> None:
    keyword_lines = []
    for component, words in keywords.items():
        rendered = ", ".join(words)
        keyword_lines.append(f"  {component}: [{rendered}]")
    _write(root / "packs" / name / "pack.yaml",
           f"name: {name}\nversion: 1.0.0\nkeywords:\n" + "\n".join(keyword_lines) + "\n")
    table = ["# Retrieval Map", "", "| Component | Docs to retrieve |", "|---|---|"]
    for component, docs in rows.items():
        table.append(f"| `{component}` | {docs} |")
    _write(root / "packs" / name / "agents" / "pipeline" / "retrieval-map.md",
           "\n".join(table) + "\n")
    _write(root / "packs" / name / "agents" / "common-pitfalls.md",
           "# Common Pitfalls\n\n## Rules\n\nUse the right context.\n")


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
        _write(
            root / "agents" / "coding-rules.md",
            "# Engine Coding Rules\n\nKeep demo code deterministic.\n",
        )
        _write(
            root / "workspaces" / "default" / "agents" / "constraints.md",
            "# Workspace Constraints\n\n- `ws-demo-rule` — Keep demo local.\n",
        )
        original_builder = task_context_engine.synapse_engine.build_synapse_snapshot
        with mock.patch.object(
            task_context_engine.synapse_engine,
            "build_synapse_snapshot",
            wraps=original_builder,
        ) as build_spy:
            artifact, synapse_snapshot = task_context_engine.build_context_snapshot(
                task="Implement demo feature",
                wiki_root=root,
                workspace="default",
                packs=["pack-demo"],
                project_dir=root,
            )
            materialized = task_context_engine.materialize_context(
                artifact,
                root,
                synapse_snapshot=synapse_snapshot,
            )
            assert build_spy.call_count == 1, "materialization rescanned the workspace"
        assert artifact["artifact_type"] == "contextd_task_context.v1"
        assert artifact["intent"]["components"] == ["demo"]
        assert artifact["referenced_docs"], artifact
        assert all(doc["path"].startswith("workspaces/default/") or doc["path"].startswith("packs/")
                   for doc in artifact["referenced_docs"])
        assert any(doc["path"] == "workspaces/default/workspace.md"
                   for doc in artifact["static_context"])
        assert any(doc["path"] == "packs/pack-demo/pack.yaml"
                   for doc in artifact["static_context"])
        assert any(doc["path"] == "agents/coding-rules.md"
                   for doc in artifact["static_context"])
        assert any(
            doc["path"] == "workspaces/default/agents/constraints.md"
            and doc["category"] == "workspace-rule"
            for doc in artifact["static_context"]
        )
        assert any(doc["path"].endswith("demo.contract.json")
                   for doc in artifact["referenced_docs"])
        first_key = artifact["contextPack"]["packKey"]
        assert materialized["contextPack"]["status"] == "materialized"
        assert (root / ".contextd" / "context" / "current-task.json").is_file()
        assert (root / ".contextd" / "context" / "synapse.json").is_file()
        assert materialized["synapse"]["status"] == "materialized"
        assert materialized["context_projection"]["memory_class"] == "context"
        persisted = json.loads(
            (root / ".contextd" / "context" / "current-task.json").read_text(
                encoding="utf-8",
            )
        )
        assert persisted == materialized, "returned and canonical persisted artifacts diverged"
        assert (root / materialized["contextPack"]["compiledRef"]).is_file()
        assert not list((root / ".contextd" / "context").rglob("*.tmp.*"))
        pack_text = (root / materialized["contextPack"]["compiledRef"]).read_text(encoding="utf-8")
        assert "workspaces/default/workspace.md" in pack_text
        assert "packs/pack-demo/pack.yaml" in pack_text

        no_snapshot_dir = root / "no-snapshot-output"
        with mock.patch.object(
            task_context_engine.synapse_engine,
            "build_synapse_snapshot",
            side_effect=AssertionError("materialization must not build synapse"),
        ):
            without_synapse = task_context_engine.materialize_context(
                artifact,
                no_snapshot_dir,
            )
        assert without_synapse["synapse"]["status"] == "not_materialized"
        assert without_synapse["synapse"]["ref"] is None
        assert not (no_snapshot_dir / ".contextd" / "context" / "synapse.json").exists()

        rematerialized_dir = root / "rematerialized-without-snapshot"
        rematerialized = task_context_engine.materialize_context(
            materialized,
            rematerialized_dir,
        )
        assert rematerialized["synapse"]["status"] == "not_materialized"
        assert rematerialized["synapse"]["ref"] is None
        assert not (
            rematerialized_dir / ".contextd" / "context" / "synapse.json"
        ).exists()

        mismatched_snapshot = json.loads(json.dumps(synapse_snapshot))
        mismatched_snapshot["synapse_hash"] = "0" * 64
        mismatch_dir = root / "mismatch-output"
        mismatch = task_context_engine.materialize_context(
            artifact,
            mismatch_dir,
            synapse_snapshot=mismatched_snapshot,
        )
        assert mismatch["synapse"]["status"] == "drifted"
        assert mismatch["synapse"]["ref"] is None
        assert not (mismatch_dir / ".contextd" / "context" / "synapse.json").exists()
        assert any("snapshot does not match" in warning for warning in mismatch["warnings"])

        mutated_snapshot = json.loads(json.dumps(synapse_snapshot))
        mutated_snapshot["nodes"][0]["title"] = "Mutated after build"
        mutation_dir = root / "mutation-output"
        mutation = task_context_engine.materialize_context(
            artifact,
            mutation_dir,
            synapse_snapshot=mutated_snapshot,
        )
        assert mutation["synapse"]["status"] == "drifted"
        assert not (mutation_dir / ".contextd" / "context" / "synapse.json").exists()

        inconsistent_artifact = json.loads(json.dumps(artifact))
        selected_path = inconsistent_artifact["referenced_docs"][0]["path"]
        inconsistent_artifact["source_hashes"][selected_path] = "f" * 64
        inconsistent_dir = root / "inconsistent-output"
        inconsistent = task_context_engine.materialize_context(
            inconsistent_artifact,
            inconsistent_dir,
            synapse_snapshot=synapse_snapshot,
        )
        assert inconsistent["synapse"]["status"] == "drifted"
        assert not (
            inconsistent_dir / ".contextd" / "context" / "synapse.json"
        ).exists()

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


def test_context_snapshot_source_coherence_and_raw_hashes() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = _workspace(root)
        target = ws / "platform" / "patterns" / "racy.md"
        late = ws / "platform" / "patterns" / "late.md"
        old_text = "# Racy\n\nOld unique-race guidance.\n"
        new_text = "# Racy\n\nNew unique-race guidance changed during build.\n"
        _write(target, old_text)

        original_builder = task_context_engine.synapse_engine.build_synapse_snapshot

        def build_then_change(*args, **kwargs):
            build = original_builder(*args, **kwargs)
            target.write_text(new_text, encoding="utf-8")
            late.write_text(
                "# Late\n\nNew unique-late guidance created after the scan.\n",
                encoding="utf-8",
            )
            return build

        with mock.patch.object(
            task_context_engine.synapse_engine,
            "build_synapse_snapshot",
            side_effect=build_then_change,
        ):
            artifact, snapshot = task_context_engine.build_context_snapshot(
                task="review unique-race and unique-late guidance",
                wiki_root=root,
                workspace="default",
                packs=[],
                project_dir=root,
                synapse_as_of=date(2026, 8, 20),
            )

        rel = "workspaces/default/platform/patterns/racy.md"
        node = synapse_engine.nodes_by_path(snapshot)[rel]
        selected = next(doc for doc in artifact["referenced_docs"] if doc["path"] == rel)
        assert selected["source_hash"] == node["source_hash"]
        assert selected["content"] == old_text.strip()
        assert not any(
            doc["path"] == "workspaces/default/platform/patterns/late.md"
            for doc in artifact["referenced_docs"]
        )
        assert target.read_text(encoding="utf-8") == new_text
        coherent = task_context_engine.materialize_context(
            artifact,
            root / "coherent-output",
            synapse_snapshot=snapshot,
        )
        assert coherent["synapse"]["status"] == "materialized"

        crlf = ws / "platform" / "patterns" / "crlf.md"
        raw = (
            b"---\r\n"
            b"type: Pattern\r\n"
            b"node_id: pattern.crlf\r\n"
            b"---\r\n"
            b"# CRLF\r\n"
        )
        crlf.write_bytes(raw)
        graph = synapse_engine.build_synapse_index(
            root,
            "default",
            as_of=date(2026, 8, 20),
        )
        crlf_node = synapse_engine.nodes_by_id(graph)["pattern.crlf"]
        assert crlf_node["source_hash"] == hashlib.sha256(raw).hexdigest()

        reads: list[Path] = []
        original_read_bytes = Path.read_bytes
        original_read_text = Path.read_text

        def count_bytes(path: Path, *args, **kwargs):
            reads.append(path.resolve())
            return original_read_bytes(path, *args, **kwargs)

        def count_text(path: Path, *args, **kwargs):
            reads.append(path.resolve())
            return original_read_text(path, *args, **kwargs)

        with mock.patch.object(Path, "read_bytes", count_bytes), mock.patch.object(
            Path,
            "read_text",
            count_text,
        ):
            task_context_engine.build_context_snapshot(
                task="review workspace knowledge",
                wiki_root=root,
                workspace="default",
                packs=[],
                project_dir=root,
                synapse_as_of=date(2026, 8, 20),
            )
        workspace_reads = [path for path in reads if path.is_relative_to(ws.resolve())]
        counts = Counter(workspace_reads)
        assert counts and max(counts.values()) == 1, counts
        print("  ok context_snapshot_source_coherence_and_raw_hashes")


def test_materialization_rejects_foreign_knowledge_root() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        roots = [base / "company-a", base / "company-b"]
        for root in roots:
            _workspace(root)

        artifact, snapshot_a = task_context_engine.build_context_snapshot(
            task="review demo pattern",
            wiki_root=roots[0],
            workspace="default",
            packs=[],
            project_dir=roots[0],
            synapse_as_of=date(2026, 8, 20),
        )
        snapshot_b = synapse_engine.build_synapse_index(
            roots[1],
            "default",
            as_of=date(2026, 8, 20),
        )
        assert snapshot_a["synapse_hash"] == snapshot_b["synapse_hash"]

        output = base / "foreign-output"
        materialized = task_context_engine.materialize_context(
            artifact,
            output,
            synapse_snapshot=snapshot_b,
        )
        assert materialized["synapse"]["status"] == "drifted"
        assert not (output / ".contextd" / "context" / "synapse.json").exists()
        print("  ok materialization_rejects_foreign_knowledge_root")


def test_synapse_lookups_are_reused_for_replacement_expansion() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = _workspace(root)
        _write(
            ws / "platform" / "patterns" / "old.md",
            """---
type: Pattern
lifecycle: superseded
node_id: pattern.old
---
# Old
""",
        )
        _write(
            ws / "platform" / "patterns" / "new.md",
            """---
type: Pattern
status: stable
node_id: pattern.new
relations:
  - type: supersedes
    target: pattern.old
---
# New
""",
        )

        original_lookups = synapse_engine.build_synapse_lookups
        with mock.patch.object(
            synapse_engine,
            "build_synapse_lookups",
            wraps=original_lookups,
        ) as lookup_spy, mock.patch.object(
            synapse_engine,
            "replacement_node_ids",
            side_effect=AssertionError("context expansion rebuilt replacement indexes"),
        ):
            artifact = task_context_engine.build_context_artifact(
                task="review old pattern",
                wiki_root=root,
                workspace="default",
                packs=[],
                project_dir=root,
                synapse_as_of=date(2026, 8, 20),
            )
        assert lookup_spy.call_count == 1
        selected = {doc["path"] for doc in artifact["referenced_docs"]}
        assert "workspaces/default/platform/patterns/new.md" in selected
        print("  ok synapse_lookups_are_reused_for_replacement_expansion")


def test_lib_modules_have_one_canonical_identity() -> None:
    assert task_context_engine.synapse_engine is synapse_engine
    assert task_context_engine.context_policy.__name__ == "lib.context_policy"
    assert "synapse_engine" not in sys.modules
    assert "task_context_engine" not in sys.modules
    print("  ok lib_modules_have_one_canonical_identity")


def test_synapse_lifecycle_graph() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = _workspace(root)
        _write(
            ws / "platform" / "patterns" / "old-timeout.md",
            """---
type: Pattern
title: Old timeout
status: deprecated
lifecycle: superseded
node_id: pattern.timeout.v1
review_by: 2025-01-01
---
# Old timeout
""",
        )
        _write(
            ws / "platform" / "patterns" / "new-timeout.md",
            """---
type: Pattern
title: New timeout
status: stable
node_id: pattern.timeout.v2
freshness: fresh
relations:
  - type: supersedes
    target: pattern.timeout.v1
---
# New timeout
""",
        )
        _write(ws / ".observations" / "prompts.jsonl", '{"prompt":"secret runtime state"}\n')
        _write(ws / "evidence" / "sources" / "raw" / "raw.md", "# Raw payload\n")
        _write(ws / "notes" / "a b.md", "# Space path\n")
        _write(ws / "notes" / "a.b.md", "# Dot path\n")

        first = synapse_engine.build_synapse_index(
            root, "default", as_of=date(2026, 1, 1),
        )
        second = synapse_engine.build_synapse_index(
            root, "default", as_of=date(2026, 1, 1),
        )
        assert first["synapse_hash"] == second["synapse_hash"]
        nodes = synapse_engine.nodes_by_id(first)
        assert len(nodes) == len(first["nodes"]), "path-derived node IDs must be unique"
        assert nodes["pattern.timeout.v1"]["lifecycle"] == "superseded"
        assert nodes["pattern.timeout.v1"]["freshness"] == "stale"
        assert nodes["pattern.timeout.v2"]["freshness"] == "fresh"
        assert all(".observations" not in node["path"] for node in first["nodes"])
        assert all("evidence/sources" not in node["path"] for node in first["nodes"])
        assert {
            (edge["type"], edge["source"], edge["target"])
            for edge in first["edges"]
        } >= {("supersedes", "pattern.timeout.v2", "pattern.timeout.v1")}
        output = synapse_engine.materialize_synapse(first, root)
        assert output == root / ".contextd" / "context" / "synapse.json"
        assert json.loads(output.read_text(encoding="utf-8"))["synapse_hash"] == first["synapse_hash"]
        print("  ok synapse_lifecycle_graph")


def test_synapse_rejects_invalid_edges_and_workspace_escape() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = _workspace(root)
        _write(
            ws / "platform" / "patterns" / "a.md",
            """---
type: Pattern
node_id: pattern.a
relations:
  - type: supersedes
    target: pattern.b
  - type: supports
    target: workspace://other/pattern.foreign
  - type: supports
    target: pattern.missing
---
# A
""",
        )
        _write(
            ws / "platform" / "patterns" / "b.md",
            """---
type: Pattern
node_id: pattern.b
relations:
  - type: supersedes
    target: pattern.a
---
# B
""",
        )
        graph = synapse_engine.build_synapse_index(
            root, "default", as_of=date(2026, 1, 1),
        )
        codes = {item["code"] for item in graph["diagnostics"]}
        assert "cross-workspace-edge" in codes, graph["diagnostics"]
        assert "dangling-edge" in codes, graph["diagnostics"]
        assert "supersede-cycle" in codes, graph["diagnostics"]
        assert not [edge for edge in graph["edges"] if edge["type"] == "supersedes"]

        escaped = synapse_engine.build_synapse_index(
            root, "../other", as_of=date(2026, 1, 1),
        )
        assert escaped["nodes"] == []
        assert any(item["code"] == "invalid-workspace" for item in escaped["diagnostics"])
        _write(
            root / ".contextd" / "config.json",
            json.dumps({"workspace": "../other", "knowledge_root": "."}),
        )
        resolved = contextd_resolver.resolve(root, require_workspace=True)
        assert resolved["error"] == "invalid-workspace", resolved
        assert resolved["workspace_dir"] is None, resolved
        try:
            task_context_engine.build_context_artifact(
                task="implement escape",
                wiki_root=root,
                workspace="../other",
                packs=[],
            )
            raise AssertionError("context build accepted workspace traversal")
        except ValueError as exc:
            assert "context build refused" in str(exc), exc
        print("  ok synapse_rejects_invalid_edges_and_workspace_escape")


def test_context_projection_expands_replacement_and_warns_stale() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ws = _workspace(root)
        _write(
            ws / "platform" / "contracts" / "legacy-timeout.md",
            """---
type: Contract
status: deprecated
lifecycle: superseded
node_id: contract.timeout.v1
freshness: stale
---
# Legacy timeout

Legacy timeout behavior.
""",
        )
        _write(
            ws / "platform" / "contracts" / "replacements" / "current-timeout.md",
            """---
type: Contract
status: stable
node_id: contract.timeout.v2
freshness: fresh
relations:
  - type: supersedes
    target: contract.timeout.v1
---
# Current timeout

Current timeout behavior replaces legacy timeout.
""",
        )
        artifact = task_context_engine.build_context_artifact(
            task="implement legacy timeout behavior",
            wiki_root=root,
            workspace="default",
            packs=[],
            project_dir=root,
            include_selection_trace=True,
            synapse_as_of=date(2026, 1, 1),
        )
        selected = {doc["path"]: doc for doc in artifact["referenced_docs"]}
        replacement_path = (
            "workspaces/default/platform/contracts/replacements/current-timeout.md"
        )
        legacy_path = "workspaces/default/platform/contracts/legacy-timeout.md"
        assert replacement_path in selected, selected
        assert selected[replacement_path]["synapse_expansion"]["reason"] == "active_replacement"
        assert legacy_path in selected, selected
        assert any("Selected stale knowledge node contract.timeout.v1" in warning
                   for warning in artifact["warnings"]), artifact["warnings"]
        assert artifact["synapse"]["artifact_type"] == "contextd_synapse_ref.v1"
        assert artifact["context_projection"]["source_synapse_hash"] == artifact["synapse"]["synapse_hash"]
        trace = artifact["_selection_trace"]["selected_docs"]
        legacy_trace = next(item for item in trace if item["path"] == legacy_path)
        assert legacy_trace["state_score_adjustment"] == -20, legacy_trace
        print("  ok context_projection_expands_replacement_and_warns_stale")


def test_budget_report_and_explain_trace() -> None:
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
        again = task_context_engine.build_context_artifact(
            task="Implement demo feature",
            wiki_root=root,
            workspace="default",
            packs=["pack-demo"],
            project_dir=root,
        )
        assert "budget_report" in artifact, artifact
        assert "_selection_trace" not in artifact, artifact
        assert artifact["budget_report"] == again["budget_report"]
        assert artifact["budget_report"]["selected_docs"] == len(artifact["referenced_docs"])
        assert artifact["budget_report"]["static_docs"] == len(artifact["static_context"])
        assert artifact["budget_report"]["estimated_tokens_referenced"] == (
            artifact["budget_report"]["estimated_tokens_selected"]
        )
        assert artifact["budget_report"]["estimated_tokens_static"] > 0
        assert artifact["budget_report"]["estimated_tokens_total"] >= (
            artifact["budget_report"]["estimated_tokens_referenced"]
        )

        explanation = task_context_engine.build_context_explanation(
            task="Implement demo feature",
            wiki_root=root,
            workspace="default",
            packs=["pack-demo"],
            project_dir=root,
        )
        assert explanation["artifact_type"] == "contextd_context_explanation.v1"
        assert explanation["selection_trace"]["selected_docs"], explanation
        assert explanation["summary"]["budget_report"] == artifact["budget_report"]
        print("  ok budget_report_and_explain_trace")


def test_manifest_v3_scopes_pack_knowledge_and_budget() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack_v3(root)
        artifact = task_context_engine.build_context_artifact(
            task="Implement demo-v3 feature with canonical guidance",
            wiki_root=root,
            workspace="default",
            packs=["pack-demo-v3"],
            project_dir=root,
        )

        static_by_path = {
            doc["path"]: doc for doc in artifact["static_context"]
        }
        metadata = static_by_path["packs/pack-demo-v3/pack.yaml"]
        knowledge = static_by_path["packs/pack-demo-v3/knowledge.md"]
        assert metadata["category"] == "pack-metadata", metadata
        assert "`demo-v3`" in metadata["content"], metadata
        assert knowledge["category"] == "pack-knowledge", knowledge
        assert "## Global Principles" in knowledge["content"], knowledge
        assert "## Component: demo-v3" in knowledge["content"], knowledge
        assert "## Component: unused-v3" not in knowledge["content"], knowledge
        assert knowledge["sections"] == [
            "Global Principles",
            "Component: demo-v3",
        ], knowledge

        budget = artifact["budget_report"]
        assert budget["static_docs"] == len(artifact["static_context"]), budget
        assert budget["estimated_tokens_static_by_category"]["pack-knowledge"] > 0
        assert budget["estimated_tokens_total"] <= (
            budget["estimated_tokens_referenced"]
            + budget["estimated_tokens_static"]
        ), budget

        report = pack_validation.validate_packs(root, ["pack-demo-v3"])
        assert report["status"] == "ok", report
    print("  ok manifest_v3_scopes_pack_knowledge_and_budget")


def test_policy_check_pass_and_failures() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack(root)
        policy_path = root / "workspaces" / "default" / "policy" / "context-policy.json"
        _write(policy_path, json.dumps({
            "rules": [
                {
                    "id": "require-contract",
                    "severity": "error",
                    "when": {"workstream": "engineering"},
                    "require": {"categories": ["contract"]},
                }
            ]
        }))
        artifact = task_context_engine.build_context_artifact(
            task="Implement demo feature",
            wiki_root=root,
            workspace="default",
            packs=["pack-demo"],
            project_dir=root,
        )
        assert artifact["governance_report"]["status"] == "ok", artifact["governance_report"]

        _write(policy_path, json.dumps({
            "rules": [
                {
                    "id": "require-quality",
                    "severity": "error",
                    "when": {"workstream": "engineering"},
                    "require": {"categories": ["quality"]},
                }
            ]
        }))
        missing_quality = task_context_engine.build_context_artifact(
            task="Implement demo feature",
            wiki_root=root,
            workspace="default",
            packs=["pack-demo"],
            project_dir=root,
        )
        assert missing_quality["governance_report"]["status"] == "error", missing_quality["governance_report"]
        assert any(v["check"] == "require.categories"
                   for v in missing_quality["governance_report"]["violations"])

        _write(policy_path, json.dumps({
            "rules": [
                {
                    "id": "deny-demo-contract",
                    "severity": "error",
                    "deny": {"docs": ["*demo.contract.json"]},
                }
            ]
        }))
        denied = task_context_engine.build_context_artifact(
            task="Implement demo feature",
            wiki_root=root,
            workspace="default",
            packs=["pack-demo"],
            project_dir=root,
        )
        assert denied["governance_report"]["status"] == "error", denied["governance_report"]
        assert any(v["check"] == "deny.docs"
                   for v in denied["governance_report"]["violations"])
    print("  ok policy_check_pass_and_failures")


def test_pack_validation_catches_bad_pack_api() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _write(root / "packs" / "pack-other" / "pack.yaml",
               "name: pack-other\nversion: 1.0.0\ndescription: Other\ncomponents:\n  - other\nkeywords:\n  other: [other]\n")
        _write(root / "packs" / "pack-bad" / "pack.yaml",
               "name: pack-bad\nversion: 1.0.0\ndescription: Bad\ncomponents:\n  - known\n"
               "keywords:\n  known: [other]\n  unknown: [bad]\n"
               "files:\n  missing: missing.md\n")
        _write(root / "packs" / "pack-bad" / "agents" / "pipeline" / "retrieval-map.md",
               "# Retrieval Map\n\n| Component | Docs to retrieve |\n|---|---|\n"
               "| `unknown` | ../outside.md |\n"
               "| `known` | packs/pack-other/agents/common-pitfalls.md |\n")
        report = pack_validation.validate_packs(root, ["pack-bad"])
        checks = {issue["check"] for issue in report["issues"]}
        assert report["status"] == "error", report
        assert "pack.keywords" in checks, report
        assert "retrieval-map.components" in checks, report
        assert "retrieval-map.path" in checks, report
        assert "retrieval-map.cross-pack" in checks, report
        assert "pack.keywords.cross_pack_ambiguous" in checks, report
    print("  ok pack_validation_catches_bad_pack_api")


def test_pack_validation_warns_on_documented_rules_without_script() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _write(root / "packs" / "pack-doc-only" / "pack.yaml",
               "name: pack-doc-only\nversion: 1.0.0\ndescription: Doc only\n"
               "components:\n  - demo\nkeywords:\n  demo: [demo]\n")
        _write(root / "packs" / "pack-doc-only" / "agents" / "pipeline" / "retrieval-map.md",
               "# Retrieval Map\n\n| Component | Docs to retrieve |\n|---|---|\n| `demo` | platform/contracts/ |\n")
        _write(root / "packs" / "pack-doc-only" / "agents" / "pipeline" / "validator-rules.md",
               "# Validator\n\n| Rule ID | Severity | Check |\n|---|---|---|\n"
               "| `pack-doc-only-demo-rule` | error | Must run. |\n")
        report = pack_validation.validate_packs(root, ["pack-doc-only"])
        assert report["status"] == "warning", report
        assert any(issue["check"] == "pack.validator_script" for issue in report["issues"]), report
    print("  ok pack_validation_warns_on_documented_rules_without_script")


def test_pack_validation_v2_quality_contract() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        pack = root / "packs" / "pack-quality"
        _write(
            pack / "pack.yaml",
            "manifest_version: 2\n"
            "name: pack-quality\n"
            "version: 1\n"
            "description: too short\n"
            "status: unknown\n"
            "category: unknown\n"
            "reviewed_on: yesterday\n"
            "audiences: [unknown]\n"
            "task_types: [unknown]\n"
            "scope_includes: [same scope]\n"
            "scope_excludes: [same scope]\n"
            "components:\n  - demo\n"
            "keywords:\n  demo: [same, same]\n"
            "files:\n"
            "  constraints: agents/constraints.md\n"
            "  validator_rules: agents/pipeline/validator-rules.md\n"
            "  validator_script: scripts/rules.py\n"
            "  retrieval_map: agents/pipeline/retrieval-map.md\n"
            "conflicts_with: []\n",
        )
        _write(pack / "README.md", "# Incomplete pack\n")
        _write(pack / "agents" / "constraints.md", "# Constraints\n\nNo stable IDs.\n")
        _write(
            pack / "agents" / "common-pitfalls.md",
            "# Pitfalls\n\n## P01 — One\n\n"
            "See `pack-quality-missing-rule`.\n",
        )
        _write(
            pack / "agents" / "pipeline" / "retrieval-map.md",
            "# Retrieval Map\n\n| Component | Docs to retrieve |\n|---|---|\n"
            "| `demo` | platform/contracts/ |\n",
        )
        _write(
            pack / "agents" / "pipeline" / "validator-rules.md",
            "# Rules\n\n| Rule ID | Severity | Check |\n|---|---|---|\n"
            "| `pack-quality-missing-rule` | error | Missing. |\n",
        )
        _write(pack / "scripts" / "rules.py", "RULES = []\n")

        report = pack_validation.validate_packs(root, ["pack-quality"])
        checks = {issue["check"] for issue in report["issues"]}
        assert report["status"] == "error", report
        assert {
            "pack.version",
            "pack.status",
            "pack.category",
            "pack.reviewed_on",
            "pack.audiences",
            "pack.task_types",
            "pack.scope",
            "pack.files",
            "pack.readme",
            "pack.constraints.ids",
            "pack.pitfalls",
            "pack.validator.parity",
            "pack.pitfalls.rule_ref",
        }.issubset(checks), report
    print("  ok pack_validation_v2_quality_contract")


def test_pack_validation_v3_catches_knowledge_and_adapter_drift() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack_v3(root)
        pack = root / "packs" / "pack-demo-v3"
        knowledge_path = pack / "knowledge.md"
        knowledge = knowledge_path.read_text(encoding="utf-8").replace(
            "### Failure Signals\n\n- Unbounded demo context.",
            "### Missing Failure Heading\n\n- Unbounded demo context.",
        )
        _write(knowledge_path, knowledge)
        _write(
            pack / "agents" / "pipeline" / "retrieval-map.md",
            "# Retrieval Map\n\n| Component | Docs to retrieve |\n|---|---|\n"
            "| `demo-v3` | platform/contracts/ |\n"
            "| `unused-v3` | platform/architecture/ |\n",
        )
        _write(
            pack / "agents" / "constraints.md",
            "# Legacy Adapter\n\n- `pack-demo-v3-legacy-only` — stale rule.\n",
        )
        _write(
            pack / "scripts" / "rules.py",
            "RULE_ID = 'pack-demo-v3-undocumented-rule'\nRULES = []\n",
        )

        report = pack_validation.validate_packs(root, ["pack-demo-v3"])
        checks = {issue["check"] for issue in report["issues"]}
        assert report["status"] == "error", report
        assert "pack.knowledge.component" in checks, report
        assert "pack.knowledge.adapter-drift" in checks, report
        assert "pack.validator.parity" in checks, report
        assert "retrieval-map.compatibility-drift" in checks, report
    print("  ok pack_validation_v3_catches_knowledge_and_adapter_drift")


def test_golden_eval_passes_and_fails_deterministically() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack(root)
        _write(root / ".contextd" / "config.json",
               json.dumps({"workspace": "default", "knowledge_root": "."}))
        fixture_dir = root / "workspaces" / "default" / "eval" / "golden-tasks"
        _write(fixture_dir / "pass.json", json.dumps({
            "id": "pass-demo-contract",
            "task": "Implement demo feature",
            "workspace": "default",
            "as_of": "2026-08-20",
            "packs": ["pack-demo"],
            "expected_docs": ["*demo.contract.json"],
            "expected_categories": ["contract"],
            "forbidden_docs": [],
            "expected_gaps": [],
            "policy_expectation": "ok",
        }))
        report_path = root / ".contextd" / "runs" / "eval-pass.json"
        assert cmd_eval.run(golden=True, workspace="default", cwd=str(root),
                            fmt="json", output=str(report_path)) == 0
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["status"] == "ok", report
        assert report["summary"]["passed"] == 1, report
        assert report["results"][0]["as_of"] == "2026-08-20", report

        _write(fixture_dir / "fail.json", json.dumps({
            "id": "fail-missing-doc",
            "task": "Implement demo feature",
            "workspace": "default",
            "as_of": "2026-08-20",
            "packs": ["pack-demo"],
            "expected_docs": ["workspaces/default/missing.md"],
        }))
        fail_path = root / ".contextd" / "runs" / "eval-fail.json"
        assert cmd_eval.run(golden=True, workspace="default", cwd=str(root),
                            fmt="json", output=str(fail_path)) == 1
        failed = json.loads(fail_path.read_text(encoding="utf-8"))
        assert failed["status"] == "error", failed
        assert failed["summary"]["failed"] == 1, failed

        (fixture_dir / "fail.json").unlink()
        undated_fixture = {
            "id": "undated-demo-contract",
            "task": "Implement demo feature",
            "workspace": "default",
            "packs": ["pack-demo"],
            "expected_docs": ["*demo.contract.json"],
        }
        _write(fixture_dir / "pass.json", json.dumps(undated_fixture))
        missing_date_path = root / ".contextd" / "runs" / "eval-missing-date.json"
        assert cmd_eval.run(
            golden=True,
            workspace="default",
            cwd=str(root),
            fmt="json",
            output=str(missing_date_path),
        ) == 1
        missing_date = json.loads(missing_date_path.read_text(encoding="utf-8"))
        assert missing_date["summary"]["load_errors"] == 1, missing_date
        assert missing_date["load_errors"][0]["error"] == "missing-or-invalid-as-of"

        fallback_path = root / ".contextd" / "runs" / "eval-fallback-date.json"
        assert cmd_eval.run(
            golden=True,
            workspace="default",
            cwd=str(root),
            fmt="json",
            output=str(fallback_path),
            as_of="2026-08-20",
        ) == 0
        fallback = json.loads(fallback_path.read_text(encoding="utf-8"))
        assert fallback["results"][0]["as_of"] == "2026-08-20", fallback
    print("  ok golden_eval_passes_and_fails_deterministically")


def test_non_code_product_pack_retrieval() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack_with_retrieval(
            root,
            "pack-product",
            {"brief": ["brief", "product brief"], "metric": ["metric", "success metric"]},
            {"brief": "product/briefs/, product/personas/, product/metrics.md"},
        )
        _write(root / "workspaces" / "default" / "product" / "briefs" / "checkout.md",
               "# Brief\n\n## Problem\n\nCheckout drops.\n\n## Target User\n\nBuyer.\n\n## Success Metric\n\nConversion.\n\n## Acceptance Criteria\n\n- measurable.\n")
        _write(root / "workspaces" / "default" / "product" / "metrics.md",
               "# Metrics\n\n## Success Metric\n\nConversion + retention.\n")
        artifact = task_context_engine.build_context_artifact(
            task="write product brief with success metric for checkout",
            wiki_root=root,
            workspace="default",
            packs=["pack-product"],
            project_dir=root,
        )
        assert artifact["intent"]["workstream"] == "product", artifact["intent"]
        assert artifact["intent"]["audience"] == "product", artifact["intent"]
        paths = {doc["path"] for doc in artifact["referenced_docs"]}
        categories = {doc["category"] for doc in artifact["referenced_docs"]}
        assert "product" in categories, artifact["referenced_docs"]
        assert any(path.endswith("product/briefs/checkout.md") for path in paths), paths
        assert any(path.endswith("product/metrics.md") for path in paths), paths
        assert "product_context" in artifact["retrieval_policy"]["priority"]
        print("  ok non_code_product_pack_retrieval")


def test_ba_unknown_domain_becomes_gap() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack_with_retrieval(
            root,
            "pack-ba",
            {"acceptance-criteria": ["acceptance criteria", "scenario"]},
            {"acceptance-criteria": "requirements/, platform/contracts/, domains/{domain}/workflow.md"},
        )
        _write(root / "workspaces" / "default" / "requirements" / "checkout.md",
               "# Requirement\n\n## Actor\n\nBuyer.\n\n## Business Outcome\n\nCheckout succeeds.\n\n## Acceptance Criteria\n\n- testable.\n")
        artifact = task_context_engine.build_context_artifact(
            task="write acceptance criteria for checkout",
            wiki_root=root,
            workspace="default",
            packs=["pack-ba"],
            project_dir=root,
        )
        assert artifact["intent"]["workstream"] == "business_analysis", artifact["intent"]
        assert any(doc["category"] == "requirement" for doc in artifact["referenced_docs"])
        assert any("domain not detected" in gap["missing"] and not gap["blocking_hint"]
                   for gap in artifact["gaps"]), artifact["gaps"]
        print("  ok ba_unknown_domain_becomes_gap")


def test_ux_pack_retrieves_design_sections() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack_with_retrieval(
            root,
            "pack-ui-ux",
            {"design-system": ["design system"], "accessibility": ["accessibility", "a11y"]},
            {
                "design-system": "platform/design/design-system.md, platform/design/tokens.md",
                "accessibility": "platform/design/a11y.md",
            },
        )
        _write(root / "workspaces" / "default" / "platform" / "design" / "design-system.md",
               "# Design System\n\n## Flow\n\nUse canonical flow.\n\n## Accessibility\n\nKeyboard first.\n\n## UX Writing\n\nPlain copy.\n")
        _write(root / "workspaces" / "default" / "platform" / "design" / "tokens.md",
               "# Tokens\n\n## Accessibility\n\nContrast tokens.\n")
        artifact = task_context_engine.build_context_artifact(
            task="design system accessibility update",
            wiki_root=root,
            workspace="default",
            packs=["pack-ui-ux"],
            project_dir=root,
        )
        design_docs = [doc for doc in artifact["referenced_docs"] if doc["category"] == "design"]
        assert artifact["intent"]["workstream"] == "design", artifact["intent"]
        assert design_docs, artifact["referenced_docs"]
        assert any("Accessibility" in doc["sections"] for doc in design_docs), design_docs
        print("  ok ux_pack_retrieves_design_sections")


def test_qc_evidence_retrieval_excludes_raw_sources() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack_with_retrieval(
            root,
            "pack-qc",
            {"test-execution": ["test execution", "test result"]},
            {"test-execution": "runbooks/, evidence/"},
        )
        _write(root / "workspaces" / "default" / "evidence" / "_index.md",
               "# Evidence Index\n\n## Active\n\n| id | state |\n")
        _write(root / "workspaces" / "default" / "evidence" / "sources" / "e1" / "raw.md",
               "# Raw\n\nSecret-ish raw source should not be retrieved wholesale.\n")
        _write(root / "workspaces" / "default" / "evidence" / "qa" / "e1" / "verified-facts.md",
               "# Verified Facts\n\n## Verified Facts\n\n- Tests passed.\n")
        artifact = task_context_engine.build_context_artifact(
            task="summarize test execution evidence for release quality",
            wiki_root=root,
            workspace="default",
            packs=["pack-qc"],
            project_dir=root,
        )
        paths = {doc["path"] for doc in artifact["referenced_docs"]}
        assert artifact["intent"]["workstream"] == "quality", artifact["intent"]
        assert any("/evidence/_index.md" in path for path in paths), paths
        assert any(path.endswith("verified-facts.md") for path in paths), paths
        assert not any("/evidence/sources/" in path for path in paths), paths
        assert "quality_evidence" in artifact["retrieval_policy"]["priority"]
        print("  ok qc_evidence_retrieval_excludes_raw_sources")


def test_retrieval_map_safety_and_redaction() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _workspace(root, "other")
        _pack_with_retrieval(
            root,
            "pack-security",
            {"guard": ["guard", "secret"]},
            {
                "guard": (
                    "security/guidance.md, security/.env, ../outside.md, "
                    f"{root}/absolute.md, workspaces/other/workspace.md"
                )
            },
        )
        _write(root / "workspaces" / "default" / "security" / "guidance.md",
               "# Security\n\n## Scope\n\napi_key = abc123\npassword: hunter2\n")
        _write(root / "workspaces" / "default" / "security" / ".env",
               "TOKEN=should-not-read\n")
        _write(root / "absolute.md", "# Absolute\n")
        artifact = task_context_engine.build_context_artifact(
            task="guard secret handling",
            wiki_root=root,
            workspace="default",
            packs=["pack-security"],
            project_dir=root,
        )
        paths = {doc["path"] for doc in artifact["referenced_docs"]}
        assert any(path.endswith("security/guidance.md") for path in paths), paths
        assert not any(path.endswith("security/.env") for path in paths), paths
        redacted_docs = [doc for doc in artifact["referenced_docs"] if doc.get("redacted")]
        assert redacted_docs, artifact["referenced_docs"]
        assert "<REDACTED-SECRET>" in redacted_docs[0]["content"], redacted_docs[0]
        assert any(gap["category"] == "security-policy" and "../outside.md" in gap["missing"]
                   for gap in artifact["gaps"]), artifact["gaps"]
        assert any(gap["category"] == "security-policy" and "absolute paths" in gap["missing"]
                   for gap in artifact["gaps"]), artifact["gaps"]
        assert any(gap["category"] == "security-policy" and "workspaces/other" in gap["missing"]
                   for gap in artifact["gaps"]), artifact["gaps"]
        assert any(gap["category"] == "security-policy" and "security/.env" in gap["missing"]
                   for gap in artifact["gaps"]), artifact["gaps"]
        assert any("Redacted sensitive-looking content" in warning for warning in artifact["warnings"])
        print("  ok retrieval_map_safety_and_redaction")


def test_evidence_glob_excludes_raw_sources() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack_with_retrieval(
            root,
            "pack-qc-glob",
            {"test-execution": ["test execution", "evidence"]},
            {"test-execution": "evidence/**/*.md"},
        )
        _write(root / "workspaces" / "default" / "evidence" / "sources" / "e1" / "raw.md",
               "# Interview Transcript\n\nPII and raw customer text should not be retrieved wholesale.\n")
        _write(root / "workspaces" / "default" / "evidence" / "qa" / "e1" / "verified-facts.md",
               "# Verified Facts\n\n## Verified Facts\n\n- Release evidence was checked.\n")
        artifact = task_context_engine.build_context_artifact(
            task="summarize test execution evidence",
            wiki_root=root,
            workspace="default",
            packs=["pack-qc-glob"],
            project_dir=root,
        )
        paths = {doc["path"] for doc in artifact["referenced_docs"]}
        assert any(path.endswith("verified-facts.md") for path in paths), paths
        assert not any("/evidence/sources/" in path for path in paths), paths
        assert "PII and raw customer text" not in json.dumps(artifact, ensure_ascii=False)
        print("  ok evidence_glob_excludes_raw_sources")


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
        invalid, warnings = task_context_engine.resolve_contract_path("../citation-format", root, "default", [])
        assert invalid is None, (invalid, warnings)
        assert any("Invalid contract id" in warning for warning in warnings), warnings
        print("  ok contract_path_index_and_fallback")


def test_thesis_hardening_docs_and_release_mapping() -> None:
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    solo = (ROOT / "packs" / "pack-solo-builder" / "README.md").read_text(encoding="utf-8")
    quickstart = (ROOT / "QUICKSTART.md").read_text(encoding="utf-8")
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    spec = (ROOT / "contextd.spec").read_text(encoding="utf-8")

    assert "Resolve workspace from `<cwd>/.contextd/config.json#workspace`" in claude, claude
    assert "Resolve workspace from `<cwd>/.claude/wiki.json#workspace`" not in claude, claude
    assert "knowledge_root" in claude, claude
    assert ".contextd/config.json#packs" in agents, agents
    assert "`wiki.json#packs`" not in agents, agents
    assert ".contextd/config.json#packs" in solo, solo
    assert ".claude/wiki.json#packs` chỉ là compatibility" in solo, solo
    assert "Python ≥ 3.9" not in quickstart, quickstart
    assert "working contextd setup" in quickstart, quickstart
    assert "macos-15-intel" in release, release
    assert "macos-13" not in release, release
    assert 'BINARY="contextd-${PLATFORM}-arm64"' not in release, release
    assert "Linux arm64 prebuilt binary is not available" in release, release
    assert "contextd-linux-arm64" not in release, release
    project_version_match = re.search(
        r'(?m)^version\s*=\s*"([^"]+)"\s*$',
        pyproject,
    )
    assert project_version_match, pyproject
    project_version = project_version_match.group(1)
    assert re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+(?:[.-][0-9A-Za-z.-]+)?",
        project_version,
    ), project_version
    for module in ("cmd_synapse", "lib.synapse_engine", "lib.frontmatter"):
        assert f"'{module}'" in spec, (module, spec)
    assert "'synapse_engine'" not in spec, "top-level lib module would create duplicate state"
    assert "'scripts/lib'" not in spec, "PyInstaller path exposes duplicate top-level modules"
    assert "needs: [release-metadata, verify, package-source, build-binaries]" in release
    assert "python-version: ['3.10', '3.12']" in release
    actual_version = contextd_version.get_version(start_path=ROOT)
    assert actual_version == project_version, (actual_version, project_version)
    print("  ok thesis_hardening_docs_and_release_mapping")


def test_onboarding_and_readme_docs_consistency() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    quickstart = (ROOT / "QUICKSTART.md").read_text(encoding="utf-8")
    pack_catalog = (ROOT / "packs" / "README.md").read_text(encoding="utf-8")
    install_docs = [
        (ROOT / "onboarding" / "install.en.html").read_text(encoding="utf-8"),
        (ROOT / "onboarding" / "install.html").read_text(encoding="utf-8"),
    ]
    onboarding_docs = [
        (ROOT / "onboarding" / "index.en.html").read_text(encoding="utf-8"),
        (ROOT / "onboarding" / "index.html").read_text(encoding="utf-8"),
    ]

    # Source installs and public onboarding must agree with pyproject.toml.
    for content in [quickstart, *install_docs]:
        assert "Python ≥ 3.9" not in content, "stale Python 3.9 requirement"
    for content in install_docs:
        assert "Python ≥ 3.10" in content, "source prerequisite missing"
        assert "python3 -m pip install -e ." in content, "source path does not install CLI"
        assert "contextd synapse --preview --text" in content, "synapse smoke step missing"
        assert "templates\\contextd-config.json" not in content, "project config used as global config"
        assert "%USERPROFILE%\\.claude\\config.json" not in content, "wrong Windows verify path"
        assert "default_workspace" in content, "global config shape missing"

    # Do not freeze example selection output that changes with governed knowledge.
    assert "Intent: review / product" not in readme, "README contains stale golden output"
    assert "<synapse-hash>" in readme, "README example must remain schematic"
    assert "abbreviated output shape" in readme, "README example stability note missing"

    # The source directories are the pack inventory; both locale summaries must track it.
    pack_names = sorted(
        path.name for path in (ROOT / "packs").iterdir()
        if path.is_dir() and (path / "pack.yaml").is_file()
    )
    assert pack_names, "pack inventory unexpectedly empty"
    for pack_name in pack_names:
        manifest = (ROOT / "packs" / pack_name / "pack.yaml").read_text(
            encoding="utf-8",
        )
        manifest_version = int(next(
            line.split(":", 1)[1].strip()
            for line in manifest.splitlines()
            if line.startswith("manifest_version:")
        ))
        assert manifest_version in (2, 3), (pack_name, "unsupported manifest")
        if manifest_version == 3:
            assert "retrieval:" in manifest, (pack_name, "v3 retrieval missing")
            assert (ROOT / "packs" / pack_name / "knowledge.md").is_file(), (
                pack_name,
                "v3 canonical knowledge missing",
            )
        assert "reviewed_on:" in manifest, (pack_name, "missing evidence review date")
        version = next(
            line.split(":", 1)[1].strip()
            for line in manifest.splitlines()
            if line.startswith("version:")
        )
        status = next(
            line.split(":", 1)[1].strip()
            for line in manifest.splitlines()
            if line.startswith("status:")
        )
        catalog_row = next(
            (line for line in pack_catalog.splitlines() if f"[{pack_name}]" in line),
            "",
        )
        assert catalog_row, (pack_name, "missing from canonical pack catalog")
        assert f"| {status} {version} |" in catalog_row, (
            pack_name,
            "catalog maturity/version drift",
        )
    for content in onboarding_docs:
        assert "13 packs" not in content, "hard-coded stale pack count"
        assert "manifest-v3" in content, "pack scaffold guidance is stale"
        for pack_name in pack_names:
            assert pack_name in content, (pack_name, "missing from onboarding catalog")
        for command in ("contextd synapse", "contextd doctor", "contextd policy-check"):
            assert command in content, (command, "missing from runtime CLI onboarding")
        for concept in ("Context artifact", "runtime memory", "long-term memory"):
            assert concept in content, (concept, "missing from context-memory model")

    # Tool templates must not recreate the legacy Compose/runtime-install pattern
    # that first-party recipes explicitly reject.
    for template_name in ("tool-recipe.md", "tool-spec.md"):
        content = (ROOT / "templates" / template_name).read_text(encoding="utf-8")
        assert "docker-compose.yml" not in content, (template_name, "legacy Compose name")
        assert "pip install -q" not in content, (template_name, "runtime dependency install")
        assert "Windows + Docker (recommend" not in content, (
            template_name,
            "container must be target/rationale driven",
        )

    # A separate knowledge root must contain a scaffolded workspace before init.
    scaffold_pos = quickstart.index("/new-workspace shared")
    init_pos = quickstart.index(
        "contextd init --knowledge-root ~/company-wiki --workspace shared"
    )
    assert scaffold_pos < init_pos, "team quickstart initializes before workspace scaffold"
    assert "workspaces/shared/workspace.md" in quickstart
    print("  ok onboarding_and_readme_docs_consistency")


def test_default_contract_index_and_demo_golden_fixture() -> None:
    path, warnings = task_context_engine.resolve_contract_path(
        "citation-format.v1", ROOT, "default", [],
    )
    assert path and path.relative_to(ROOT).as_posix() == (
        "workspaces/default/platform/contracts/citation-format.md"
    ), (path, warnings)
    invalid, warnings = task_context_engine.resolve_contract_path(
        "../citation-format", ROOT, "default", [],
    )
    assert invalid is None, (invalid, warnings)
    assert any("Invalid contract id" in warning for warning in warnings), warnings

    artifact = task_context_engine.build_context_artifact(
        task="Write a product brief, acceptance criteria, and design system flow for "
             "agent-context-demo reliable agent inputs",
        wiki_root=ROOT,
        workspace="default",
        packs=["pack-product", "pack-ba", "pack-ui-ux"],
        project_dir=ROOT,
    )
    paths = {doc["path"] for doc in artifact["referenced_docs"]}
    categories = {doc["category"] for doc in artifact["referenced_docs"]}
    assert "workspaces/default/product/briefs/agent-context-build.md" in paths, paths
    assert "workspaces/default/requirements/agent-context-build.md" in paths, paths
    assert "workspaces/default/platform/design/design-system.md" in paths, paths
    assert {"product", "requirement", "design"}.issubset(categories), categories
    assert not any(path.startswith("workspaces/iot-device/") for path in paths), paths
    print("  ok default_contract_index_and_demo_golden_fixture")


def test_doctor_and_adapter_drift_checks() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack(root)
        _write(root / ".contextd" / "config.json",
               json.dumps({"workspace": "default", "knowledge_root": ".", "packs": ["pack-demo"]}))
        clean = cmd_doctor.diagnose(cwd=str(root))
        assert clean["status"] == "ok", clean

        _write(root / ".contextd" / "config.json",
               json.dumps({"workspace": "default", "knowledge_root": ".", "packs": ["pack-missing"]}))
        missing = cmd_doctor.diagnose(cwd=str(root))
        assert missing["status"] == "error", missing
        assert any(issue["check"] == "active-packs" for issue in missing["issues"]), missing
        assert any(issue["check"] == "pack.manifest" for issue in missing["issues"]), missing

        _pack_with_retrieval(
            root,
            "pack-bad",
            {"bad": ["bad"]},
            {"bad": "../outside.md"},
        )
        _write(root / ".contextd" / "config.json",
               json.dumps({"workspace": "default", "knowledge_root": ".", "packs": ["pack-bad"]}))
        unsafe = cmd_doctor.diagnose(cwd=str(root))
        assert unsafe["status"] == "error", unsafe
        assert any(issue["check"] == "retrieval-map-safety" for issue in unsafe["issues"]), unsafe

    artifacts = render_runtime.render("codex-plugin", workspace="default", include_engine=False)
    skill = artifacts["skills/contextd/SKILL.md"]
    assert "Look for `.contextd/config.json`" in skill, skill
    assert "Look for `.claude/wiki.json`" not in skill, skill
    assert skill.find("`.contextd/config.json`") < skill.find("`.claude/wiki.json`"), skill

    clean_repo = cmd_doctor.diagnose(cwd=str(ROOT))
    assert not any(issue["check"] == "adapter-drift" for issue in clean_repo["issues"]), clean_repo
    print("  ok doctor_and_adapter_drift_checks")


def test_codex_agents_use_json_canonical_artifact() -> None:
    for filename in (
        "contextd-planner.toml",
        "contextd-context-selector.toml",
        "contextd-reviewer.toml",
    ):
        text = (ROOT / ".codex" / "agents" / filename).read_text(encoding="utf-8")
        assert "contextd context" in text, filename
        assert "current-task.json" in text, filename
        assert "Pass A — Retrieval" not in text, filename
        assert "Context File Template" not in text, filename
        assert "Write `{project_dir}/.contextd/context/current-task.md`" not in text, filename
        assert "source of truth" not in text.lower() or "current-task.json" in text, filename
    print("  ok codex_agents_use_json_canonical_artifact")


def test_pack_ui_ux_rules() -> None:
    path = ROOT / "packs" / "pack-ui-ux" / "scripts" / "rules.py"
    spec = importlib.util.spec_from_file_location("pack_ui_ux_rules_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    design_path = Path("/tmp/ws/workspaces/default/platform/design/design-system.md")
    violations = []
    for rule in module.RULES:
        violations.extend(rule(design_path, [
            "# Design System",
            "Use color.primary token for the primary action.",
            "Hardcoded fallback #ff00aa.",
        ], {}))
    rules = {v["rule"] for v in violations}
    assert "pack-ui-ux-hardcoded-color" in rules, violations
    assert "pack-ui-ux-missing-a11y-note" in rules, violations
    assert "pack-ui-ux-contrast-unchecked" in rules, violations

    flow_path = Path("/tmp/ws/workspaces/default/domains/checkout/flows/payment.md")
    flow_violations = []
    for rule in module.RULES:
        flow_violations.extend(rule(flow_path, ["# Payment Flow", "## Happy Path"], {}))
    assert any(v["rule"] == "pack-ui-ux-flow-no-error-path" for v in flow_violations), flow_violations

    clean = []
    for rule in module.RULES:
        clean.extend(rule(design_path, [
            "# Design System",
            "> A11y: keyboard focus and ARIA labels are documented.",
            "Use color.primary token with contrast 4.5:1.",
        ], {}))
    assert not clean, clean
    print("  ok pack_ui_ux_rules")


def test_pack_operator_steering_wayfinding_rules() -> None:
    path = ROOT / "packs" / "pack-operator-steering" / "scripts" / "rules.py"
    spec = importlib.util.spec_from_file_location(
        "pack_operator_steering_rules_test",
        path,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    wayfinding_path = Path(
        "/tmp/ws/workspaces/default/reports/operator-wayfinding-checkpoint.md"
    )
    violations = []
    for rule in module.RULES:
        violations.extend(rule(wayfinding_path, [
            "# Operator Wayfinding Checkpoint",
            "## Evidence & Gap Check",
            "- Proven: task exists",
        ], {}))
    assert any(
        item["rule"] == "pack-operator-steering-wayfinding-missing-control-fields"
        for item in violations
    ), violations

    template = (
        ROOT
        / "packs"
        / "pack-operator-steering"
        / "templates"
        / "wayfinding-checkpoint.md"
    )
    clean = []
    lines = template.read_text(encoding="utf-8").splitlines()
    for rule in module.RULES:
        clean.extend(rule(template, lines, {}))
    assert not clean, clean

    # Mentioning a decision frontier in an audit must not turn that report into
    # a decision-ledger document and demand unrelated ADR fields.
    audit_path = Path("/tmp/ws/workspaces/default/reports/context-audit.md")
    audit_lines = [
        "# Context Audit Report",
        "## Evidence",
        "- Inspected: current artifact",
        "## Findings",
        "- Decision frontier is incomplete.",
    ]
    audit_violations = []
    for rule in module.RULES:
        audit_violations.extend(rule(audit_path, audit_lines, {}))
    assert not any(
        item["rule"] == "pack-operator-steering-decision-missing-ledger-fields"
        for item in audit_violations
    ), audit_violations
    print("  ok pack_operator_steering_wayfinding_rules")


def test_stdio_utf8_under_legacy_codepage() -> None:
    """CLI must not crash writing/reading non-ASCII under a legacy codepage.

    Forces PYTHONIOENCODING=cp1252 (the historical Windows console default)
    to prove lib/stdio.py's configure_stdio() reconfiguration — not an
    environment variable the caller happens to set — is what makes this work.
    """
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"
    env.pop("PYTHONUTF8", None)
    task = "đánh giá context drift với kiểm tra"
    for args in (
        ["context", task, "--preview", "--format", "markdown"],
        ["context", task, "--preview", "--format", "json"],
        ["explain", task, "--format", "text"],
        ["check"],
    ):
        proc = subprocess.run(
            [sys.executable, "-m", "scripts.cli", *args],
            cwd=str(ROOT), text=True, encoding="utf-8", capture_output=True, env=env,
        )
        assert proc.returncode == 0, (args, proc.stdout, proc.stderr)
    print("  ok stdio_utf8_under_legacy_codepage")


def test_intent_classification_word_boundaries() -> None:
    """Keyword matching must respect word boundaries, not bare substrings."""
    from lib import task_context_engine as tce

    cases = [
        ("build a new payment service", "implement_feature", "engineering"),
        ("check why the consumer fails", "fix_bug", "engineering"),
        ("add rapid api endpoint", "implement_feature", "engineering"),
        ("fix the checkout crash", "fix_bug", "engineering"),
        ("debug context quality", "fix_bug", None),
    ]
    for task, expected_intent, expected_workstream in cases:
        intent = tce.detect_intent(task)
        assert intent == expected_intent, (task, intent, expected_intent)
        if expected_workstream is not None:
            workstream = tce.detect_workstream(task, [], [])
            assert workstream == expected_workstream, (task, workstream, expected_workstream)
    print("  ok intent_classification_word_boundaries")


def test_pack_keyword_special_chars() -> None:
    """Punctuation-heavy keywords (.proto, @RestController) must still match."""
    from lib import task_context_engine as tce

    assert "grpc" in tce.detect_components(
        "update service.proto stub", ROOT, ["pack-web-api"])
    assert "rest" in tce.detect_components(
        "add @RestController route", ROOT, ["pack-web-api"])
    assert "drift-check" in tce.detect_components(
        "drift-check accepted decisions", ROOT, ["pack-operator-steering"])
    print("  ok pack_keyword_special_chars")


def test_cli_ux_help_and_aliases() -> None:
    def run_cli(args: list[str]) -> subprocess.CompletedProcess:
        # contextd forces UTF-8 on its own stdout (see lib/stdio.py) regardless
        # of the OS console codepage, so decode captured output as UTF-8 too —
        # otherwise a locale-default decode (e.g. cp1252 on Windows) breaks on
        # the workspace's non-ASCII content.
        return subprocess.run(
            [sys.executable, "-m", "scripts.cli", *args],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            capture_output=True,
        )

    starter = run_cli(["--help"])
    assert starter.returncode == 0, (starter.stdout, starter.stderr)
    assert "Start here:" in starter.stdout, starter.stdout
    for name in ["init", "check", "context", "explain", "find", "recipes"]:
        assert f"  {name}" in starter.stdout, starter.stdout
    for hidden in ["pack-validate", "mcp-server", "task-context", "policy-check", "synapse"]:
        assert hidden not in starter.stdout, starter.stdout

    full = run_cli(["help", "--all"])
    assert full.returncode == 0, (full.stdout, full.stderr)
    for name in ["pack-validate", "mcp-server", "task-context", "policy-check", "eval", "synapse"]:
        assert name in full.stdout, full.stdout

    doctor = run_cli(["doctor", "--format", "text"])
    check = run_cli(["check"])
    assert check.returncode == doctor.returncode, (check.stdout, check.stderr, doctor.stdout, doctor.stderr)
    assert check.stdout == doctor.stdout, (check.stdout, doctor.stdout)

    no_materialize = run_cli(["context", "design context", "--format", "json", "--no-materialize"])
    preview = run_cli(["context", "design context", "--format", "json", "--preview"])
    assert no_materialize.returncode == 0, (no_materialize.stdout, no_materialize.stderr)
    assert preview.returncode == 0, (preview.stdout, preview.stderr)
    no_materialize_json = json.loads(no_materialize.stdout)
    preview_json = json.loads(preview.stdout)
    no_materialize_json.pop("generated_at", None)
    preview_json.pop("generated_at", None)
    assert preview_json == no_materialize_json

    legacy = run_cli(["task-context", "design context", "--format", "json"])
    assert legacy.returncode == 0, (legacy.stdout, legacy.stderr)
    assert json.loads(legacy.stdout)["artifact_type"] == "contextd_task_context.v1"

    synapse = run_cli(["synapse", "--preview", "--as-of", "2026-08-17", "--format", "json"])
    assert synapse.returncode == 0, (synapse.stdout, synapse.stderr)
    assert json.loads(synapse.stdout)["artifact_type"] == "contextd_synapse.v1"

    invalid_workspace = run_cli([
        "context", "design context", "--workspace", "../other", "--preview",
    ])
    assert invalid_workspace.returncode == 1, (
        invalid_workspace.stdout, invalid_workspace.stderr,
    )
    assert "context build refused" in invalid_workspace.stderr

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack(root)
        init = run_cli(["init", "--cwd", str(root)])
        assert init.returncode == 0, (init.stdout, init.stderr)
        config = json.loads((root / ".contextd" / "config.json").read_text(encoding="utf-8"))
        assert config["workspace"] == "default", config
        assert config["knowledge_root"] == ".", config
        check = run_cli(["check", "--cwd", str(root)])
        assert check.returncode == 0, (check.stdout, check.stderr)
    print("  ok cli_ux_help_and_aliases")


def test_cli_smoke() -> None:
    commands = [
        [sys.executable, "-m", "scripts.cli", "resolve", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "find", "citation", "--limit", "1", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "context", "design context", "--format", "json", "--no-materialize"],
        [sys.executable, "-m", "scripts.cli", "synapse", "--preview", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "connect", "--client", "codex",
         "--knowledge-root", str(ROOT), "--workspace", "default"],
        [sys.executable, "-m", "scripts.cli", "doctor", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "explain", "design context", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "pack-validate", "--all", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "policy-check", "debug context quality", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "eval", "--golden", "--workspace", "default", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "contract-path", "citation-format.v1", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "mcp-config", "--client", "codex",
         "--knowledge-root", str(ROOT), "--workspace", "default"],
    ]
    expected_exports = {
        "plain": ["contextd-bundle.md"],
        "codex-plugin": [".codex-plugin/plugin.json", "skills/contextd/SKILL.md"],
        "codex-instructions": [".codex/instructions.md"],
        "cursor": [".cursorrules", ".cursor/context.md"],
    }
    with tempfile.TemporaryDirectory() as td:
        export_root = Path(td)
        for runtime, expected in expected_exports.items():
            out_dir = export_root / runtime
            commands.append([
                sys.executable, "-m", "scripts.cli", "export",
                "--runtime", runtime, "--output", str(out_dir),
            ])
        for cmd in commands:
            # See run_cli() note above: decode as UTF-8 to match contextd's
            # forced-UTF-8 stdout, independent of the OS console codepage.
            proc = subprocess.run(cmd, cwd=str(ROOT), text=True, encoding="utf-8",
                                  capture_output=True)
            assert proc.returncode == 0, (cmd, proc.stdout, proc.stderr)
        for runtime, expected in expected_exports.items():
            for rel in expected:
                assert (export_root / runtime / rel).is_file(), (runtime, rel)
    print("  ok cli_smoke")


def _mcp_request(proc: subprocess.Popen, payload: dict) -> dict:
    assert proc.stdin is not None
    assert proc.stdout is not None
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    assert line, "MCP server closed stdout"
    return json.loads(line)


def test_mcp_server_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _pack(root)
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "scripts.cli", "mcp-server",
                "--knowledge-root", str(root),
                "--workspace", "default",
                "--cwd", str(root),
            ],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            init = _mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "contextd-test", "version": "1"},
                },
            })
            assert init["result"]["protocolVersion"] == "2025-11-25", init
            assert init["result"]["capabilities"]["tools"]["listChanged"] is False, init
            assert init["result"]["capabilities"]["resources"]["listChanged"] is False, init
            assert init["result"]["capabilities"]["prompts"]["listChanged"] is False, init

            assert proc.stdin is not None
            proc.stdin.write(json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }) + "\n")
            proc.stdin.flush()

            tools = _mcp_request(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            names = {tool["name"] for tool in tools["result"]["tools"]}
            assert {
                "contextd.resolve",
                "contextd.find",
                "contextd.context",
                "contextd.contract_path",
                "contextd.bundle",
            }.issubset(names), names

            resources = _mcp_request(proc, {"jsonrpc": "2.0", "id": 21, "method": "resources/list"})
            resource_uris = {resource["uri"] for resource in resources["result"]["resources"]}
            assert "contextd://workspace/default/workspace.md" in resource_uris, resources

            workspace_doc = _mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 22,
                "method": "resources/read",
                "params": {"uri": "contextd://workspace/default/workspace.md"},
            })
            assert "# Workspace" in workspace_doc["result"]["contents"][0]["text"], workspace_doc

            prompts = _mcp_request(proc, {"jsonrpc": "2.0", "id": 23, "method": "prompts/list"})
            prompt_names = {prompt["name"] for prompt in prompts["result"]["prompts"]}
            assert {
                "contextd.build_task_context",
                "contextd.explain_context",
                "contextd.run_policy_check",
            }.issubset(prompt_names), prompts

            prompt = _mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 24,
                "method": "prompts/get",
                "params": {
                    "name": "contextd.build_task_context",
                    "arguments": {"task": "Implement demo feature"},
                },
            })
            assert "contextd context" in prompt["result"]["messages"][0]["content"]["text"], prompt

            resolved = _mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "contextd.resolve", "arguments": {}},
            })
            assert resolved["result"]["structuredContent"]["workspace"] == "default", resolved

            found = _mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "contextd.find",
                    "arguments": {"query": "citation", "limit": 1},
                },
            })
            assert found["result"]["structuredContent"]["advisory"] is True, found

            context = _mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "contextd.context",
                    "arguments": {"task": "Implement demo feature"},
                },
            })
            assert context["result"]["structuredContent"]["artifact_type"] == "contextd_task_context.v1", context

            contract = _mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "contextd.contract_path",
                    "arguments": {"contract_id": "demo.v1"},
                },
            })
            contract_payload = contract["result"]["structuredContent"]
            assert contract_payload["relative_path"].endswith("demo.contract.json"), contract

            bundle = _mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "contextd.bundle",
                    "arguments": {"max_chars": 5000, "include_packs": True},
                },
            })
            assert "contextd Bundle" in bundle["result"]["structuredContent"]["content"], bundle

            invalid = _mcp_request(proc, {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {"name": "contextd.missing", "arguments": {}},
            })
            assert invalid["error"]["code"] == -32602, invalid
        finally:
            if proc.stdin:
                proc.stdin.close()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
                proc.wait(timeout=5)
        print("  ok mcp_server_smoke")


def test_installer_dry_run_knowledge_root() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        home = base / "home"
        root = base / "knowledge"
        home.mkdir()
        _workspace(root)
        env = os.environ.copy()
        env["HOME"] = str(home)

        proc = subprocess.run(
            [
                "bash", str(ROOT / "scripts" / "install-to-claude.sh"),
                "--dry-run",
                "--knowledge-root", str(root),
                "--default-workspace", "default",
            ],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            env=env,
        )
        assert proc.returncode == 0, (proc.stdout, proc.stderr)
        assert "Knowledge root:" in proc.stdout, proc.stdout
        assert not (home / ".contextd" / "config.json").exists()

        alias = subprocess.run(
            [
                "bash", str(ROOT / "scripts" / "install-to-claude.sh"),
                "--dry-run",
                "--knowledge-repo", str(root),
            ],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            env=env,
        )
        assert alias.returncode == 0, (alias.stdout, alias.stderr)
        assert "compatibility alias" in alias.stderr, alias.stderr

        default_root = subprocess.run(
            ["bash", str(ROOT / "scripts" / "install-to-claude.sh"), "--dry-run"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            env=env,
        )
        assert default_root.returncode == 0, (default_root.stdout, default_root.stderr)
        assert f"Knowledge root: {ROOT}" in default_root.stdout, default_root.stdout

        mcp_snippet = subprocess.run(
            [
                "bash", str(ROOT / "scripts" / "install-to-claude.sh"),
                "--knowledge-root", str(root),
                "--default-workspace", "default",
                "--print-mcp-config", "codex",
            ],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            env=env,
        )
        assert mcp_snippet.returncode == 0, (mcp_snippet.stdout, mcp_snippet.stderr)
        assert "[mcp_servers.contextd]" in mcp_snippet.stdout, mcp_snippet.stdout
        assert "mcp-server" in mcp_snippet.stdout, mcp_snippet.stdout
        assert not (home / ".contextd" / "config.json").exists()
    print("  ok installer_dry_run_knowledge_root")


def test_migrate_config_roundtrip_and_no_clobber() -> None:
    def _run_migrate(**kwargs):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cmd_migrate_config.run(**kwargs)
        return code, stdout.getvalue(), stderr.getvalue()

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root, "legacy")
        _write(root / ".claude" / "wiki.json", json.dumps({
            "project": "legacy-app",
            "workspace": "legacy",
            "wiki_root": ".",
            "packs": ["pack-demo"],
            "domain": "checkout",
        }))
        code, out, err = _run_migrate(cwd=str(root), dry_run=True)
        assert code == 0, (out, err)
        assert "knowledge_root" in out, out
        assert not (root / ".contextd" / "config.json").exists()

        code, out, err = _run_migrate(cwd=str(root))
        assert code == 0, (out, err)
        config_path = root / ".contextd" / "config.json"
        migrated = json.loads(config_path.read_text(encoding="utf-8"))
        assert migrated["project"] == "legacy-app", migrated
        assert migrated["workspace"] == "legacy", migrated
        assert migrated["knowledge_root"] == ".", migrated
        assert migrated["packs"] == ["pack-demo"], migrated
        assert migrated["domain"] == "checkout", migrated
        assert migrated["compat"]["legacy_field_alias"] == "wiki_root", migrated
        assert migrated["compat"]["generated_from"].endswith(".claude/wiki.json"), migrated

        code, out, err = _run_migrate(cwd=str(root))
        assert code == 1, (out, err)
        assert "already exists" in err, err
        code, out, err = _run_migrate(cwd=str(root), force=True)
        assert code == 0, (out, err)
    print("  ok migrate_config_roundtrip_and_no_clobber")


def test_trace_uses_contextd_runs_and_renderer_fallback() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _workspace(root)
        _write(root / ".contextd" / "config.json",
               json.dumps({"workspace": "default", "knowledge_root": "."}))
        payload = {
            "tool_name": "Task",
            "cwd": str(root),
            "tool_input": {"subagent_type": "contextd-planner"},
            "tool_response": (
                "done\n```json\n"
                + json.dumps({
                    "run_id": "run-canonical",
                    "stage": "01-planner",
                    "workspace_at_run": "default",
                    "intent": {"type": "design", "workspace": "default"},
                })
                + "\n```\n"
            ),
        }
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "emit_trace.py")],
            cwd=str(ROOT),
            input=json.dumps(payload),
            text=True,
            capture_output=True,
        )
        assert proc.returncode == 0, (proc.stdout, proc.stderr)
        assert (root / ".contextd" / "runs" / "run-canonical" / "01-planner.json").is_file()
        assert not (root / ".claude" / "runs" / "run-canonical").exists()

        rendered = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "render_trace.py"),
             "--project-dir", str(root), "--last"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        assert rendered.returncode == 0, (rendered.stdout, rendered.stderr)
        assert (root / ".contextd" / "runs" / "run-canonical" / "trace.html").is_file()

        shutil.rmtree(root / ".contextd" / "runs")
        _write(root / ".claude" / "runs" / "legacy-run" / "run.json",
               json.dumps({
                   "stage": "run",
                   "run_id": "legacy-run",
                   "workspace_at_run": "default",
                   "stages_completed": [],
               }))
        legacy_rendered = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "render_trace.py"),
             "--project-dir", str(root), "--last"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
        assert legacy_rendered.returncode == 0, (legacy_rendered.stdout, legacy_rendered.stderr)
        assert (root / ".claude" / "runs" / "legacy-run" / "trace.html").is_file()
    print("  ok trace_uses_contextd_runs_and_renderer_fallback")


def test_package_release_dry_run_shape() -> None:
    proc = subprocess.run(
        ["bash", str(ROOT / "scripts" / "package-release.sh"), "--dry-run"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    stage = None
    for line in proc.stdout.splitlines():
        candidate = Path(line.strip())
        if candidate.name == "wiki-template" and candidate.is_dir():
            stage = candidate
    assert stage is not None, proc.stdout
    try:
        assert (stage / "workspaces" / "default" / "workspace.md").is_file()
        assert (stage / "workspaces" / "README.md").is_file()
        assert not (stage / "build").exists()
        assert not (stage / "dist").exists()
        assert not (stage / "contextd.egg-info").exists()
        version_file = stage / "scripts" / "_version.py"
        assert version_file.is_file()
        assert "__version__ =" in version_file.read_text(encoding="utf-8")
        staged_version = (stage / "VERSION").read_text(encoding="utf-8").splitlines()[0].strip()
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "root=Path.cwd(); "
                    "sys.path.insert(0, str(root/'scripts')); "
                    "from lib import contextd_version; "
                    "print(contextd_version.get_version("
                    "package_name='contextd-missing-for-test', start_path=root))"
                ),
            ],
            cwd=str(stage),
            text=True,
            capture_output=True,
        )
        assert probe.returncode == 0, (probe.stdout, probe.stderr)
        assert probe.stdout.strip() == staged_version, probe.stdout
        assert contextd_version.get_version(
            package_name="contextd-missing-for-test",
            start_path=stage,
        ) != "0.0.0-dev"
        committed_manifest = json.loads((ROOT / ".contextd" / "manifest.json").read_text(encoding="utf-8"))
        assert committed_manifest == generate_manifest.generate_manifest(), committed_manifest
        manifest = json.loads((stage / ".contextd" / "manifest.json").read_text(encoding="utf-8"))
        assert manifest == generate_manifest.generate_manifest(), manifest
        assert not (stage / ".contextd" / "runs").exists()
        assert not (stage / ".contextd" / "context").exists()
    finally:
        shutil.rmtree(stage.parent, ignore_errors=True)
    print("  ok package_release_dry_run_shape")


def run() -> int:
    tests = [
        test_contextd_config_wins,
        test_legacy_claude_still_resolves,
        test_pack_override_replace_semantics,
        test_missing_workspace_lists_available,
        test_context_artifact_and_materialized_pack,
        test_context_snapshot_source_coherence_and_raw_hashes,
        test_materialization_rejects_foreign_knowledge_root,
        test_synapse_lookups_are_reused_for_replacement_expansion,
        test_lib_modules_have_one_canonical_identity,
        test_synapse_lifecycle_graph,
        test_synapse_rejects_invalid_edges_and_workspace_escape,
        test_context_projection_expands_replacement_and_warns_stale,
        test_budget_report_and_explain_trace,
        test_manifest_v3_scopes_pack_knowledge_and_budget,
        test_policy_check_pass_and_failures,
        test_pack_validation_catches_bad_pack_api,
        test_pack_validation_warns_on_documented_rules_without_script,
        test_pack_validation_v2_quality_contract,
        test_pack_validation_v3_catches_knowledge_and_adapter_drift,
        test_golden_eval_passes_and_fails_deterministically,
        test_non_code_product_pack_retrieval,
        test_ba_unknown_domain_becomes_gap,
        test_ux_pack_retrieves_design_sections,
        test_qc_evidence_retrieval_excludes_raw_sources,
        test_retrieval_map_safety_and_redaction,
        test_evidence_glob_excludes_raw_sources,
        test_contract_index_missing_target_is_gap,
        test_contract_path_index_and_fallback,
        test_thesis_hardening_docs_and_release_mapping,
        test_onboarding_and_readme_docs_consistency,
        test_default_contract_index_and_demo_golden_fixture,
        test_doctor_and_adapter_drift_checks,
        test_codex_agents_use_json_canonical_artifact,
        test_pack_ui_ux_rules,
        test_pack_operator_steering_wayfinding_rules,
        test_pack_devops_iac.test_pack_devops_iac_rules,
        test_stdio_utf8_under_legacy_codepage,
        test_intent_classification_word_boundaries,
        test_pack_keyword_special_chars,
        test_cli_ux_help_and_aliases,
        test_cli_smoke,
        test_mcp_server_smoke,
        test_installer_dry_run_knowledge_root,
        test_migrate_config_roundtrip_and_no_clobber,
        test_trace_uses_contextd_runs_and_renderer_fallback,
        test_package_release_dry_run_shape,
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
