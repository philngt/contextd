#!/usr/bin/env python3
"""Focused path-confinement tests for contextd runtime boundaries.

Run:
    python3 scripts/test_context_security.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "lib"))

import pack_loader  # noqa: E402
import detect_repetition  # noqa: E402
from lib import context_security, pack_validation  # noqa: E402


HOOK_SCRIPT = HERE / "detect_repetition.py"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _raises_value_error(fn) -> ValueError:
    try:
        fn()
    except ValueError as exc:
        return exc
    raise AssertionError("expected ValueError")


def _raises_runtime_error(fn) -> RuntimeError:
    try:
        fn()
    except RuntimeError as exc:
        return exc
    raise AssertionError("expected RuntimeError")


def _symlink(link: Path, target: Path, *, directory: bool = False) -> bool:
    try:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target, target_is_directory=directory)
        return True
    except (NotImplementedError, OSError):
        return False


def test_root_relative_posix_is_canonical_and_never_absolute() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        root = base / "knowledge"
        doc = root / "nested" / "doc.md"
        _write(doc, "# Doc\n")

        assert context_security.root_relative_posix(doc, root) == "nested/doc.md"
        outside = base / "outside.md"
        _write(outside, "outside\n")
        _raises_value_error(
            lambda: context_security.root_relative_posix(outside, root)
        )

        alias = base / "knowledge-alias"
        if _symlink(alias, root, directory=True):
            assert context_security.root_relative_posix(
                alias / "nested" / "doc.md", alias
            ) == "nested/doc.md"
    print("  ok root_relative_posix_is_canonical_and_never_absolute")


def test_confined_child_rejects_portable_escape_forms() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        valid = context_security.confined_child(root, "nested/file.md")
        assert valid == (root / "nested" / "file.md").resolve()

        unsafe = [
            "",
            "../outside",
            "nested/../../outside",
            r"..\outside",
            "/etc/passwd",
            "C:/Windows/System32",
            r"C:\Windows\System32",
            "C:drive-relative",
            r"\\server\share\file",
            r"\rooted\file",
            "safe.txt:stream",
            "file:relative",
            "~/.ssh/id_rsa",
            "./nested/file.md",
            "nested/\x00file.md",
            "CON/file.md",
            "nested/NUL.txt",
            "nested/trailing.",
        ]
        for value in unsafe:
            _raises_value_error(
                lambda value=value: context_security.confined_child(root, value)
            )

        assert context_security.reject_unsafe_entry("{ws}/patterns/*.md") is None
        for value in unsafe:
            assert context_security.reject_unsafe_entry(value), value
    print("  ok confined_child_rejects_portable_escape_forms")


def test_named_roots_reject_symlink_aliases() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "knowledge"
        real_ws = root / "workspaces" / "real"
        real_pack = root / "packs" / "pack-real"
        real_ws.mkdir(parents=True)
        real_pack.mkdir(parents=True)

        ws_alias = root / "workspaces" / "alias"
        pack_alias = root / "packs" / "pack-alias"
        ws_linked = _symlink(ws_alias, real_ws, directory=True)
        pack_linked = _symlink(pack_alias, real_pack, directory=True)
        if ws_linked:
            _raises_value_error(
                lambda: context_security.workspace_dir(root, "alias")
            )
        if pack_linked:
            _raises_value_error(
                lambda: context_security.pack_dir(root, "pack-alias")
            )

        outside = Path(td) / "outside-workspace"
        outside.mkdir()
        outside_alias = root / "workspaces" / "outside-alias"
        if _symlink(outside_alias, outside, directory=True):
            _raises_value_error(
                lambda: context_security.workspace_dir(root, "outside-alias")
            )

        for invalid_name in (" CON", "CON", "aux.txt", "name."):
            _, error = context_security.validate_context_name(
                invalid_name, "workspace"
            )
            assert error, invalid_name
    print("  ok named_roots_reject_symlink_aliases")


def test_path_policy_checks_logical_and_resolved_targets() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        secret = root / "secrets" / "note.md"
        raw = root / "workspaces" / "default" / "evidence" / "sources" / "e1" / "raw.md"
        normal = root / "docs" / "normal.md"
        _write(secret, "secret\n")
        _write(raw, "raw\n")
        _write(normal, "normal\n")

        assert "secret directory" in str(context_security.path_policy_reason(secret))
        assert "raw evidence" in str(context_security.path_policy_reason(raw))
        assert context_security.path_policy_reason(normal) is None
        assert "raw evidence" in str(context_security.path_policy_reason(
            normal,
            logical_path=Path("workspaces/default/evidence/sources/e1/raw.md"),
        ))

        secret_link = root / "docs" / "safe-name.md"
        if _symlink(secret_link, secret):
            reason = context_security.path_policy_reason(
                secret_link, logical_path=Path("docs/safe-name.md")
            )
            assert reason and "resolved target" in reason and "secret directory" in reason

        raw_link = root / "docs" / "summary.md"
        if _symlink(raw_link, raw):
            reason = context_security.path_policy_reason(
                raw_link, logical_path=Path("docs/summary.md")
            )
            assert reason and "resolved target" in reason and "raw evidence" in reason
    print("  ok path_policy_checks_logical_and_resolved_targets")


def test_pack_validator_script_cannot_escape_pack() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        pack_root = root / "packs" / "pack-demo"
        outside_script = root / "outside.py"
        marker = root / "executed.txt"
        _write(
            outside_script,
            f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\nRULES = []\n",
        )

        traversal_pack = pack_loader.Pack(
            "pack-demo",
            pack_root,
            {"files": {"validator_script": "../../outside.py"}},
        )
        assert traversal_pack.file_path("validator_script") is None
        assert pack_loader.load_pack_validator_rules([traversal_pack]) == []
        assert not marker.exists()

        linked_rule = pack_root / "scripts" / "rules.py"
        if _symlink(linked_rule, outside_script):
            linked_pack = pack_loader.Pack(
                "pack-demo",
                pack_root,
                {"files": {"validator_script": "scripts/rules.py"}},
            )
            assert linked_pack.file_path("validator_script") is None
            assert pack_loader.load_pack_validator_rules([linked_pack]) == []
            assert not marker.exists()

        valid_root = root / "packs" / "pack-valid"
        _write(
            valid_root / "scripts" / "rules.py",
            "def rule(file_path, lines, ctx):\n    return []\nRULES = [rule]\n",
        )
        valid_pack = pack_loader.Pack(
            "pack-valid",
            valid_root,
            {"files": {"validator_script": "scripts/rules.py"}},
        )
        rules = pack_loader.load_pack_validator_rules([valid_pack])
        assert len(rules) == 1 and callable(rules[0])
    print("  ok pack_validator_script_cannot_escape_pack")


def test_pack_validation_rejects_requested_name_and_manifest_escape() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "packs").mkdir()
        outside = root / "outside.py"
        _write(outside, "RULES = []\n")

        invalid = pack_validation.validate_packs(root, pack_names=["../../outside"])
        assert invalid["status"] == "error", invalid
        assert any(issue["check"] == "pack.name" for issue in invalid["issues"])
        assert all(not Path(issue["path"]).is_absolute() for issue in invalid["issues"])

        pack_root = root / "packs" / "pack-bad"
        _write(
            pack_root / "pack.yaml",
            """name: pack-bad
