"""Integration tests require the full repository checkout (run in CI)."""
from __future__ import annotations
from dataclasses import replace
from datetime import date
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmd_graph_project
from lib import synapse_engine
from lib.graph_projection import ProjectionRequest

ROOT = Path(__file__).resolve().parents[1]


class SnapshotIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ws = self.root / "workspaces/demo"
        self.ws.mkdir(parents=True)
        (self.root / ".contextd").mkdir()
        (self.root / ".contextd/config.json").write_text(json.dumps({
            "workspace": "demo", "knowledge_root": ".", "packs": []}), encoding="utf-8")
        (self.ws / "workspace.md").write_text("# Demo\n\n## Packs\n\n(none)\n", encoding="utf-8")
        self.write_node("a", "knowledge_role: strategy\nregions: [backend]\nrelations:\n  - type: depends_on\n    target: b\n")
        self.write_node("b", "knowledge_role: mechanism\nregions: [backend]\n")

    def write_node(self, name, extra=""):
        path = self.ws / f"{name}.md"
        path.write_text(f"---\ntype: Pattern\nstatus: stable\nnode_id: {name}\n{extra}---\n\n# {name}\n", encoding="utf-8")
        return path

    def snapshot(self):
        return synapse_engine.build_synapse_snapshot(self.root, "demo", as_of=date(2026, 9, 16))

    def cli(self, *extra):
        env = dict(os.environ, HOME=str(self.root / "isolated-home"))
        return subprocess.run([sys.executable, str(ROOT / "scripts/cmd_graph_project.py"),
                               "--cwd", str(self.root), "--seed", "a", "--as-of", "2026-09-16", *extra],
                              capture_output=True, text=True, env=env, timeout=30)

    def test_real_snapshot_frontmatter_and_schema(self):
        import jsonschema
        artifact = cmd_graph_project.project_snapshot(self.snapshot(), ProjectionRequest(("a",)))
        self.assertEqual([n["knowledge_role"] for n in artifact["nodes"]], ["strategy", "mechanism"])
        schema = json.loads((ROOT / "templates/graph-projection.schema.json").read_text())
        jsonschema.validate(artifact, schema, format_checker=jsonschema.FormatChecker())

    def test_projection_never_rereads_sources(self):
        snapshot = self.snapshot()
        with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("second source read")), \
             mock.patch.object(Path, "read_text", side_effect=AssertionError("second source read")):
            artifact = cmd_graph_project.project_snapshot(snapshot, ProjectionRequest(("a",)))
        self.assertEqual(len(artifact["nodes"]), 2)

    def test_source_changes_require_next_build(self):
        snapshot = self.snapshot()
        original = cmd_graph_project.project_snapshot(snapshot, ProjectionRequest(("a",)))
        self.write_node("b", "knowledge_role: evidence\n")
        self.assertEqual(cmd_graph_project.project_snapshot(snapshot, ProjectionRequest(("a",))), original)
        changed = cmd_graph_project.project_snapshot(self.snapshot(), ProjectionRequest(("a",)))
        self.assertNotEqual(original["projection_hash"], changed["projection_hash"])

    def test_tampered_graph_hash_is_rejected(self):
        snapshot = self.snapshot()
        snapshot.graph["nodes"][0]["lifecycle"] = "deprecated"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            cmd_graph_project.project_snapshot(snapshot, ProjectionRequest(("a",)))

    def test_mismatched_retained_source_is_rejected(self):
        snapshot = self.snapshot()
        path = next(node["path"] for node in snapshot.graph["nodes"] if node["id"] == "a")
        bad_sources = dict(snapshot.sources_by_path)
        bad_sources[path] = replace(bad_sources[path], source_hash="0" * 64)
        with self.assertRaisesRegex(ValueError, "source record"):
            cmd_graph_project.project_snapshot(replace(snapshot, sources_by_path=bad_sources), ProjectionRequest(("a",)))

    def test_graph_errors_refuse_projection(self):
        self.write_node("b", "relations:\n  - type: depends_on\n    target: workspace://other/a\n")
        with self.assertRaisesRegex(ValueError, "Graph contains errors"):
            cmd_graph_project.project_snapshot(self.snapshot(), ProjectionRequest(("a",)))

    def test_raw_evidence_and_runtime_files_not_indexed(self):
        for relative in [".observations/secret.md", "evidence/sources/private/raw.md"]:
            path = self.ws / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("---\nnode_id: private\n---\nprivate-marker", encoding="utf-8")
        snapshot = self.snapshot()
        self.assertNotIn("private", {n["id"] for n in snapshot.graph["nodes"]})

    def test_symlink_escape_is_rejected_without_projection(self):
        foreign = self.root / "workspaces/other"
        foreign.mkdir()
        target = foreign / "private.md"
        target.write_text("---\nnode_id: foreign\n---\n", encoding="utf-8")
        try:
            (self.ws / "escape.md").symlink_to(target)
        except OSError as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")
        with self.assertRaisesRegex(ValueError, "Graph contains errors"):
            cmd_graph_project.project_snapshot(self.snapshot(), ProjectionRequest(("a",)))

    def test_cli_is_read_only_and_deterministic(self):
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
        first, second = self.cli(), self.cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertFalse(json.loads(first.stdout)["execution_authorized"])
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*")))

    def test_cli_warns_by_default_and_strict_fails(self):
        normal = self.cli("--depth", "0")
        strict = self.cli("--depth", "0", "--strict")
        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertEqual(strict.returncode, 1, strict.stderr)
        self.assertEqual(json.loads(normal.stdout)["summary"]["required_neighbor_gaps"], 1)

    def test_cli_invalid_bounds_fail_before_build(self):
        result = self.cli("--depth", "-1")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_cli_workspace_traversal_is_refused(self):
        result = self.cli("--workspace", "../other")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
