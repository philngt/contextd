#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime-neutral contextd tests.

Run:
    python scripts/test_contextd_runtime.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "lib"))

import cmd_doctor  # noqa: E402
import cmd_eval  # noqa: E402
import contextd_version  # noqa: E402
import generate_manifest  # noqa: E402
import cmd_resolve  # noqa: E402
import render_runtime  # noqa: E402
from lib import contextd_resolver, pack_validation, task_context_engine  # noqa: E402


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
               "name: pack-bad\nversion: 1.0.0\ndescription: Bad\ncomponents:\n  - known\nkeywords:\n  unknown: [bad]\nfiles:\n  missing: missing.md\n")
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
    print("  ok pack_validation_catches_bad_pack_api")


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

        _write(fixture_dir / "fail.json", json.dumps({
            "id": "fail-missing-doc",
            "task": "Implement demo feature",
            "workspace": "default",
            "packs": ["pack-demo"],
            "expected_docs": ["workspaces/default/missing.md"],
        }))
        fail_path = root / ".contextd" / "runs" / "eval-fail.json"
        assert cmd_eval.run(golden=True, workspace="default", cwd=str(root),
                            fmt="json", output=str(fail_path)) == 1
        failed = json.loads(fail_path.read_text(encoding="utf-8"))
        assert failed["status"] == "error", failed
        assert failed["summary"]["failed"] == 1, failed
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
    assert 'version = "1.3.2"' in pyproject, pyproject
    actual_version = contextd_version.get_version(start_path=ROOT)
    assert actual_version == "1.3.2", actual_version
    print("  ok thesis_hardening_docs_and_release_mapping")


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
    print("  ok doctor_and_adapter_drift_checks")


def test_cli_smoke() -> None:
    commands = [
        [sys.executable, "-m", "scripts.cli", "resolve", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "find", "citation", "--limit", "1", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "context", "design context", "--format", "json", "--no-materialize"],
        [sys.executable, "-m", "scripts.cli", "doctor", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "explain", "design context", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "pack-validate", "--all", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "policy-check", "debug context quality", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "eval", "--golden", "--workspace", "default", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "contract-path", "citation-format.v1", "--format", "json"],
        [sys.executable, "-m", "scripts.cli", "mcp-config", "--client", "codex",
         "--knowledge-root", str(ROOT), "--workspace", "default"],
    ]
    with tempfile.TemporaryDirectory() as td:
        commands.append([
            sys.executable, "-m", "scripts.cli", "export", "--runtime", "cursor", "--output", td,
        ])
        for cmd in commands:
            proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
            assert proc.returncode == 0, (cmd, proc.stdout, proc.stderr)
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
                    "sys.path.insert(0, str(root/'scripts'/'lib')); "
                    "import contextd_version; "
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
        test_budget_report_and_explain_trace,
        test_policy_check_pass_and_failures,
        test_pack_validation_catches_bad_pack_api,
        test_golden_eval_passes_and_fails_deterministically,
        test_non_code_product_pack_retrieval,
        test_ba_unknown_domain_becomes_gap,
        test_ux_pack_retrieves_design_sections,
        test_qc_evidence_retrieval_excludes_raw_sources,
        test_retrieval_map_safety_and_redaction,
        test_contract_index_missing_target_is_gap,
        test_contract_path_index_and_fallback,
        test_thesis_hardening_docs_and_release_mapping,
        test_default_contract_index_and_demo_golden_fixture,
        test_doctor_and_adapter_drift_checks,
        test_cli_smoke,
        test_mcp_server_smoke,
        test_installer_dry_run_knowledge_root,
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
