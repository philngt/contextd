#!/usr/bin/env python3
"""OES → contextd integration tests using an actual OES checkout.

Run with OES_CLI=/path/to/oes/bin/oes.mjs python3 scripts/test_oes_context.py.
Without OES_CLI, a sibling ../oes checkout is used when available.
"""
from __future__ import annotations

import copy
from datetime import date
import hashlib
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

from lib import context_output, oes_context, task_context_engine as engine


ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = Path("workspaces/default/ontology/consumer-recovery.graph.json")
SOURCE_PATH = Path("workspaces/default/decisions/consumer-write-recovery.md")
TASK = "Investigate ingest-worker lost writes"
SOURCE_ID = "recovery-decision-source"
EVIDENCE_ID = "persist-before-ack-evidence"
EDGE_ID = "worker-implements-recovery"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


class OESContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get("OES_CLI")
        cls.cli = Path(configured) if configured else ROOT.parent / "oes/bin/oes.mjs"
        cls.cli = cls.cli.resolve()
        if not cls.cli.is_file() or shutil.which("node") is None:
            message = "OES integration requires Node.js 20+ and OES_CLI=/path/to/oes/bin/oes.mjs"
            if configured:
                raise RuntimeError(message)
            raise unittest.SkipTest(message)
        cls.schema = json.loads((ROOT / "templates/task-context.schema.json").read_text())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ws = self.root / "workspaces/default"
        write(self.ws / "workspace.md", "# Example workspace\n\n## Packs\n\n(none)\n")
        write(self.root / ".contextd/config.json", json.dumps({
            "workspace": "default", "knowledge_root": ".", "packs": [],
        }))
        write(self.root / "agents/constraints.md", "# Engine constraints\nPreserve source provenance.\n")
        write(self.ws / "platform/contracts/baseline.md", "# Baseline\n\n## Rule\nKeep workspace boundaries.\n")
        write(self.root / SOURCE_PATH, (ROOT / SOURCE_PATH).read_text(encoding="utf-8"))
        self.graph = json.loads((ROOT / GRAPH_PATH).read_text(encoding="utf-8"))
        self.save_graph()

    def save_graph(self):
        write(self.root / GRAPH_PATH, json.dumps(self.graph, indent=2) + "\n")

    def node(self, node_id):
        return next(n for n in self.graph["nodes"] if n["id"] == node_id)

    def build(self, *, with_oes=True, request=None):
        return engine.build_context_result(
            TASK, self.root, "default", [], project_dir=self.root,
            synapse_as_of=date(2026, 11, 4),
            oes_request=(request or oes_context.OESRequest(
                graph=GRAPH_PATH, cli=self.cli,
            )) if with_oes else None,
        )

    def selected_source(self, artifact, path=SOURCE_PATH.as_posix()):
        return next(doc for doc in artifact["referenced_docs"] if doc["path"] == path)

    def run_cli(self, command="context", *extra):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/cli.py"), command, TASK,
             "--oes-graph", str(GRAPH_PATH), "--oes-cli", str(self.cli), *extra],
            cwd=self.root, capture_output=True, text=True, encoding="utf-8", check=False,
        )

    def replace_source(self, text, uri="decisions/consumer-write-recovery.md", locator="L1"):
        target = self.ws / uri
        write(target, text)
        self.node(SOURCE_ID)["properties"].update({
            "uri": uri, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        })
        self.node(EVIDENCE_ID)["properties"].update({
            "locator": locator, "excerpt": text.rstrip("\n"),
        })
        self.save_graph()

    def test_real_validator_adds_a_document_with_traceable_evidence(self):
        baseline = self.build(with_oes=False).artifact
        self.assertNotIn(SOURCE_PATH.as_posix(), [d["path"] for d in baseline["referenced_docs"]])
        result = self.build()
        artifact = result.artifact
        doc = self.selected_source(artifact)
        citation, = doc["oes_evidence"]
        self.assertEqual(EDGE_ID, citation["edge_id"])
        self.assertEqual("implementsRule", citation["relation"])
        self.assertEqual("ingest-worker", citation["from_node"]["id"])
        self.assertEqual("accepted", citation["to_node"]["status"])
        self.assertEqual("asserted", citation["assertion_status"])
        self.assertEqual(EVIDENCE_ID, citation["evidence_id"])
        self.assertEqual(SOURCE_ID, citation["source_id"])
        self.assertEqual("L22-L23", citation["locator"])
        self.assertEqual("matched", citation["evidence_check"])
        self.assertEqual(hashlib.sha256((self.root / SOURCE_PATH).read_bytes()).hexdigest(), citation["source_hash"])
        self.assertEqual(hashlib.sha256((self.root / GRAPH_PATH).read_bytes()).hexdigest(), citation["graph_hash"])
        self.assertEqual({"structural": "passed", "evidence": "passed", "checked": 1, "skipped": 0}, artifact["oes"]["validation"])
        self.assertEqual([EDGE_ID], artifact["oes"]["matched_edge_ids"])
        trace = next(d for d in result.selection_trace["selected_docs"] if d["path"] == doc["path"])
        self.assertEqual(12, trace["oes_score_adjustment"])
        self.assertEqual(doc["oes_evidence"], trace["oes_evidence"])
        Draft7Validator(self.schema).validate(artifact)

    def test_cli_materializes_citations_in_json_task_markdown_and_agent_pack(self):
        result = self.run_cli("context", "--json")
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        artifact = json.loads(result.stdout)
        self.assertEqual("materialized", artifact["contextPack"]["status"])
        stored = json.loads((self.root / artifact["materialized"]["json"]).read_text())
        self.assertEqual(artifact["oes"], stored["oes"])
        doc = self.selected_source(artifact)
        for key in ("markdown", "pack"):
            text = (self.root / artifact["materialized"][key]).read_text()
            for expected in (EDGE_ID, EVIDENCE_ID, "L22-L23", "asserted"):
                self.assertIn(expected, text)
            self.assertIn(doc["oes_evidence"][0]["excerpt"].splitlines()[0], text)
        explained = self.run_cli("explain", "--text")
        self.assertEqual(0, explained.returncode, explained.stderr or explained.stdout)
        self.assertIn(EDGE_ID, explained.stdout)
        self.assertIn(SOURCE_PATH.as_posix(), explained.stdout)

    def test_repeated_builds_are_deterministic_and_graph_changes_rotate_identity(self):
        first, second = self.build(), self.build()
        self.assertEqual(first.artifact["contextPack"]["packKey"], second.artifact["contextPack"]["packKey"])
        self.assertEqual(first.selection_trace, second.selection_trace)
        self.graph["edges"][0].update({"assertionStatus": "hypothesis", "confidence": 0.45,
                                      "validFrom": "2026-01-01", "validTo": "2026-12-31",
                                      "properties": {"scope": "consumer-persistence"}})
        self.node("persist-before-ack")["properties"]["status"] = "rejected"
        self.save_graph()
        updated = self.build().artifact
        self.assertNotEqual(first.artifact["contextPack"]["packKey"], updated["contextPack"]["packKey"])
        citation, = self.selected_source(updated)["oes_evidence"]
        self.assertEqual("hypothesis", citation["assertion_status"])
        self.assertEqual("rejected", citation["to_node"]["status"])
        self.assertEqual(0.45, citation["confidence"])
        self.assertEqual("2026-01-01", citation["valid_from"])
        self.assertEqual({"scope": "consumer-persistence"}, citation["relation_properties"])
        self.assertIn("hypothesis", context_output._pack_markdown(updated))
        Draft7Validator(self.schema).validate(updated)

    def test_materialization_refuses_modified_citation_metadata(self):
        result = self.build()
        changed = copy.deepcopy(result.artifact)
        self.selected_source(changed)["oes_evidence"][0]["assertion_status"] = "verified"
        with self.assertRaisesRegex(ValueError, "changed|identity|projection"):
            engine.materialize_context(changed, self.root, synapse_snapshot=result.synapse)
        self.assertFalse((self.root / ".contextd/context").exists())

    def test_invalid_graph_and_tampered_excerpt_fail_before_output(self):
        original = copy.deepcopy(self.graph)
        for corruption in ("unknown_endpoint", "wrong_excerpt", "partial_excerpt",
                           "array_template", "numeric_ontology_version"):
            with self.subTest(corruption=corruption):
                self.graph = copy.deepcopy(original)
                if corruption == "unknown_endpoint":
                    self.graph["edges"][0]["to"] = "missing-rule"
                elif corruption == "wrong_excerpt":
                    self.node(EVIDENCE_ID)["properties"]["excerpt"] = "Invented source statement."
                elif corruption == "partial_excerpt":
                    excerpt = self.node(EVIDENCE_ID)["properties"]["excerpt"]
                    self.node(EVIDENCE_ID)["properties"]["excerpt"] = excerpt.splitlines()[0]
                elif corruption == "array_template":
                    self.graph["template"] = ["software-system"]
                else:
                    self.graph["metadata"]["ontologyVersion"] = 42
                self.save_graph()
                result = self.run_cli("context", "--json")
                self.assertNotEqual(0, result.returncode)
                self.assertIn("OES", result.stderr)
                self.assertFalse((self.root / ".contextd/context").exists())

    def test_expected_source_hash_detects_drift_outside_cited_lines(self):
        source = self.root / SOURCE_PATH
        source.write_text(source.read_text() + "\nAdditional uncited text.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "source-hash-mismatch"):
            self.build()

    def test_paths_cannot_bypass_workspace_or_governed_source_boundary(self):
        original_uri = self.node(SOURCE_ID)["properties"]["uri"]
        for uri in ("../other/secret.md", "/tmp/secret.md", "file:///tmp/secret.md",
                    "https://example.invalid/source.md", "decisions/%2e%2e/secret.md",
                    "workspaces/other/secret.md", "evidence/sources/private/raw.md"):
            with self.subTest(uri=uri):
                self.node(SOURCE_ID)["properties"]["uri"] = uri
                self.save_graph()
                with self.assertRaises(ValueError):
                    self.build()
        self.node(SOURCE_ID)["properties"]["uri"] = original_uri
        self.graph["metadata"]["workspace"] = "other"
        self.save_graph()
        with self.assertRaisesRegex(ValueError, "workspace"):
            self.build()

    def test_graph_and_source_symlinks_cannot_escape_workspace(self):
        outside = self.root / "outside"
        write(outside / "source.md", "FOREIGN_WORKSPACE_SENTINEL\n")
        source_link = self.ws / "decisions/foreign.md"
        try:
            source_link.symlink_to(outside / "source.md")
        except OSError:
            self.skipTest("Symlink creation is unavailable on this platform")
        self.node(SOURCE_ID)["properties"]["uri"] = "decisions/foreign.md"
        self.save_graph()
        with self.assertRaisesRegex(ValueError, "outside|workspace"):
            self.build()
        foreign_graph = outside / "graph.json"
        foreign_graph.write_bytes((self.root / GRAPH_PATH).read_bytes())
        graph_link = self.ws / "ontology/foreign.graph.json"
        graph_link.symlink_to(foreign_graph)
        with self.assertRaisesRegex(ValueError, "workspace"):
            self.build(request=oes_context.OESRequest(graph=graph_link, cli=self.cli))

    def test_validator_consumes_retained_source_bytes_after_live_file_changes(self):
        original = (self.root / SOURCE_PATH).read_bytes()
        loader = oes_context.load_selection

        def change_live_source_then_validate(*args, **kwargs):
            (self.root / SOURCE_PATH).write_text("Changed after the governed source scan.\n")
            return loader(*args, **kwargs)

        with mock.patch.object(oes_context, "load_selection", side_effect=change_live_source_then_validate):
            result = self.build()
        doc = self.selected_source(result.artifact)
        self.assertEqual(hashlib.sha256(original).hexdigest(), doc["source_hash"])
        self.assertEqual(doc["source_hash"], doc["oes_evidence"][0]["source_hash"])
        self.assertIn("persist each accepted record", doc["content"])
        materialized = engine.materialize_context(result.artifact, self.root, synapse_snapshot=result.synapse)
        self.assertEqual("materialized", materialized["synapse"]["status"])

    def test_citations_redact_sensitive_values_after_integrity_check(self):
        self.replace_source("The worker configuration contains api_key=DEMO_SECRET_98765.\n")
        result = self.build()
        artifact = result.artifact
        citation, = self.selected_source(artifact)["oes_evidence"]
        self.assertTrue(citation["redacted"])
        self.assertIn("<REDACTED-SECRET>", citation["excerpt"])
        self.assertNotIn("DEMO_SECRET_98765", json.dumps(artifact))
        self.assertNotIn("DEMO_SECRET_98765", context_output._pack_markdown(artifact))
        Draft7Validator(self.schema).validate(artifact)

    def test_supported_by_target_is_evidence_without_redundant_evidence_ids(self):
        self.node("persist-before-ack")["properties"]["label"] = "ingest-worker recovery"
        self.graph["edges"] = [{
            "id": "recovery-supported-by", "type": "supportedBy",
            "from": "persist-before-ack", "to": EVIDENCE_ID, "assertionStatus": "asserted",
        }]
        self.save_graph()
        citation, = self.selected_source(self.build().artifact)["oes_evidence"]
        self.assertEqual(EVIDENCE_ID, citation["evidence_id"])
        self.assertEqual("supportedBy", citation["relation"])

    def test_selection_does_not_expand_beyond_matched_nodes_one_hop(self):
        uri = "decisions/archive-retention.md"
        text = "Archived audit logs are retained for review.\n"
        write(self.ws / uri, text)
        self.graph["nodes"].extend([
            {"id": "archive-source", "type": "Source", "properties": {"uri": uri, "sha256": hashlib.sha256(text.encode()).hexdigest()}},
            {"id": "archive-evidence", "type": "Evidence", "properties": {"sourceId": "archive-source", "locator": "L1", "excerpt": text.rstrip("\n")}},
            {"id": "archive-policy", "type": "BusinessRule", "properties": {"statement": "Retain archived audit logs.", "status": "proposed"}},
        ])
        self.graph["edges"].append({
            "id": "second-hop", "type": "derivedFrom", "from": "persist-before-ack",
            "to": "archive-policy", "evidenceIds": ["archive-evidence"], "assertionStatus": "hypothesis",
        })
        self.save_graph()
        artifact = self.build().artifact
        self.assertEqual([EDGE_ID], artifact["oes"]["matched_edge_ids"])
        self.assertNotIn(f"workspaces/default/{uri}", [d["path"] for d in artifact["referenced_docs"]])
        unrelated = engine.build_context_result(
            "Investigate billing settlement", self.root, "default", [],
            oes_request=oes_context.OESRequest(graph=GRAPH_PATH, cli=self.cli),
        ).artifact
        self.assertEqual([], unrelated["oes"]["matched_edge_ids"])
        self.assertFalse(any(d.get("oes_evidence") for d in unrelated["referenced_docs"]))

    def test_many_graph_routes_still_obey_category_budgets(self):
        for i in range(5):
            uri = f"decisions/recovery-{i}.md"
            text = f"# Recovery {i}\n\nThe worker retains failed operation {i}.\n"
            write(self.ws / uri, text)
            source_id, evidence_id = f"source-{i}", f"evidence-{i}"
            self.graph["nodes"].extend([
                {"id": source_id, "type": "Source", "properties": {"uri": uri, "sha256": hashlib.sha256(text.encode()).hexdigest()}},
                {"id": evidence_id, "type": "Evidence", "properties": {"sourceId": source_id, "locator": "L3", "excerpt": text.splitlines()[2]}},
                {"id": f"rule-{i}", "type": "BusinessRule", "properties": {"statement": f"Retain operation {i}.", "status": "proposed"}},
            ])
            self.graph["edges"].append({"id": f"route-{i}", "type": "implementsRule", "from": "ingest-worker", "to": f"rule-{i}", "evidenceIds": [evidence_id], "assertionStatus": "hypothesis"})
        self.save_graph()
        result = self.build()
        docs = result.artifact["referenced_docs"]
        budget = result.artifact["budget_report"]
        self.assertLessEqual(len(docs), budget["max_docs"])
        self.assertEqual(2, sum(d["category"] == "decision" for d in docs))
        self.assertTrue(any(d["selection_reason"] == "category_budget_exhausted" and d.get("oes_evidence") for d in result.selection_trace["dropped_docs"]))
        expected_tokens = sum(max(1, (len(d["content"]) + 3) // 4) if d["content"] else 0 for d in docs)
        self.assertEqual(expected_tokens, budget["estimated_tokens_referenced"])
        for d in result.selection_trace["selected_docs"]:
            if d.get("oes_evidence"):
                self.assertEqual(12, d["oes_score_adjustment"])

    def test_static_source_overlap_keeps_evidence_once_in_compiled_pack(self):
        uri = "agents/constraints.md"
        self.replace_source("The worker must preserve explicit approval boundaries.\n", uri)
        result = self.build()
        artifact = result.artifact
        path = f"workspaces/default/{uri}"
        static = next(d for d in artifact["static_context"] if d["path"] == path)
        self.assertTrue(static["oes_evidence"])
        self.assertTrue(self.selected_source(artifact, path)["oes_evidence"])
        pack = context_output._pack_markdown(artifact)
        self.assertEqual(1, pack.count(f"## Source: {path}"))
        self.assertEqual(1, pack.count(f'"evidence_id": "{EVIDENCE_ID}"'))
        self.assertEqual(1, artifact["budget_report"]["deduplicated_overlap_docs"])
        for target in ("referenced", "graph"):
            with self.subTest(target=target):
                changed = json.loads(json.dumps(artifact))
                if target == "referenced":
                    self.selected_source(changed, path)["oes_evidence"][0]["assertion_status"] = "verified"
                else:
                    changed["oes"]["graph_hash"] = "0" * 64
                with self.assertRaises(ValueError):
                    engine.materialize_context(changed, self.root, synapse_snapshot=result.synapse)
                self.assertFalse((self.root / ".contextd/context").exists())

    def test_validator_protocol_failures_and_timeouts_are_not_success(self):
        # Fault injection covers the subprocess boundary; successful tests above
        # execute the real CLI and never substitute a fake successful validator.
        valid = {"command": "check-graph", "passed": True, "diagnostics": [],
                 "evidence": {"checked": 1, "skipped": 0}}
        failures = ["OK", "[]", json.dumps({**valid, "passed": False}),
                    json.dumps({**valid, "evidence": {"checked": 0, "skipped": 1}}),
                    json.dumps({**valid, "command": "check-evidence"})]
        for output in failures:
            with self.subTest(output=output), mock.patch.object(
                oes_context.subprocess, "run",
                return_value=subprocess.CompletedProcess([], 0, stdout=output, stderr=""),
            ):
                with self.assertRaises(ValueError):
                    self.build()
        with mock.patch.object(oes_context.subprocess, "run", side_effect=subprocess.TimeoutExpired("oes", 0.01)):
            with self.assertRaisesRegex(ValueError, "timed out"):
                self.build()

    def test_ordinary_build_has_no_validator_dependency(self):
        with mock.patch.object(oes_context, "load_selection", side_effect=AssertionError("OES should remain opt-in")):
            artifact = self.build(with_oes=False).artifact
        self.assertNotIn("oes", artifact)
        self.assertFalse(any(d.get("oes_evidence") for d in artifact["referenced_docs"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
