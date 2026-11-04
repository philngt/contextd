#!/usr/bin/env python3
"""Task support, negative golden tasks, and a real external-project OES flow."""
from __future__ import annotations

import copy
from contextlib import redirect_stdout
from datetime import date
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from jsonschema import Draft7Validator

import cmd_eval
from lib import context_coverage, oes_context, task_context_engine as engine


ROOT = Path(__file__).resolve().parent.parent
TASK = "add idempotency to kafka consumer"
AS_OF = date(2026, 8, 20)
NO_MATCH = "No task-specific document matched"
SCHEMA = json.loads((ROOT / "templates/task-context.schema.json").read_text(encoding="utf-8"))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


class TaskCoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="contextd-coverage-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "knowledge"
        self.project = self.base / "application"
        self.nested = self.project / "src"
        self.nested.mkdir(parents=True)
        self.ws = self.root / "workspaces/default"
        write(self.ws / "workspace.md", "# Workspace\n\n## Packs\n\n(none)\n")
        write(self.root / "agents/constraints.md", "# Constraints\nPreserve workspace boundaries.\n")
        write(self.ws / "platform/contracts/citation-format.md",
              "# Citation format\n\n## Rule\nAdd a prefix to source locators.\n")
        write(self.ws / "platform/patterns/generic-logging.md",
              "# Generic logging\n\n## Rules\nAdd stable request identifiers to log entries.\n")
        write(self.ws / "projects/unrelated/knowledge-map.md",
              "# Knowledge map\n\n## Purpose\nA separate administrative portal.\n")
        self.configure([])

    def configure(self, packs):
        write(self.project / ".contextd/config.json", json.dumps({
            "workspace": "default", "knowledge_root": "../knowledge", "packs": packs,
        }))

    def build(self, task=TASK, packs=None):
        return engine.build_context_result(
            task, self.root, "default", [] if packs is None else packs,
            project_dir=self.project, synapse_as_of=AS_OF,
        )

    def route_pack(self):
        pack = self.root / "packs/pack-routing"
        write(pack / "pack.yaml", (
            "name: pack-routing\nversion: 1.0.0\n"
            "components: [transport]\nkeywords:\n  transport: [kafka]\n"
        ))
        write(pack / "agents/pipeline/retrieval-map.md", (
            "# Retrieval Map\n\n| Component | Docs to retrieve |\n|---|---|\n"
            "| `transport` | platform/patterns/generic-logging.md |\n"
        ))

    def test_no_match_rejects_filler_and_delivers_the_gap_to_the_agent(self):
        result = self.build()
        artifact = result.artifact
        self.assertEqual([], artifact["referenced_docs"])
        coverage = artifact["coverage"]
        self.assertEqual("no_match", coverage["status"])
        self.assertEqual(["idempotency", "kafka"], coverage["query_terms"])
        self.assertEqual([], coverage["matched_terms"])
        self.assertEqual(coverage["query_terms"], coverage["unmatched_terms"])
        self.assertEqual([], coverage["selected_paths"])
        self.assertEqual("not_requested", coverage["graph"]["status"])
        self.assertIs(False, coverage["complete"])
        self.assertTrue(any(g["category"] == "knowledge-coverage" and
                            NO_MATCH in g["missing"] for g in artifact["gaps"]))
        self.assertIn("agents/constraints.md", [d["path"] for d in artifact["static_context"]])
        self.assertTrue(result.selection_trace["considered_docs"])
        self.assertTrue(all(d["selection_reason"] == "no_task_relevance"
                            for d in result.selection_trace["considered_docs"]))
        diagnostics = context_coverage.render(coverage, artifact["gaps"])
        budget = artifact["budget_report"]
        self.assertEqual(engine._estimate_tokens(diagnostics), budget["estimated_tokens_diagnostics"])
        self.assertGreater(budget["estimated_tokens_diagnostics"], 0)
        self.assertEqual(budget["estimated_tokens_static"] + budget["estimated_tokens_diagnostics"],
                         budget["estimated_tokens_total"])
        materialized = engine.materialize_context(artifact, self.project, synapse_snapshot=result.synapse)
        for key in ("markdown", "pack"):
            content = (self.project / materialized["materialized"][key]).read_text(encoding="utf-8")
            self.assertIn(diagnostics, content)
            self.assertIn(NO_MATCH, content)
        Draft7Validator(SCHEMA).validate(materialized)

    def test_partial_literal_match_is_support_without_a_completeness_claim(self):
        path = "workspaces/default/platform/patterns/kafka-replay.md"
        write(self.root / path, "# Kafka replay\n\n## Flow\nConfirm the partition position before replay.\n")
        artifact = self.build().artifact
        self.assertEqual([path], [d["path"] for d in artifact["referenced_docs"]])
        coverage = artifact["coverage"]
        self.assertEqual("lexical_match", coverage["status"])
        self.assertEqual(["kafka"], coverage["matched_terms"])
        self.assertEqual(["idempotency"], coverage["unmatched_terms"])
        self.assertEqual([path], coverage["selected_paths"])
        self.assertIs(False, coverage["complete"])
        self.assertFalse(any(g["category"] == "knowledge-coverage" for g in artifact["gaps"]))
        Draft7Validator(SCHEMA).validate(artifact)

    def test_generic_software_role_is_not_a_task_specific_anchor(self):
        generic = "workspaces/default/platform/contracts/graph-authoring.md"
        write(self.root / generic, (
            "# Graph authoring\n\n## Boundary\n"
            "contextd is an OES consumer. The service validates graph structure for an agent.\n"
        ))
        relevant = "workspaces/default/platform/patterns/kafka-delivery.md"
        write(self.root / relevant, "# Kafka delivery\n\n## Flow\nInspect the partition position before replay.\n")
        result = self.build()
        self.assertEqual([relevant], [d["path"] for d in result.artifact["referenced_docs"]])
        dropped = next(d for d in result.selection_trace["dropped_docs"] if d["path"] == generic)
        self.assertEqual("no_task_relevance", dropped["selection_reason"])
        self.assertEqual([], dropped["relevance"]["matched_terms"])
        self.assertEqual("lexical_match", result.artifact["coverage"]["status"])
        self.assertEqual(["kafka"], result.artifact["coverage"]["matched_terms"])
        self.assertIs(False, result.artifact["coverage"]["complete"])
        (self.root / relevant).unlink()
        without_anchor = self.build().artifact
        self.assertEqual([], without_anchor["referenced_docs"])
        self.assertEqual("no_match", without_anchor["coverage"]["status"])
        self.assertTrue(any(NO_MATCH in gap["missing"] for gap in without_anchor["gaps"]))

    def test_action_only_query_is_unassessed(self):
        artifact = self.build("add").artifact
        self.assertEqual([], artifact["referenced_docs"])
        self.assertEqual("unassessed", artifact["coverage"]["status"])
        self.assertEqual([], artifact["coverage"]["query_terms"])
        self.assertIs(False, artifact["coverage"]["complete"])
        self.assertFalse(any(NO_MATCH in g["missing"] for g in artifact["gaps"]))

    def test_match_only_in_a_dropped_section_does_not_supply_context(self):
        write(self.ws / "platform/patterns/transport-notes.md", (
            "# Transport notes\n\n## Background\nKafka was discussed in a historical comparison.\n\n"
            "## Flow\nRoute diagnostics to the operations console.\n"
        ))
        artifact = self.build("add kafka").artifact
        self.assertEqual([], artifact["referenced_docs"])
        self.assertEqual("no_match", artifact["coverage"]["status"])

    def test_declared_pack_route_survives_without_literal_overlap(self):
        self.route_pack()
        result = self.build(packs=["pack-routing"])
        artifact = result.artifact
        path = "workspaces/default/platform/patterns/generic-logging.md"
        self.assertEqual([path], [d["path"] for d in artifact["referenced_docs"]])
        self.assertEqual("declared_route", artifact["coverage"]["status"])
        self.assertEqual([], artifact["coverage"]["matched_terms"])
        self.assertIn("pack_route", artifact["referenced_docs"][0]["relevance"]["basis"])
        self.assertFalse(any(g["category"] == "knowledge-coverage" for g in artifact["gaps"]))
        Draft7Validator(SCHEMA).validate(artifact)

    def test_static_duplicate_retains_the_selected_reference_route(self):
        self.route_pack()
        path = "packs/pack-routing/agents/common-pitfalls.md"
        write(self.root / path, "# General constraints\n\n## Rules\nKeep local policies explicit.\n")
        write(self.root / "packs/pack-routing/agents/pipeline/retrieval-map.md", (
            "# Retrieval Map\n\n| Component | Docs to retrieve |\n|---|---|\n"
            f"| `transport` | {path} |\n"
        ))
        artifact = self.build(packs=["pack-routing"]).artifact
        self.assertIn(path, [d["path"] for d in artifact["static_context"]])
        self.assertIn(path, [d["path"] for d in artifact["referenced_docs"]])
        self.assertEqual("declared_route", artifact["coverage"]["status"])
        self.assertEqual([path], artifact["coverage"]["selected_paths"])
        self.assertEqual([], artifact["coverage"]["matched_terms"])
        self.assertFalse(any(g["category"] == "knowledge-coverage" for g in artifact["gaps"]))
        self.assertEqual(1, engine._pack_markdown(artifact).count("Keep local policies explicit."))

    def test_static_projection_controls_literal_coverage_for_duplicate_source(self):
        pack = self.root / "packs/pack-routing"
        path = "packs/pack-routing/knowledge.md"
        write(pack / "pack.yaml", (
            "name: pack-routing\nversion: 1.0.0\nmanifest_version: 3\n"
            "components: [transport, unrelated]\nkeywords:\n  transport: [kafka]\n"
            f"retrieval:\n  transport: [{path}]\nfiles:\n  knowledge: knowledge.md\n"
        ))
        sections = ["# Local guidance", "## Global Principles", "Preserve local boundaries."]
        for component, text in (("transport", "Use the declared delivery rule."),
                                ("unrelated", "Kafka appears only in this unrequested component.")):
            sections.extend([
                f"## Component: {component}", "### Mental Model", text,
                "### Standards", "Keep local constraints.",
                "### Failure Signals", "Report missing facts.",
                "### Evidence And Stop Conditions", "Stop for missing authorization.",
            ])
        write(pack / "knowledge.md", "\n\n".join(sections) + "\n")
        artifact = self.build(packs=["pack-routing"]).artifact
        selected = next(d for d in artifact["referenced_docs"] if d["path"] == path)
        emitted = next(d for d in artifact["static_context"] if d["path"] == path)
        self.assertIn("kafka", selected["relevance"]["matched_terms"])
        self.assertNotIn("Kafka", emitted["content"])
        self.assertEqual("declared_route", artifact["coverage"]["status"])
        self.assertNotIn("kafka", artifact["coverage"]["matched_terms"])
        self.assertIn("kafka", artifact["coverage"]["unmatched_terms"])
        self.assertNotIn("unrequested component", engine._pack_markdown(artifact))

    def test_no_match_does_not_borrow_matching_knowledge_from_another_workspace(self):
        write(self.root / "workspaces/other/platform/patterns/kafka-idempotency.md", (
            "# Kafka idempotency\n\n## Rules\nConsumer guidance: FOREIGN_ONLY_MARKER.\n"
        ))
        artifact = self.build().artifact
        self.assertEqual("no_match", artifact["coverage"]["status"])
        self.assertEqual([], artifact["referenced_docs"])
        self.assertFalse(any(p.startswith("workspaces/other/") for p in artifact["source_hashes"]))
        self.assertNotIn("FOREIGN_ONLY_MARKER", engine._pack_markdown(artifact))

    def test_only_replacements_of_relevant_sources_inherit_eligibility(self):
        write(self.ws / "platform/patterns/kafka-legacy.md", (
            "---\ntype: Pattern\nnode_id: pattern.transport.old\nlifecycle: superseded\n---\n"
            "# Kafka legacy\n\n## Flow\nFollow the historical partition procedure.\n"
        ))
        replacement = "workspaces/default/platform/architecture/delivery-current.md"
        write(self.root / replacement, (
            "---\ntype: Architecture\nnode_id: architecture.delivery.current\nstatus: stable\n"
            "relations:\n  - type: supersedes\n    target: pattern.transport.old\n---\n"
            "# Current delivery policy\n\n## Flow\nPersist the durable marker before acknowledgement.\n"
        ))
        artifact = self.build().artifact
        doc = next(d for d in artifact["referenced_docs"] if d["path"] == replacement)
        self.assertIn("replacement", doc["relevance"]["basis"])
        self.assertIn(replacement, artifact["coverage"]["selected_paths"])
        unrelated = self.build("add geospatial indexing").artifact
        self.assertNotIn(replacement, [d["path"] for d in unrelated["referenced_docs"]])
        self.assertEqual("no_match", unrelated["coverage"]["status"])

    def test_coverage_and_gap_mutations_are_rejected_before_writes(self):
        result = self.build()
        for field in ("coverage", "gaps"):
            with self.subTest(field=field):
                artifact = copy.deepcopy(result.artifact)
                if field == "coverage":
                    artifact["coverage"]["status"] = "lexical_match"
                else:
                    artifact["gaps"] = []
                target = self.base / f"invalid-{field}"
                with self.assertRaisesRegex(ValueError, "projection changed"):
                    engine.materialize_context(artifact, target, synapse_snapshot=result.synapse)
                self.assertFalse(target.exists())

    def test_eval_count_and_gap_requirements_fail_independently(self):
        fixture = {"expected_referenced_doc_count": 0, "expected_gaps": [NO_MATCH]}
        artifact = self.build().artifact
        self.assertEqual("pass", cmd_eval._score_fixture(fixture, artifact)["status"])
        with_doc = copy.deepcopy(artifact)
        with_doc["referenced_docs"] = [{"path": "unrelated.md", "category": "pattern"}]
        scored = cmd_eval._score_fixture(fixture, with_doc)
        self.assertIn("referenced doc count 1 != expected 0", scored["errors"])
        without_gap = copy.deepcopy(artifact)
        without_gap["gaps"] = []
        self.assertIn(f"expected gap not found: {NO_MATCH}",
                      cmd_eval._score_fixture(fixture, without_gap)["errors"])
        for invalid in (-1, True, "0"):
            with self.subTest(invalid=invalid):
                scored = cmd_eval._score_fixture({"expected_referenced_doc_count": invalid}, artifact)
                self.assertEqual("fail", scored["status"])
                self.assertIn("expected_referenced_doc_count must be a non-negative integer", scored["errors"])

    def test_eval_explicit_empty_packs_override_inherited_packs(self):
        self.route_pack()
        self.configure(["pack-routing"])
        fixtures = self.ws / "eval/golden-tasks"
        base = {"task": TASK, "as_of": AS_OF.isoformat(), "workspace": "default"}
        write(fixtures / "empty.json", json.dumps({
            **base, "id": "empty-packs", "packs": [],
            "expected_referenced_doc_count": 0, "expected_gaps": [NO_MATCH],
        }))
        write(fixtures / "inherited.json", json.dumps({
            **base, "id": "inherited-packs", "expected_referenced_doc_count": 1,
            "expected_docs": ["workspaces/default/platform/patterns/generic-logging.md"],
        }))
        output = self.base / "eval.json"
        with redirect_stdout(io.StringIO()):
            code = cmd_eval.run(golden=True, cwd=str(self.nested), output=str(output))
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(0, code, report)
        results = {r["id"]: r for r in report["results"]}
        self.assertEqual("no_match", results["empty-packs"]["coverage"]["status"])
        self.assertTrue(results["empty-packs"]["gaps"])
        self.assertEqual("declared_route", results["inherited-packs"]["coverage"]["status"])
        rendered = cmd_eval._render_text(report)
        self.assertIn("Coverage: no_match", rendered)
        self.assertIn(NO_MATCH, rendered)

    def test_default_positive_and_negative_golden_tasks_pass_together(self):
        output = self.base / "default-golden.json"
        with redirect_stdout(io.StringIO()):
            code = cmd_eval.run(golden=True, workspace="default", cwd=str(ROOT), output=str(output))
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(0, code, report)
        results = {r["id"]: r for r in report["results"]}
        negative = results["kafka-idempotency-no-task-support"]
        self.assertEqual([], negative["selected_docs"])
        self.assertEqual("no_match", negative["coverage"]["status"])
        self.assertTrue(results["default-context-quality"]["selected_docs"])
        self.assertGreater(report["summary"]["passed"], 1)


class ExternalProjectCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get("OES_CLI")
        cls.oes_cli = (Path(configured) if configured else ROOT.parent / "oes/bin/oes.mjs").resolve()
        if not cls.oes_cli.is_file() or shutil.which("node") is None:
            message = "External-project integration requires Node.js and OES_CLI=/path/to/oes/bin/oes.mjs"
            if configured:
                raise RuntimeError(message)
            raise unittest.SkipTest(message)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="contextd-external-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        for directory in ("project", "knowledge"):
            shutil.copytree(ROOT / "examples/external-project" / directory, self.base / directory)
        self.project = self.base / "project"
        self.nested = self.project / "src"
        self.root = self.base / "knowledge"
        self.graph_path = Path("workspaces/payments/ontology/delivery-policy.graph.json")
        self.source_path = Path("workspaces/payments/decisions/delivery-policy.md")

    def run_cli(self, command, with_oes=False):
        args = [sys.executable, str(ROOT / "scripts/cli.py"), command, TASK, "--json"]
        if with_oes:
            args.extend(["--oes-graph", str(self.graph_path), "--oes-cli", str(self.oes_cli)])
        result = subprocess.run(
            args, cwd=self.nested, capture_output=True, text=True, encoding="utf-8", timeout=45,
        )
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        value = json.loads(result.stdout)
        return value["artifact"] if command == "explain" else value

    def test_same_external_task_gains_real_evidence_and_materializes_in_project(self):
        baseline = self.run_cli("explain")
        self.assertEqual([], baseline["referenced_docs"])
        self.assertEqual("no_match", baseline["coverage"]["status"])
        self.assertTrue(any(NO_MATCH in gap["missing"] for gap in baseline["gaps"]))
        artifact = self.run_cli("context", with_oes=True)
        self.assertEqual("payments", artifact["workspace"])
        self.assertEqual(self.project.resolve(), Path(artifact["project_dir"]).resolve())
        self.assertEqual(self.root.resolve(), Path(artifact["knowledge_root"]).resolve())
        self.assertEqual("evidence_match", artifact["coverage"]["status"])
        self.assertEqual("matched", artifact["coverage"]["graph"]["status"])
        self.assertIs(False, artifact["coverage"]["complete"])
        self.assertEqual({"structural": "passed", "evidence": "passed", "checked": 1, "skipped": 0},
                         artifact["oes"]["validation"])
        doc, = artifact["referenced_docs"]
        self.assertEqual(self.source_path.as_posix(), doc["path"])
        citation, = doc["oes_evidence"]
        self.assertEqual("worker-implements-idempotency", citation["edge_id"])
        self.assertEqual("L18-L20", citation["locator"])
        raw_source = (self.root / self.source_path).read_bytes()
        self.assertEqual(hashlib.sha256(raw_source).hexdigest(), citation["source_hash"])
        self.assertEqual("\n".join(raw_source.decode("utf-8").splitlines()[17:20]), citation["excerpt"])
        self.assertNotIn("workspaces/default/", json.dumps(artifact))
        self.assertFalse((self.nested / ".contextd").exists())
        self.assertFalse((self.root / ".contextd").exists())
        for key in ("json", "markdown", "pack"):
            path = self.project / artifact["materialized"][key]
            self.assertTrue(path.is_file(), path)
        stored = json.loads((self.project / artifact["materialized"]["json"]).read_text(encoding="utf-8"))
        self.assertEqual(artifact["coverage"], stored["coverage"])
        for key in ("markdown", "pack"):
            content = (self.project / artifact["materialized"][key]).read_text(encoding="utf-8")
            self.assertIn("evidence_match", content)
            self.assertIn(citation["edge_id"], content)
            self.assertIn(citation["locator"], content)
            self.assertIn(citation["excerpt"].splitlines()[0], content)
        Draft7Validator(SCHEMA).validate(artifact)

    def test_valid_but_unmatched_graph_reports_only_its_bounded_route_gap(self):
        path = self.root / self.graph_path
        graph = json.loads(path.read_text(encoding="utf-8"))
        graph["nodes"][0]["properties"]["label"] = "Payment processor"
        graph["nodes"][1]["id"] = "delivery-durability"
        graph["nodes"][1]["properties"]["statement"] = "Commit every write before acknowledgement."
        graph["edges"][0]["to"] = "delivery-durability"
        write(path, json.dumps(graph, indent=2) + "\n")
        artifact = self.run_cli("explain", with_oes=True)
        self.assertEqual("passed", artifact["oes"]["validation"]["evidence"])
        self.assertEqual([], artifact["referenced_docs"])
        self.assertEqual("no_match", artifact["coverage"]["status"])
        self.assertEqual("no_match", artifact["coverage"]["graph"]["status"])
        self.assertEqual([], artifact["coverage"]["graph"]["matched_edge_ids"])
        self.assertIs(False, artifact["coverage"]["complete"])
        gap = next(g for g in artifact["gaps"] if g["category"] == "oes-coverage")
        self.assertIn("graph", gap["missing"].lower())
        self.assertIn("not proof", gap["missing"])
        Draft7Validator(SCHEMA).validate(artifact)

    def test_matched_graph_omitted_by_budget_is_not_reported_as_absent(self):
        with mock.patch.dict(engine.WORKSTREAM_BUDGETS["engineering"], {"decision": 0}):
            result = engine.build_context_result(
                TASK, self.root, "payments", [], project_dir=self.project, synapse_as_of=AS_OF,
                oes_request=oes_context.OESRequest(graph=self.graph_path, cli=self.oes_cli),
            )
        artifact = result.artifact
        self.assertEqual([], artifact["referenced_docs"])
        self.assertEqual("not_selected", artifact["coverage"]["graph"]["status"])
        self.assertEqual(["worker-implements-idempotency"], artifact["coverage"]["graph"]["matched_edge_ids"])
        knowledge_gap = next(g for g in artifact["gaps"] if g["category"] == "knowledge-coverage")
        self.assertIn("candidates were found", knowledge_gap["missing"])
        self.assertNotIn(NO_MATCH, knowledge_gap["missing"])
        self.assertTrue(any(g["category"] == "oes-coverage" for g in artifact["gaps"]))
        Draft7Validator(SCHEMA).validate(artifact)


if __name__ == "__main__":
    unittest.main(verbosity=2)
