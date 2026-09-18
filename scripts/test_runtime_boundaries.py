"""Regressions for compiled identity, write preflight and export boundaries."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import render_runtime as runtime
from lib import task_context_engine as engine
from lib.context_payload import compiled_sources
from lib.context_security import read_safe_text


class RuntimeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="contextd-boundary-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "knowledge"
        self.root.mkdir()
        self.ws = self.root / "workspaces" / "default"
        self.ws.mkdir(parents=True)
        self.write("workspaces/default/workspace.md", "# Default\n\n## Purpose\nTest workspace.\n")
        self.write("workspaces/default/platform/patterns/demo.md", "# Demo\n\n## Flow\nImplement demo safely.\n")

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def doc(self, name, content="example", category="pattern"):
        return {"path": name, "category": category, "sections": ["Flow"],
                "content": content, "source_hash": "a" * 64}

    def key(self, docs, static=None):
        return engine._build_context_pack("default", [], docs, static)["packKey"]

    def build(self):
        return engine.build_context_snapshot(
            "implement demo feature", self.root, "default", [], project_dir=self.root,
        )

    def test_content_change_rotates_unprofiled_identity(self):
        self.assertNotEqual(self.key([self.doc("demo.md", "old")]),
                            self.key([self.doc("demo.md", "new")]))

    def test_section_change_rotates_identity(self):
        a = self.doc("demo.md")
        b = {**a, "sections": ["Failure"]}
        self.assertNotEqual(self.key([a]), self.key([b]))

    def test_output_order_rotates_identity(self):
        a, b = self.doc("a.md"), self.doc("b.md")
        self.assertNotEqual(self.key([a, b]), self.key([b, a]))

    def test_repeated_projection_is_stable(self):
        docs = [self.doc("a.md"), self.doc("b.md")]
        self.assertEqual(self.key(docs), self.key(copy.deepcopy(docs)))

    def test_static_duplicate_owns_identity_and_render(self):
        static = self.doc("demo.md", "static wins")
        referenced = self.doc("demo.md", "unused duplicate")
        self.assertEqual(compiled_sources([static], [referenced]), [static])
        self.assertEqual(self.key([referenced], [static]), self.key([], [static]))
        ref = engine._build_context_pack("default", [], [referenced], [static])
        text = engine._pack_markdown({"workspace": "default", "contextPack": ref,
                                     "static_context": [static], "referenced_docs": [referenced]})
        self.assertEqual(text.count("static wins"), 1)
        self.assertNotIn("unused duplicate", text)

    def test_all_rendered_categories_are_in_source_manifest(self):
        doc = self.doc("operator.md", category="operator")
        ref = engine._build_context_pack("default", [], [doc])
        self.assertEqual([s["path"] for s in ref["sources"]], ["operator.md"])

    def test_compiled_budget_matches_deduplicated_view(self):
        a, b = self.doc("a.md", "1234"), self.doc("b.md", "12345678")
        report = engine._finalize_budget_report({}, [a, b], [a])
        self.assertEqual(report["compiled_docs"], 2)
        self.assertEqual(report["deduplicated_overlap_docs"], 1)
        self.assertEqual(report["estimated_tokens_total"], 3)

    def test_mutated_payload_is_rejected_without_writes(self):
        artifact, snapshot = self.build()
        artifact["static_context"][0]["content"] += "\nmutation"
        output = self.root / "output"
        with self.assertRaisesRegex(ValueError, "projection changed"):
            engine.materialize_context(artifact, output, synapse_snapshot=snapshot)
        self.assertFalse(output.exists())

    def test_mutated_source_manifest_is_rejected_without_writes(self):
        artifact, snapshot = self.build()
        artifact["contextPack"]["sources"] = []
        output = self.root / "output"
        with self.assertRaisesRegex(ValueError, "projection changed"):
            engine.materialize_context(artifact, output, synapse_snapshot=snapshot)
        self.assertFalse(output.exists())

    def test_legacy_identity_requires_explicit_rebuild(self):
        artifact, _ = self.build()
        del artifact["contextPack"]["identity_version"]
        output = self.root / "output"
        with self.assertRaisesRegex(ValueError, "rebuild"):
            engine.materialize_context(artifact, output)
        self.assertFalse(output.exists())

    def test_snapshot_validation_exception_precedes_writes(self):
        artifact, snapshot = self.build()
        output = self.root / "output"
        with patch.object(engine.synapse_engine, "compute_synapse_hash", side_effect=ValueError("invalid graph")):
            with self.assertRaisesRegex(ValueError, "invalid graph"):
                engine.materialize_context(artifact, output, synapse_snapshot=snapshot)
        self.assertFalse(output.exists())

    def test_render_exception_precedes_writes(self):
        artifact, snapshot = self.build()
        output = self.root / "output"
        with patch.object(engine, "render_markdown", side_effect=ValueError("invalid render")):
            with self.assertRaisesRegex(ValueError, "invalid render"):
                engine.materialize_context(artifact, output, synapse_snapshot=snapshot)
        self.assertFalse(output.exists())

    def test_materialization_does_not_rescan_or_mutate_input(self):
        artifact, snapshot = self.build()
        before = copy.deepcopy(artifact)
        output = self.root / "output"
        with patch.object(Path, "read_bytes", side_effect=AssertionError("rescan")), \
             patch.object(Path, "read_text", side_effect=AssertionError("rescan")):
            result = engine.materialize_context(artifact, output, synapse_snapshot=snapshot)
        self.assertEqual(artifact, before)
        self.assertEqual(result["synapse"]["status"], "materialized")
        self.assertTrue((output / result["contextPack"]["compiledRef"]).is_file())

    def test_mismatched_optional_snapshot_keeps_documented_drift_status(self):
        artifact, snapshot = self.build()
        snapshot = copy.deepcopy(snapshot)
        snapshot["synapse_hash"] = "0" * 64
        output = self.root / "output"
        result = engine.materialize_context(artifact, output, synapse_snapshot=snapshot)
        self.assertEqual(result["synapse"]["status"], "drifted")
        self.assertIsNone(result["synapse"]["ref"])
        self.assertFalse((output / ".contextd/context/synapse.json").exists())
        self.assertTrue((output / ".contextd/context/current-task.json").is_file())

    def test_safe_reader_redacts_inline_secrets(self):
        source = self.write("workspaces/default/runbooks/demo.md", "password: synthetic-test-value\n")
        text = read_safe_text(source, self.ws)
        self.assertNotIn("synthetic-test-value", text)
        self.assertIn("<REDACTED-SECRET>", text)

    def test_secret_directory_is_not_read(self):
        source = self.write("workspaces/default/secrets/demo.md", "secret marker")
        with patch.object(Path, "read_text", side_effect=AssertionError("unsafe read")):
            self.assertIsNone(read_safe_text(source, self.ws))

    def test_outside_source_is_not_read(self):
        source = self.write("outside.md", "outside marker")
        with patch.object(Path, "read_text", side_effect=AssertionError("unsafe read")):
            self.assertIsNone(read_safe_text(source, self.ws))

    def symlink(self, link, target):
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            link.symlink_to(target, target_is_directory=target.is_dir())
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")

    def test_cross_workspace_symlink_omitted_from_plain_export(self):
        foreign = self.write("workspaces/foreign/private.md", "FOREIGN-MARKER")
        self.symlink(self.ws / "platform/patterns/leak.md", foreign)
        files = runtime._collect_workspace_files(self.root, "default")
        self.assertNotIn("FOREIGN-MARKER", "\n".join(files.values()))
        self.assertFalse(any("leak.md" in name for name in files))

    def test_plain_export_redacts_workspace_prose(self):
        self.write("workspaces/default/runbooks/demo.md", "api_key: synthetic-test-value\n")
        files = runtime.render_plain({}, "default", self.root, [], False)
        self.assertNotIn("synthetic-test-value", "\n".join(files.values()))

    def test_export_rejects_workspace_override_before_renderer(self):
        resolved = {"knowledge_root": str(self.root), "workspace": "default", "packs": []}
        with patch.object(runtime, "_load_manifest", return_value={}), \
             patch.object(runtime.cmd_resolve, "resolve", return_value=resolved):
            for invalid in ("../foreign", "missing", "/tmp/foreign"):
                with self.subTest(invalid=invalid):
                    with self.assertRaisesRegex(ValueError, "workspace"):
                        runtime.render("cursor", workspace=invalid)

    def pack(self, version=3, knowledge="knowledge.md"):
        return self.write("packs/pack-demo/pack.yaml", (
            f"name: pack-demo\nmanifest_version: {version}\nversion: 1.0.0\n"
            f"files:\n  knowledge: {knowledge}\n"))

    def test_v3_bundle_uses_canonical_knowledge_not_legacy_prose(self):
        self.pack()
        self.write("packs/pack-demo/knowledge.md", "# Canonical\nNEW-MARKER")
        self.write("packs/pack-demo/agents/constraints.md", "OLD-MARKER")
        files = runtime._collect_pack_files(self.root, "pack-demo")
        text = "\n".join(files.values())
        self.assertIn("NEW-MARKER", text)
        self.assertNotIn("OLD-MARKER", text)

    def test_v2_bundle_keeps_legacy_prose(self):
        self.pack(version=2)
        self.write("packs/pack-demo/agents/constraints.md", "V2-MARKER")
        self.assertIn("V2-MARKER", "\n".join(runtime._collect_pack_files(self.root, "pack-demo").values()))

    def test_unsafe_v3_knowledge_does_not_fall_back_to_legacy(self):
        self.pack(knowledge="../../outside.md")
        self.write("outside.md", "OUTSIDE-MARKER")
        self.write("packs/pack-demo/agents/constraints.md", "OLD-MARKER")
        self.assertEqual(runtime._collect_pack_files(self.root, "pack-demo"), {})

    def test_v3_knowledge_symlink_cannot_escape_pack(self):
        self.pack()
        foreign = self.write("packs/pack-other/private.md", "OTHER-PACK-MARKER")
        self.symlink(self.root / "packs/pack-demo/knowledge.md", foreign)
        text = "\n".join(runtime._collect_pack_files(self.root, "pack-demo").values())
        self.assertNotIn("OTHER-PACK-MARKER", text)

    def test_invalid_pack_name_cannot_escape_packs_directory(self):
        for name in ("../default", "/tmp/pack", "..\\default"):
            self.assertEqual(runtime._collect_pack_files(self.root, name), {})

    def test_engine_prose_uses_redaction(self):
        self.write("agents/constraints.md", "token: synthetic-test-value")
        self.assertNotIn("synthetic-test-value", "\n".join(runtime._collect_engine_files(self.root).values()))

    def test_bootstrap_adapter_does_not_read_or_select_sources(self):
        with patch.object(Path, "read_text", side_effect=AssertionError("independent retrieval")):
            files = runtime.render_codex_instructions({}, "default", self.root, [], True)
        text = files[".codex/instructions.md"]
        self.assertIn("contextd context", text)
        self.assertNotIn("Implement demo safely", text)


    def test_unserializable_synapse_is_rejected_before_writes(self):
        artifact, snapshot = self.build()
        snapshot = copy.deepcopy(snapshot)
        snapshot["diagnostics"].append({"bad": object()})
        output = self.root / "output"
        with self.assertRaises(TypeError):
            engine.materialize_context(artifact, output, synapse_snapshot=snapshot)
        self.assertFalse(output.exists())

    def test_nonregular_source_is_not_read(self):
        source = self.write("workspaces/default/runbooks/demo.md", "safe")
        with patch.object(Path, "is_file", return_value=False), \
             patch.object(Path, "read_text", side_effect=AssertionError("nonregular read")):
            self.assertIsNone(read_safe_text(source, self.ws))

    def test_workspace_bundle_accepts_relative_knowledge_root(self):
        import os
        relative = Path(os.path.relpath(self.root, Path.cwd()))
        self.assertEqual(runtime._collect_workspace_files(relative, "default"),
                         runtime._collect_workspace_files(self.root, "default"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