version: 1.0.0
description: Bad fixture
components: [demo]
keywords:
  demo: [demo]
files:
  validator_script: ../../outside.py
""",
        )
        report = pack_validation.validate_packs(root, pack_names=["pack-bad"])
        assert report["status"] == "error", report
        assert any(
            issue["check"] == "pack.files" and "Unsafe file path" in issue["message"]
            for issue in report["issues"]
        ), report
    print("  ok pack_validation_rejects_requested_name_and_manifest_escape")


def test_pack_loader_fails_closed_for_missing_active_pack() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        workspace = root / "workspaces" / "default"
        _write(
            workspace / "workspace.md",
            "# Workspace\n\n## Packs\n\n- pack-missing\n",
        )
        error = _raises_runtime_error(
            lambda: pack_loader.load_packs_for_workspace(root, "default")
        )
        assert "missing or unsafe pack" in str(error), error

        _write(
            workspace / "workspace.md",
            "# Workspace\n\n## Packs\n\n- ../outside\n",
        )
        error = _raises_runtime_error(
            lambda: pack_loader.load_packs_for_workspace(root, "default")
        )
        assert "invalid active pack" in str(error), error

        _write(
            workspace / "workspace.md",
            "# Workspace\n\n## Packs\n\n- pack-missing\n",
        )

        outside_pack = root / "outside-pack"
        _write(outside_pack / "pack.yaml", "name: pack-missing\nversion: 1.0.0\n")
        alias = root / "packs" / "pack-missing"
        if _symlink(alias, outside_pack, directory=True):
            error = _raises_runtime_error(
                lambda: pack_loader.load_packs_for_workspace(root, "default")
            )
            assert "missing or unsafe pack" in str(error), error
            alias.unlink()

        _write(root / "outside.py", "RULES = []\n")
        _write(
            root / "packs" / "pack-missing" / "pack.yaml",
            """name: pack-missing
