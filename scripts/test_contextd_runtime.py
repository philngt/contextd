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
        assert not (stage / "scripts" / "_version.py").exists()
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
        test_contract_index_missing_target_is_gap,
        test_contract_path_index_and_fallback,
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
