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


class BuildBoundaryTests(Fixture):
    def build(self):
        return engine.build_context_result("implement demo", self.root, "default", [], project_dir=self.root)

    def test_trace_is_separate_from_canonical_artifact(self):
        result = self.build()
        self.assertNotIn("_selection_trace", result.artifact)
        self.assertTrue(result.selection_trace["considered_docs"])

    def test_legacy_tuple_api_is_compatible(self):
        artifact, graph = engine.build_context_snapshot("implement demo", self.root, "default", [], include_selection_trace=True)
        self.assertIn("_selection_trace", artifact)
        self.assertEqual(graph["synapse_hash"], artifact["synapse"]["synapse_hash"])

    def test_explain_does_not_modify_build_artifact(self):
        result = self.build()
        original = copy.deepcopy(result.artifact)
        with patch.object(engine, "build_context_result", return_value=result):
            explained = engine.build_context_explanation("implement demo", self.root, "default", [])
        self.assertEqual(result.artifact, original)
        self.assertEqual(explained["selection_trace"], result.selection_trace)

    def test_output_can_render_without_reading_sources(self):
        from lib import context_output
        result = self.build()
        with patch.object(Path, "read_text", side_effect=AssertionError("source reread")), patch.object(Path, "read_bytes", side_effect=AssertionError("source reread")):
            rendered = context_output.render_markdown(result.artifact)
        self.assertIn("Task Context", rendered)

    def test_compiler_has_no_filesystem_writer(self):
        import ast
        tree = ast.parse(Path(engine.__file__).read_text(encoding="utf-8"))
        writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {"write_text", "write_bytes", "mkdir"}]
        self.assertEqual(writes, [])

    def test_policy_checks_static_sources_and_total_budget(self):
        from lib import context_policy
        artifact = {"referenced_docs": [], "static_context": [{"path": "agents/constraints.md", "category": "engine-rule", "content": "x" * 400}], "budget_report": {"estimated_tokens_selected": 0, "estimated_tokens_total": 100}}
        rule = {"id": "cap", "deny": {"max_estimated_tokens": 50, "categories": ["engine-rule"]}}
        checks = {v["check"] for v in context_policy._evaluate_deny(rule, "test", artifact)}
        self.assertEqual(checks, {"deny.max_estimated_tokens", "deny.categories"})
        self.assertEqual(len(artifact["static_context"][0]["content"]), 400)

    def test_policy_deduplicates_same_static_and_referenced_path(self):
        from lib import context_policy
        doc = {"path": "same.md", "category": "pattern", "content": "example"}
        artifact = {"static_context": [doc], "referenced_docs": [doc]}
        violations = context_policy._evaluate_deny({"id": "cap", "deny": {"max_selected_docs": 1}}, "test", artifact)
        self.assertEqual(violations, [])

    def test_legacy_budget_report_fallback_remains_supported(self):
        from lib import context_policy
        artifact = {"referenced_docs": [], "budget_report": {"estimated_tokens_selected": 100}}
        violations = context_policy._evaluate_deny({"id": "cap", "deny": {"max_estimated_tokens": 50}}, "test", artifact)
        self.assertEqual(violations[0]["check"], "deny.max_estimated_tokens")


class PackPolicyTests(Fixture):
    def test_new_pack_controls_workstream_without_kernel_change(self):
        self.write("packs/pack-custom/pack.yaml", "name: pack-custom\nmanifest_version: 2\nworkstream: security\n")
        result = engine.build_context_result("inspect generic behavior", self.root, "default", ["pack-custom"])
        self.assertEqual(result.artifact["intent"]["workstream"], "security")

    def test_authored_metadata_wins_over_legacy_name(self):
        self.assertEqual(pack_loader.pack_workstream("pack-ui-ux", {"workstream": "product"}), "product")

    def test_old_manifest_keeps_compatibility_at_loader_boundary(self):
        self.assertEqual(pack_loader.pack_workstream("pack-ui-ux", {}), "design")
        self.assertIsNone(pack_loader.pack_workstream("pack-custom", {}))

    def test_invalid_workstream_fails_before_compilation(self):
        self.write("packs/pack-custom/pack.yaml", "name: pack-custom\nworkstream: not-a-workstream\n")
        with self.assertRaisesRegex(ValueError, "workstream"):
            engine.build_context_result("inspect", self.root, "default", ["pack-custom"])

    def test_kernel_has_no_named_pack_policy(self):
        text = Path(engine.__file__).read_text(encoding="utf-8")
        self.assertNotIn("PACK_WORKSTREAMS", text)
        self.assertNotIn('"pack-ui-ux"', text)
        self.assertNotIn('"pack-product"', text)

    def test_default_presets_keep_existing_budgets(self):
        from lib import context_defaults
        self.assertEqual(context_defaults.CATEGORY_BUDGETS["contract"], 2)
        self.assertEqual(context_defaults.PRIORITY["contract"], 0)
        self.assertEqual(context_defaults.INTENT_PRECEDENCE[0], "incident")

    def test_universal_guidance_has_no_backend_persona_or_output_template(self):
        root = Path(__file__).resolve().parent.parent
        text = (root / "agents/system-prompt.md").read_text(encoding="utf-8")
        self.assertNotIn("You are a senior backend engineer", text)
        self.assertNotIn("Structure every response as", text)
        self.assertIn("Backend Implementation Workflow", text)
        self.assertTrue((root / "agents/workflows/backend-implementation.md").is_file())

    def test_adapter_document_does_not_override_compiler(self):
        root = Path(__file__).resolve().parent.parent
        text = (root / "agents/pipeline/README.md").read_text(encoding="utf-8")
        self.assertNotIn("file này thắng", text)
        self.assertIn("Compiler + artifact schema", text)


class ManifestSchemaTests(unittest.TestCase):
    def test_schema_accepts_authored_workstream_and_rejects_unknown_value(self):
        import jsonschema
        root = Path(__file__).resolve().parent.parent
        schema = json.loads((root / "templates/pack.schema.json").read_text(encoding="utf-8"))
        manifest = pack_loader.load_manifest(root / "packs/pack-product/pack.yaml")
        jsonschema.Draft7Validator(schema).validate(manifest)
        manifest["workstream"] = "invalid-domain"
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft7Validator(schema).validate(manifest)

    def test_new_pack_template_declares_workstream(self):
        root = Path(__file__).resolve().parent.parent
        text = (root / "templates/pack.yaml").read_text(encoding="utf-8")
        self.assertIn("workstream: engineering", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
