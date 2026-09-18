"""Regression coverage for the staged runtime/engine boundary refactor."""
from __future__ import annotations
import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cmd_task_context
import mcp_server
import pack_loader
import render_runtime
from lib import contextd_resolver as resolver, task_context_engine as engine


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="contextd-simplify-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("workspaces/default/workspace.md", "# Default\n\n## Packs\n- pack-ws\n")
        self.write("workspaces/default/platform/patterns/demo.md", "# Demo\n\n## Flow\nImplement demo.\n")
        self.write("workspaces/other/workspace.md", "# Other\n\n## Packs\n- pack-other\n")
        self.write(".contextd/config.json", json.dumps({"workspace": "default", "knowledge_root": ".", "packs": ["pack-project"]}))
        for name in ("pack-ws", "pack-project", "pack-other"):
            self.write(f"packs/{name}/pack.yaml", f"name: {name}\nmanifest_version: 2\n")

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class ResolutionTests(Fixture):
    def test_project_pack_list_replaces_workspace_defaults(self):
        state = resolver.resolve_request(cwd=self.root)
        self.assertEqual(state.packs, ["pack-project"])
        self.assertEqual(state.knowledge_root, self.root)

    def test_explicit_same_workspace_uses_workspace_pack_defaults(self):
        state = resolver.resolve_request(cwd=self.root, workspace="default")
        self.assertEqual(state.packs, ["pack-ws"])

    def test_other_workspace_override_is_consistent(self):
        state = resolver.resolve_request(cwd=self.root, workspace="other")
        self.assertEqual(state.packs, ["pack-other"])
        self.assertEqual(state.workspace, "other")

    def test_mcp_uses_same_resolved_request(self):
        options = mcp_server.ServerOptions(cwd=self.root)
        for workspace in (None, "default", "other"):
            with self.subTest(workspace=workspace):
                expected = resolver.resolve_request(cwd=self.root, workspace=workspace)
                self.assertEqual(mcp_server.resolve_state(options, workspace=workspace, require_workspace=True), expected)

    def test_config_free_explicit_root_and_workspace(self):
        clean = self.root / "clean"
        clean.mkdir()
        with patch.object(resolver, "find_config", return_value=(None, [])):
            state = resolver.resolve_request(cwd=clean, knowledge_root=self.root, workspace="default")
        self.assertEqual(state.packs, ["pack-ws"])

    def test_explicit_workspace_recovers_missing_config_workspace(self):
        self.write(".contextd/config.json", json.dumps({"knowledge_root": "."}))
        state = resolver.resolve_request(cwd=self.root, workspace="default")
        self.assertEqual(state.workspace, "default")

    def test_invalid_workspace_rejected_consistently(self):
        for value in ("../other", "/tmp/outside", "missing", ""):
            with self.subTest(value=value):
                with self.assertRaises(resolver.ResolutionError):
                    resolver.resolve_request(cwd=self.root, workspace=value)
                with self.assertRaises(mcp_server.ToolExecutionError):
                    mcp_server.resolve_state(mcp_server.ServerOptions(cwd=self.root), workspace=value, require_workspace=True)

    def test_invalid_config_pack_name_rejected(self):
        self.write(".contextd/config.json", json.dumps({"workspace": "default", "knowledge_root": ".", "packs": ["../foreign"]}))
        with self.assertRaisesRegex(resolver.ResolutionError, "pack name"):
            resolver.resolve_request(cwd=self.root)

    def test_empty_pack_override_stays_empty(self):
        self.write(".contextd/config.json", json.dumps({"workspace": "default", "knowledge_root": ".", "packs": []}))
        self.assertEqual(resolver.resolve_request(cwd=self.root).packs, [])

    def test_cli_and_direct_compilation_have_same_payload(self):
        state = resolver.resolve_request(cwd=self.root, workspace="other")
        expected = engine.build_context_artifact("implement demo", self.root, "other", state.packs, project_dir=self.root, warnings=state.warnings)
        stdout = io.StringIO()
        with patch.object(resolver, "resolve_request", return_value=state), contextlib.redirect_stdout(stdout):
            self.assertEqual(cmd_task_context.run("implement demo", workspace="other", fmt="json"), 0)
        actual = json.loads(stdout.getvalue())
        actual.pop("generated_at")
        expected.pop("generated_at")
        self.assertEqual(actual, expected)

    def test_legacy_config_normalizes_to_same_canonical_state(self):
        (self.root / ".contextd/config.json").unlink()
        self.write(".claude/wiki.json", json.dumps({"workspace": "default", "wiki_root": ".", "packs": []}))
        state = resolver.resolve_request(cwd=self.root)
        self.assertEqual(state.knowledge_root, self.root)
        self.assertEqual(state.packs, [])


class ManifestTests(Fixture):
    def test_keyword_parser_uses_manifest_quoting(self):
        manifest = self.write("packs/pack-demo/pack.yaml", 'name: pack-demo\nkeywords:\n  special: ["a,b", "C#", "@RestController"]\n')
        self.assertEqual(engine._parse_pack_keywords(manifest)["special"], ["a,b", "C#", "@RestController"])

    def test_manifest_metadata_is_not_secret_redacted(self):
        manifest = self.write("packs/pack-demo/pack.yaml", 'name: pack-demo\nkeywords:\n  secret: [secret, token]\n')
        self.assertEqual(pack_loader.load_manifest(manifest)["keywords"]["secret"], ["secret", "token"])

    def test_workspace_pack_parser_has_one_implementation(self):
        with patch.object(resolver, "parse_workspace_packs", return_value=["pack-shared"]) as parser:
            self.assertEqual(pack_loader.parse_workspace_packs(self.root / "unused.md"), ["pack-shared"])
        parser.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
