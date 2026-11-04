"""Native OES authoring, exact snapshots, workflow isolation and portable exports.

Use OES_CLI=/path/to/oes/bin/oes.mjs (or a sibling ../oes checkout).
Successful cases invoke the real OES CLI; mocks only inject boundary failures.
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

from jsonschema import Draft202012Validator, Draft7Validator

from export_graph_authoring import export as export_skills, SKILLS
from lib import graph_authoring_oes as native, oes_context, oes_validation, task_context_engine as engine


ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "examples/graph-authoring/oes-native"
RES = ROOT / "templates/graph-authoring"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


class NativeAuthoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get("OES_CLI") or os.environ.get("CONTEXTD_OES_CLI")
        cls.cli = Path(configured).resolve() if configured else ROOT.parent / "oes/bin/oes.mjs"
        if not cls.cli.is_file() or shutil.which("node") is None:
            message = "Native authoring tests require Node.js 20+ and OES_CLI=/path/to/oes/bin/oes.mjs"
            if configured:
                raise RuntimeError(message)
            raise unittest.SkipTest(message)
        cls.schemas = {key: read(RES / f"graph-{key}.v2.schema.json")
                       for key in ("proposal", "baseline")}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.sources = self.root / "sources"
        shutil.copytree(FIX / "sources", self.sources)
        self.p = read(FIX / "proposal.json")
        self.b = read(FIX / "baseline.json")
        self.request = oes_validation.OESRequest(cli=self.cli)

    def check(self):
        return native.validate(self.p, self.b, workspace="default", project_id="refund-demo",
                               schemas=self.schemas, request=self.request, source_root=self.sources)

    def error(self, code):
        result = self.check()
        self.assertFalse(result.report["valid"], result.report)
        self.assertIn(code, [item["code"] for item in result.report["errors"]])
        self.assertIsNone(result.graph_bytes)
        return result.report

    def candidate_node(self, identifier):
        return next(node for node in self.p["graph"]["nodes"] if node["id"] == identifier)

    def both_source_nodes(self):
        return [next(node for node in value["graph"]["nodes"] if node["type"] == "Source")
                for value in (self.p, self.b)]

    def test_real_oes_native_graph_keeps_review_and_assertion_states(self):
        before = copy.deepcopy((self.p, self.b))
        result = self.check()
        self.assertTrue(result.report["valid"], result.report)
        self.assertEqual(result.report["validation"], {
            "schema": "passed", "structural": "passed", "evidence": "passed", "checked": 2, "skipped": 0,
        })
        self.assertEqual((self.p, self.b), before)
        graph = json.loads(result.graph_bytes)
        self.assertEqual(graph["metadata"]["contextdProposal"]["status"], "pending")
        self.assertEqual(graph["edges"][-1]["assertionStatus"], "hypothesis")
        rule = next(node for node in graph["nodes"] if node["id"] == "rule:refund-receipt")
        self.assertEqual({k: rule["properties"][k] for k in ("status", "model", "verification", "review")},
                         {"status": "proposed", "model": "to-be", "verification": "observed", "review": "draft"})
        self.assertTrue(result.report["sources_verified"])
        for key in ("apply_supported", "execution_authorized", "live_baseline_verified"):
            self.assertFalse(result.report[key])
        self.assertEqual(result.report["graph_hash"], hashlib.sha256(result.graph_bytes).hexdigest())

    def test_schemas_are_valid_and_oes_owns_graph_envelope(self):
        for schema in self.schemas.values():
            Draft202012Validator.check_schema(schema)
        # OES's engine permits a default status, but its published envelope
        # explicitly requires assertionStatus. The real OES schema must run too.
        del self.p["graph"]["edges"][-1]["assertionStatus"]
        self.error("invalid-oes-shape:required")

    def test_oes_owns_node_vocabulary_and_relation_endpoints(self):
        self.candidate_node("rule:refund-receipt")["type"] = "LegacyFeature"
        report = self.error("oes-validation-failed")
        self.assertIn("unknown-node-type", report["errors"][0]["detail"])
        self.p = read(FIX / "proposal.json")
        self.p["graph"]["edges"][-1]["to"] = "source:refund-policy"
        report = self.error("oes-validation-failed")
        self.assertIn("invalid-target-type", report["errors"][0]["detail"])

    def test_revision_workspace_and_project_binding(self):
        for change, code in (
            (lambda: self.p.update(base_revision="old"), "stale-base-revision"),
            (lambda: self.p.update(workspace="foreign"), "workspace-mismatch"),
            (lambda: self.b["graph"]["metadata"].update(projectId="foreign"), "project-mismatch"),
        ):
            with self.subTest(code=code):
                self.p, self.b = read(FIX / "proposal.json"), read(FIX / "baseline.json")
                change()
                self.error(code)

    def test_existing_records_cannot_be_changed_deleted_or_retyped(self):
        for operation in ("change", "delete", "retype"):
            with self.subTest(operation=operation):
                self.p = read(FIX / "proposal.json")
                node = self.candidate_node("service:refund-worker")
                if operation == "change":
                    node["properties"]["label"] = "Changed owner name"
                elif operation == "delete":
                    self.p["graph"]["nodes"].remove(node)
                else:
                    node["type"] = "Module"
                self.error("existing-record-changed")

    def test_reserved_ids_and_duplicate_baseline_ids(self):
        self.b["reserved_ids"].append("rule:refund-receipt")
        self.error("identity-collision")
        self.b = read(FIX / "baseline.json")
        self.b["graph"]["nodes"].append(copy.deepcopy(self.b["graph"]["nodes"][0]))
        self.error("duplicate-baseline-id")

    def test_additive_comparison_preserves_json_types_in_records_and_headers(self):
        baseline_node = next(node for node in self.b["graph"]["nodes"] if node["type"] == "Service")
        baseline_node["properties"]["custom_flag"] = True
        self.candidate_node("service:refund-worker")["properties"]["custom_flag"] = 1
        self.error("existing-record-changed")
        self.p, self.b = read(FIX / "proposal.json"), read(FIX / "baseline.json")
        self.p["graph"]["metadata"]["synthetic"] = 1
        self.error("graph-header-changed")

    def test_native_pending_lifecycle_never_auto_approves_claims(self):
        self.p["status"] = "approved"
        self.error("invalid-shape:const")
        self.p = read(FIX / "proposal.json")
        self.candidate_node("rule:refund-receipt")["properties"]["status"] = "accepted"
        self.error("new-claim-not-proposed")
        self.p = read(FIX / "proposal.json")
        self.candidate_node("rule:refund-receipt")["properties"]["review"] = "approved"
        self.error("new-claim-not-draft")
        self.p = read(FIX / "proposal.json")
        self.p["graph"]["metadata"]["contextdProposal"]["id"] = "proposal:another"
        self.error("proposal-marker-mismatch")

    def test_identity_review_and_issues_remain_workflow_records(self):
        self.p["identity_matches"] = [{
            "candidate_id": "candidate:worker", "target_id": "service:refund-worker",
            "basis": "suggested", "evidence_refs": ["evidence:refund-inventory"],
            "rationale": "Similarity needs owner review.",
        }]
        self.p["issues"] = [{
            "id": "issue:implementation", "kind": "implementation-gap",
            "subjects": ["rule:refund-receipt", "edge:worker-receipt-rule"],
            "detail": "Implementation has not been observed.", "evidence_refs": ["evidence:receipt-policy"],
        }]
        report = self.check().report
        self.assertTrue(report["valid"], report)
        self.assertEqual({item["code"] for item in report["warnings"]},
                         {"identity-review-required", "review-issue:implementation-gap"})
        self.p["identity_matches"][0]["target_id"] = "unknown:owner"
        self.error("missing-reuse-target")
        self.p["identity_matches"][0]["target_id"] = "service:refund-worker"
        self.p["issues"][0]["subjects"] = ["unknown:subject"]
        self.error("missing-issue-subject")

    def test_a_paraphrase_is_not_an_excerpt(self):
        self.candidate_node("evidence:receipt-policy")["properties"]["excerpt"] = "Refunds need receipts."
        report = self.error("oes-validation-failed")
        self.assertIn("excerpt-mismatch", report["errors"][0]["detail"])
        self.assertFalse(report["sources_verified"])

    def test_source_hash_is_required_and_detects_uncited_drift(self):
        for node in self.both_source_nodes():
            del node["properties"]["sha256"]
        report = self.error("oes-validation-failed")
        self.assertIn("sha256", report["errors"][0]["detail"])
        self.p, self.b = read(FIX / "proposal.json"), read(FIX / "baseline.json")
        with (self.sources / "rules/refund-receipts.md").open("ab") as stream:
            stream.write(b"Uncited but changed bytes.\n")
        report = self.error("oes-validation-failed")
        self.assertIn("sha256", report["errors"][0]["detail"])

    def test_sources_cannot_escape_or_fetch_remote_content(self):
        for uri in ("../outside.md", "https://never-fetch.invalid/source", "/etc/passwd", "rules/../other.md"):
            with self.subTest(uri=uri):
                for node in self.both_source_nodes():
                    node["properties"]["uri"] = uri
                report = self.error("oes-validation-failed")
                self.assertIn("literal path", report["errors"][0]["detail"])

    def test_source_symlink_rejected_but_explicit_root_alias_is_portable(self):
        alias = self.root / "source-alias"
        try:
            alias.symlink_to(self.sources, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        self.sources = alias
        result = self.check()
        self.assertTrue(result.report["valid"])
        native.export(result, graph_path=alias / "pending.graph.json")
        self.assertEqual((self.root / "sources/pending.graph.json").read_bytes(), result.graph_bytes)
        target = self.root / "sources/rules/refund-receipts.md"
        saved = self.root / "outside.md"
        target.rename(saved)
        target.symlink_to(saved)
        self.error("oes-validation-failed")

    def test_oes_reads_retained_bytes_after_live_source_changes(self):
        original_run = oes_validation._run
        calls = []

        def mutate_after_capture(request, args):
            calls.append(args)
            if args[0] == "check-graph":
                (self.sources / "rules/refund-receipts.md").write_text("Changed after capture.\n")
            return original_run(request, args)

        with mock.patch.object(oes_validation, "_run", side_effect=mutate_after_capture):
            result = self.check()
        self.assertTrue(result.report["valid"], result.report)
        self.assertIn("--require-hash", next(args for args in calls if args[0] == "check-graph"))

    def test_review_hash_binds_scope_ontology_and_exact_export_bytes(self):
        first = self.check()
        self.assertEqual(first.report, self.check().report)
        self.p["scope"]["not_reviewed"].append("An additional explicit limitation.")
        second = self.check()
        self.assertNotEqual(first.report["review_input_hash"], second.report["review_input_hash"])
        self.assertEqual(first.report["graph_hash"], second.report["graph_hash"])
        template = oes_validation.compile_template(self.request, "software-system")
        template["metadata"]["description"] += " A revised ontology description."
        with mock.patch.object(native, "compile_template", return_value=template):
            third = self.check()
        self.assertTrue(third.report["valid"])
        self.assertNotEqual(second.report["review_input_hash"], third.report["review_input_hash"])

    def test_ontology_version_mismatch_is_visible(self):
        for value in (self.p, self.b):
            value["graph"]["metadata"]["ontologyVersion"] = "future-version"
        self.error("ontology-version-mismatch")

    def test_concurrent_ontology_change_with_same_version_refuses_handoff(self):
        after = oes_validation.compile_template(self.request, "software-system")
        before = copy.deepcopy(after)
        before["entityTypes"]["BusinessRule"]["parent"] = "Entity"
        self.assertEqual(before["metadata"]["version"], after["metadata"]["version"])
        # A formerly ordinary entity becomes a Claim while retaining its type
        # name/version. The real OES checker accepts this Claim status, but the
        # pending-review guard ran against the earlier inheritance snapshot.
        self.candidate_node("rule:refund-receipt")["properties"]["status"] = "accepted"
        with mock.patch.object(native, "compile_template", side_effect=[before, after]):
            report = self.error("ontology-changed-during-validation")
        self.assertEqual(report["validation"]["evidence"], "passed")
        self.assertEqual(report["validation"]["structural"], "not-passed")

    def test_empty_owner_baseline_still_requires_evidence_in_candidate(self):
        self.b["graph"]["nodes"], self.b["graph"]["edges"] = [], []
        self.assertTrue(self.check().report["valid"])
        self.p["graph"]["nodes"], self.p["graph"]["edges"] = [], []
        self.error("oes-validation-failed")

    def test_shared_transport_empty_baseline_mode_is_explicit_and_bounded(self):
        graph = copy.deepcopy(self.b["graph"])
        graph["nodes"], graph["edges"] = [], []
        result = oes_validation.validate_snapshot(
            self.request, native.encode(graph), {}, 0, require_hash=True, allow_empty_evidence=True,
        )
        self.assertEqual(result, {"structural": "passed", "evidence": "not-applicable", "checked": 0, "skipped": 0})
        graph["nodes"] = [copy.deepcopy(self.candidate_node("service:refund-worker"))]
        with self.assertRaisesRegex(ValueError, "Only an empty owner baseline"):
            oes_validation.validate_snapshot(self.request, native.encode(graph), {}, 0, allow_empty_evidence=True)

    def test_malformed_oes_schema_returns_safe_structured_failure(self):
        for schema in ({"type": "SECRET_INVALID_TYPE"}, {"$ref": "#/$defs/SECRET_MISSING_REF"}):
            with self.subTest(schema=schema), mock.patch.object(native, "load_graph_schema", return_value=schema):
                report = self.error("invalid-oes-contract")
            self.assertNotIn("SECRET", json.dumps(report))

    def test_exports_use_checked_pending_bytes_and_refuse_overwrite(self):
        result = self.check()
        self.p["graph"]["metadata"]["contextdProposal"]["status"] = "approved"
        path = self.root / "candidate.graph.json"
        native.export(result, graph_path=path)
        self.assertEqual(path.read_bytes(), result.graph_bytes)
        self.assertEqual(read(path)["metadata"]["contextdProposal"]["status"], "pending")
        with self.assertRaises(ValueError):
            native.export(result, graph_path=path)
        self.assertEqual(path.read_bytes(), result.graph_bytes)

    def test_pending_export_is_rejected_by_actual_consumer_boundary(self):
        result = self.check()
        ws = self.root / "workspaces/default"
        (ws / "ontology").mkdir(parents=True)
        path = ws / "ontology/candidate.graph.json"
        native.export(result, graph_path=path)
        for marker in ({"id": "proposal:refund-receipts", "status": "pending"}, None, "approved"):
            graph = json.loads(result.graph_bytes)
            graph["metadata"]["contextdProposal"] = marker
            path.write_bytes(native.encode(graph))
            with self.subTest(marker=marker), mock.patch.object(oes_context, "_validate", side_effect=AssertionError("must stop before OES")):
                with self.assertRaisesRegex(ValueError, "pending review candidate"):
                    oes_context.load_selection(oes_context.OESRequest(graph=path, cli=self.cli),
                                               wiki_root=self.root, workspace="default", task="refund-worker",
                                               keywords=["refund-worker"], source_records={})

    def test_owner_admitted_fixture_preserves_claim_dimensions_in_context(self):
        result = self.check()
        ws = self.root / "workspaces/default"
        (ws / "ontology").mkdir(parents=True)
        (ws / "rules").mkdir()
        source = self.sources / "rules/refund-receipts.md"
        source_bytes = source.read_bytes()
        (ws / "rules/refund-receipts.md").write_bytes(source_bytes)
        (ws / "workspace.md").write_text("# Workspace\n\n## Packs\n\n(none)\n")
        (self.root / "agents").mkdir()
        (self.root / "agents/constraints.md").write_text("# Constraints\nPreserve owner review states.\n")
        (self.root / ".contextd").mkdir()
        (self.root / ".contextd/config.json").write_text(json.dumps({
            "workspace": "default", "knowledge_root": ".", "packs": [],
        }))
        # Synthetic owner-issued fixture, not an approval implementation. Only
        # its admission declaration changes; hypotheses/claims stay unpromoted.
        graph = json.loads(result.graph_bytes)
        graph["metadata"]["contextdProposal"]["status"] = "approved"
        path = ws / "ontology/owner-approved.graph.json"
        path.write_bytes(native.encode(graph))
        request = oes_context.OESRequest(graph=path, cli=self.cli)
        built = engine.build_context_result(
            "Implement refund-worker receipts", self.root, "default", [], project_dir=self.root,
            synapse_as_of=date(2026, 11, 4), oes_request=request,
        )
        citations = [citation for doc in built.artifact["referenced_docs"]
                     for citation in doc.get("oes_evidence", [])]
        citation = next(item for item in citations if item["edge_id"] == "edge:worker-receipt-rule")
        expected = self.candidate_node("rule:refund-receipt")["properties"]
        for field in ("model", "verification", "scope", "review", "freshness", "status"):
            self.assertEqual(citation["to_node"][field], expected[field])
        self.assertEqual(citation["assertion_status"], "hypothesis")
        self.assertEqual(citation["locator"], "L15")
        Draft7Validator(read(ROOT / "templates/task-context.schema.json")).validate(built.artifact)
        rendered = "\n".join(doc["content"] for doc in built.artifact["referenced_docs"])
        self.assertIn('"verification": "observed"', rendered)
        # Review/model dimensions are preserved output data, never new search seeds.
        selection = oes_context.load_selection(
            request, wiki_root=self.root, workspace="default", task="to-be observed current",
            keywords=["to-be", "observed", "current"], source_records={
                "workspaces/default/rules/refund-receipts.md": oes_context.SourceRecord(
                    text=source_bytes.decode("utf-8"), source_hash=hashlib.sha256(source_bytes).hexdigest(),
                ),
            },
        )
        self.assertEqual(selection.metadata["matched_node_ids"], [])
        self.assertEqual(selection.citations_by_path, {})

    def test_incomplete_or_untrusted_validator_reports_fail_closed(self):
        graph = native.encode(self.p["graph"])
        payloads = {"rules/refund-receipts.md": (self.sources / "rules/refund-receipts.md").read_bytes()}
        for report in (
            {"command": "check-graph", "passed": True, "diagnostics": [], "evidence": {"checked": 2, "skipped": 1}},
            {"command": "check-graph", "passed": True, "diagnostics": [], "evidence": {"checked": True, "skipped": 0}},
            {"command": "check-graph", "passed": True},
            {"command": "other", "passed": True, "diagnostics": [], "evidence": {"checked": 2, "skipped": 0}},
        ):
            result = subprocess.CompletedProcess([], 0, json.dumps(report), "")
            with self.subTest(report=report), mock.patch.object(oes_validation.subprocess, "run", return_value=result):
                with self.assertRaises(ValueError):
                    oes_validation.validate_snapshot(self.request, graph, payloads, 2, require_hash=True)
        with mock.patch.object(oes_validation.subprocess, "run", side_effect=subprocess.TimeoutExpired("oes", 0.01)):
            self.error("oes-template-unavailable")

    def command(self, *args, script=None):
        return subprocess.run([
            sys.executable, str(script or ROOT / "scripts/cmd_graph_authoring.py"),
            "--baseline", str(FIX / "baseline.json"), "--workspace", "default", "--project", "refund-demo",
            "--source-root", str(self.sources), "--oes-cli", str(self.cli), *args,
        ], cwd=self.root, capture_output=True, text=True, timeout=30)

    def test_cli_native_import_validate_and_export_round_trip(self):
        proposal, graph = self.root / "proposal.json", self.root / "graph.json"
        result = self.command("--graph", str(FIX / "candidate.graph.json"),
                              "--proposal-id", "proposal:refund-receipts", "--reviewed", "Complete supplied fixture.",
                              "--output-proposal", str(proposal), "--output-graph", str(graph))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        first = json.loads(result.stdout)
        result = self.command("--proposal", str(proposal))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(first["review_input_hash"], json.loads(result.stdout)["review_input_hash"])
        self.assertEqual(first["graph_hash"], hashlib.sha256(graph.read_bytes()).hexdigest())
        self.assertEqual(read(proposal)["graph"], read(graph))

    def test_cli_failures_write_no_outputs_and_do_not_echo_source_prose(self):
        path, output = self.root / "invalid.json", self.root / "must-not-exist.graph.json"
        self.candidate_node("evidence:receipt-policy")["properties"]["excerpt"] = "SECRET_SOURCE_PROSE"
        path.write_bytes(native.encode(self.p))
        result = self.command("--proposal", str(path), "--output-graph", str(output))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse(output.exists())
        self.assertNotIn("SECRET_SOURCE_PROSE", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_exported_skills_run_native_validator_without_contextd_runtime(self):
        bundle = self.root / "skills-bundle"
        export_skills(bundle)
        for name in SKILLS:
            script = bundle / "skills" / name / "scripts/validate.py"
            output = self.root / (name + ".graph.json")
            result = self.command("--proposal", str(FIX / "proposal.json"), "--output-graph", str(output), script=script)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(read(output)["metadata"]["contextdProposal"]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