version: 1.0.0
components: [demo]
files:
  validator_script: ../../outside.py
""",
        )
        error = _raises_runtime_error(
            lambda: pack_loader.load_packs_for_workspace(root, "default")
        )
        assert "missing or unsafe pack" in str(error), error
    print("  ok pack_loader_fails_closed_for_missing_active_pack")


def _hook_env() -> dict[str, str]:
    env = os.environ.copy()
    env["REP_MIN_COUNT"] = "3"
    env["REP_JACCARD"] = "0.4"
    return env


def test_repetition_hook_refuses_observation_symlink_writes() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "project"
        workspace = root / "workspaces" / "default"
        outside = Path(td) / "outside-observations"
        outside.mkdir(parents=True)
        _write(workspace / "workspace.md", "# Workspace\n\n## Packs\n\n")
        _write(
            root / ".contextd" / "config.json",
            json.dumps({"workspace": "default", "knowledge_root": ".", "packs": []}),
        )

        observations = workspace / ".observations"
        if not _symlink(observations, outside, directory=True):
            print("  skip repetition_hook_refuses_observation_symlink_writes (symlink unavailable)")
            return

        proc = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            cwd=str(root),
            input=json.dumps({
                "prompt": "review repeated build workflow",
                "cwd": str(root),
            }),
            text=True,
            capture_output=True,
            env=_hook_env(),
        )
        assert proc.returncode == 0, (proc.stdout, proc.stderr)
        assert not list(outside.iterdir()), list(outside.iterdir())
        assert "unsafe observations path" in proc.stderr, proc.stderr
    print("  ok repetition_hook_refuses_observation_symlink_writes")


def test_observation_file_rechecks_parent_alias() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "knowledge"
        workspace = root / "workspaces" / "default"
        outside = Path(td) / "outside"
        workspace.mkdir(parents=True)
        outside.mkdir()
        base = detect_repetition.obs_dir(root, "default")
        base.mkdir()
        base.rmdir()
        if not _symlink(base, outside, directory=True):
            print("  skip observation_file_rechecks_parent_alias (symlink unavailable)")
            return
        _raises_value_error(
            lambda: detect_repetition._observation_file(base, "prompts.jsonl")  # noqa: SLF001
        )
    print("  ok observation_file_rechecks_parent_alias")


def test_repetition_hook_refuses_observation_file_symlink_writes() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "project"
        workspace = root / "workspaces" / "default"
        observations = workspace / ".observations"
        outside_log = Path(td) / "outside-prompts.jsonl"
        _write(workspace / "workspace.md", "# Workspace\n\n## Packs\n\n")
        _write(
            root / ".contextd" / "config.json",
            json.dumps({"workspace": "default", "knowledge_root": ".", "packs": []}),
        )
        observations.mkdir(parents=True)
        outside_log.write_text("sentinel\n", encoding="utf-8")
        if not _symlink(observations / "prompts.jsonl", outside_log):
            print("  skip repetition_hook_refuses_observation_file_symlink_writes (symlink unavailable)")
            return

        proc = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            cwd=str(root),
            input=json.dumps({
                "prompt": "review repeated build workflow",
                "cwd": str(root),
            }),
            text=True,
            capture_output=True,
            env=_hook_env(),
        )
        assert proc.returncode == 0, (proc.stdout, proc.stderr)
        assert outside_log.read_text(encoding="utf-8") == "sentinel\n"
        assert "unsafe observations path" in proc.stderr, proc.stderr
    print("  ok repetition_hook_refuses_observation_file_symlink_writes")


def run() -> int:
    tests = [
        test_root_relative_posix_is_canonical_and_never_absolute,
        test_confined_child_rejects_portable_escape_forms,
        test_named_roots_reject_symlink_aliases,
        test_path_policy_checks_logical_and_resolved_targets,
        test_pack_validator_script_cannot_escape_pack,
        test_pack_validation_rejects_requested_name_and_manifest_escape,
        test_pack_loader_fails_closed_for_missing_active_pack,
        test_repetition_hook_refuses_observation_symlink_writes,
        test_observation_file_rechecks_parent_alias,
        test_repetition_hook_refuses_observation_file_symlink_writes,
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            print(f"  FAIL {test.__name__}: {exc}", file=sys.stderr)
            failed += 1
        except Exception as exc:
            print(
                f"  ERROR {test.__name__}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            failed += 1
    if failed:
        print(f"\n{failed} test(s) failed", file=sys.stderr)
        return 1
    print(f"\nAll {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(run())
