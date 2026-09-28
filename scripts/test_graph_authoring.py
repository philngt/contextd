"""New authoring contracts, read-only CLI, standalone export and staging isolation."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lib.graph_authoring import MAX_INPUT_BYTES, read_json, validate
from export_graph_authoring import export, SKILLS

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "templates/graph-authoring"
FIX = ROOT / "examples/graph-authoring"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.p = load(FIX / "proposal.json")
        self.b = load(FIX / "baseline.json")
        self.o = load(RES / "product-software.v1.json")
        self.schemas = {"proposal": load(RES / "graph-proposal.schema.json"),
                        "baseline": load(RES / "graph-baseline.schema.json")}

    def check(self):
        return validate(self.p, self.b, self.o, workspace="default", project_id="order-demo", schemas=self.schemas)

    def has_error(self, code):
        result = self.check()
        self.assertFalse(result["valid"])
        self.assertIn(code, [x["code"] for x in result["errors"]])

    def test_fixture_keeps_three_models_and_gap(self):
        r = self.check()
        self.assertTrue(r["valid"])
        self.assertEqual({c["model"] for c in self.p["claims"]}, {"as-is", "to-be", "reference"})
        self.assertEqual([x["code"] for x in r["warnings"]], ["review-issue:implementation-gap"])
        for flag in ("apply_supported", "execution_authorized", "sources_verified", "live_baseline_verified"):
            self.assertIs(r[flag], False)

    def test_exact_fifteen_types(self):
        self.assertEqual(set(self.o["node_types"]), {
            "Problem", "Feature", "Spec", "Decision", "Note", "Evidence", "Actor",
            "DomainType", "Action", "Workflow", "BusinessRule", "Screen", "Component",
            "Interface", "AcceptanceCriterion"})

    def test_no_mutation_and_deterministic_report(self):
        before = copy.deepcopy((self.p, self.b, self.o))
        self.assertEqual(self.check(), self.check())
        self.assertEqual((self.p, self.b, self.o), before)

    def test_hash_tracks_proposal_and_profile(self):
        first = self.check()["review_input_hash"]
        self.p["claims"][0]["statement"] += " Changed."
        self.assertNotEqual(first, self.check()["review_input_hash"])
        second = self.check()["review_input_hash"]
        self.o["principles"].append("Additional review guidance.")
        self.assertNotEqual(second, self.check()["review_input_hash"])

    def test_profile_not_hardcoded_in_core(self):
        self.o["node_types"]["CustomThing"] = {"module": "extension", "description": "Reviewed extension."}
        self.p["nodes"][0]["type"] = "CustomThing"
        self.p["edges"] = []
        self.assertTrue(self.check()["valid"])

    def test_stale_revision(self):
        self.p["base_revision"] = "old"
        self.has_error("stale-base-revision")

    def test_workspace_mismatch(self):
        self.p["workspace"] = "other"
        self.has_error("workspace-mismatch")

    def test_project_mismatch(self):
        self.b["project_id"] = "other"
        self.has_error("project-mismatch")

    def test_profile_version_mismatch(self):
        self.p["ontology"]["version"] = "2"
        self.has_error("ontology-mismatch")

    def test_duplicate_new_id(self):
        self.p["nodes"].append(copy.deepcopy(self.p["nodes"][0]))
        self.has_error("identity-collision")

    def test_preserve_existing_id(self):
        self.p["nodes"][0]["id"] = "action:cancel-order"
        self.has_error("identity-collision")

    def test_preserve_retired_reserved_id(self):
        self.b["reserved_ids"].append(self.p["nodes"][0]["id"])
        self.has_error("identity-collision")

    def test_duplicate_baseline_id(self):
        self.b["nodes"].append(copy.deepcopy(self.b["nodes"][0]))
        self.has_error("duplicate-baseline-id")

    def test_unknown_node_type(self):
        self.p["nodes"][0]["type"] = "JavaClass"
        self.has_error("unsupported-node-type")

    def test_evidence_has_required_record(self):
        self.p["nodes"][0]["type"] = "Evidence"
        self.has_error("evidence-record-required")

    def test_missing_source(self):
        self.p["evidence"][0]["source_id"] = "src:absent"
        self.has_error("missing-source")

    def test_duplicate_source(self):
        self.p["sources"].append(copy.deepcopy(self.p["sources"][0]))
        self.has_error("duplicate-source-id")

    def test_missing_evidence(self):
        self.p["claims"][0]["evidence_refs"] = ["evidence:absent"]
        self.has_error("missing-evidence")

    def test_missing_claim_subject(self):
        self.p["claims"][0]["subject"] = "node:absent"
        self.has_error("missing-claim-subject")

    def test_invalid_edge_kind(self):
        self.p["edges"][0]["kind"] = "related_to"
        self.has_error("unsupported-edge-kind")

    def test_invalid_edge_endpoint_type(self):
        self.p["edges"][0]["kind"] = "performs"
        self.has_error("invalid-edge-endpoint-type")

    def test_constrains_signatures_are_not_cross_product(self):
        edge = self.p["edges"][0]
        edge.update(kind="constrains", **{"from": "rule:cancel-eligibility", "to": "action:cancel-order"})
        self.has_error("invalid-edge-endpoint-type")

    def test_missing_edge_endpoint(self):
        self.p["edges"][0]["to"] = "node:absent"
        self.has_error("missing-edge-endpoint")

    def test_duplicate_edge(self):
        edge = copy.deepcopy(self.p["edges"][0]); edge["id"] = "edge:duplicate"
        self.p["edges"].append(edge)
        self.has_error("duplicate-edge")

    def test_scoped_edges_not_collapsed(self):
        edge = copy.deepcopy(self.p["edges"][0]); edge["id"] = "edge:as-is"
        edge["qualifiers"]["model"] = "as-is"
        self.p["edges"].append(edge)
        self.assertTrue(self.check()["valid"])

    def test_suggested_identity_requires_review(self):
        self.p["identity_matches"][0]["basis"] = "suggested"
        r = self.check()
        self.assertTrue(r["valid"])
        self.assertIn("identity-review-required", [x["code"] for x in r["warnings"]])

    def test_reuse_target_must_exist(self):
        self.p["identity_matches"][0]["target_id"] = "node:absent"
        self.has_error("missing-reuse-target")

    def test_ambiguous_candidate(self):
        self.p["identity_matches"].append(copy.deepcopy(self.p["identity_matches"][0]))
        self.has_error("ambiguous-candidate-id")

    def test_missing_issue_subject(self):
        self.p["issues"][0]["subjects"] = ["claim:absent"]
        self.has_error("missing-issue-subject")

    def test_missing_baseline_visible(self):
        self.p["sources"][0]["content_hash"] = None
        r = self.check()
        self.assertTrue(r["valid"])
        self.assertIn("incomplete-source-baseline", [x["code"] for x in r["warnings"]])
        self.p["sources"][0]["limitations"] = []
        self.has_error("missing-baseline-limitation")

    def test_no_autoapproval(self):
        for collection, field, value in ((None,"status","applied"), ("nodes","status","active"),
                                         ("claims","review","accepted")):
            with self.subTest(collection=collection):
                before = copy.deepcopy(self.p)
                (self.p if collection is None else self.p[collection][0])[field] = value
                self.has_error("invalid-shape:const")
                self.p = before

    def test_no_unknown_mutation_fields(self):
        self.p["delete_nodes"] = ["action:cancel-order"]
        self.has_error("invalid-shape:additionalProperties")

    def test_schema_error_does_not_echo_source_prose(self):
        self.p["claims"][0]["model"] = "SECRET_PAYLOAD"
        self.assertNotIn("SECRET_PAYLOAD", json.dumps(self.check()))

    def test_empty_wrong_shapes_fail_cleanly(self):
        for value in (None, [], "bad", {}, {"artifact_type": "contextd_graph_proposal.v1"}):
            with self.subTest(value=value):
                self.p = value
                self.assertFalse(self.check()["valid"])

    def test_profile_rejects_arbitrary_execution_fields(self):
        self.o["loader"] = "run arbitrary command"
        with self.assertRaises(ValueError):
            self.check()

    def test_schemas_are_valid(self):
        from jsonschema import Draft202012Validator
        for schema in self.schemas.values():
            Draft202012Validator.check_schema(schema)

    def test_id_cannot_end_in_newline(self):
        self.p["nodes"][0]["id"] += "\n"
        self.has_error("invalid-shape:not")

    def test_fixture_source_hashes(self):
        for source in self.p["sources"]:
            raw = (FIX / source["locator"]).read_bytes()
            self.assertEqual(source["content_hash"], hashlib.sha256(raw).hexdigest())


class IOAndCLITests(unittest.TestCase):
    def test_json_duplicate_keys_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    read_json(path)

    def test_size_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_bytes(b' ' * (MAX_INPUT_BYTES + 1))
            with self.assertRaises(ValueError):
                read_json(path)

    def test_symlink_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory); (path / "real.json").write_text('{}')
            try:
                (path / "link.json").symlink_to(path / "real.json")
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaises(ValueError):
                read_json(path / "link.json")

    def test_directory_input(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                read_json(Path(directory))

    def command(self, *extra, script=None, no_site=False):
        return subprocess.run([sys.executable, *(['-S'] if no_site else []),
            str(script or ROOT / 'scripts/cmd_graph_authoring.py'),
            '--proposal', str(FIX/'proposal.json'), '--baseline', str(FIX/'baseline.json'),
            '--workspace','default','--project','order-demo', *extra],
            capture_output=True, text=True, cwd=ROOT, timeout=30)

    def test_cli_default_and_strict(self):
        self.assertEqual(self.command().returncode, 0)
        self.assertEqual(self.command('--strict').returncode, 1)

    def test_cli_binding_failure(self):
        r = self.command('--workspace','foreign')
        self.assertEqual(r.returncode, 1)
        self.assertFalse(json.loads(r.stdout)['valid'])

    def test_cli_no_dependency(self):
        r = self.command(no_site=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn('optional jsonschema', r.stderr)
        self.assertNotIn('Traceback', r.stderr)

    def test_cli_no_writes_or_locator_reads(self):
        before = {p:p.read_bytes() for p in FIX.rglob('*') if p.is_file()}
        r = self.command()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(before, {p:p.read_bytes() for p in FIX.rglob('*') if p.is_file()})
        with tempfile.TemporaryDirectory() as directory:
            proposal = load(FIX/'proposal.json')
            proposal['sources'][0]['locator'] = 'https://never-fetch.invalid/private'
            path = Path(directory)/'proposal.json'; path.write_text(json.dumps(proposal))
            self.assertEqual(self.command('--proposal',str(path)).returncode, 0)

    def test_cli_bad_input_no_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bad.json'; path.write_text('SECRET_NOT_JSON')
            r = self.command('--proposal',str(path))
            self.assertEqual(r.returncode,2)
            self.assertNotIn('SECRET_NOT_JSON', r.stdout+r.stderr)
            self.assertNotIn('Traceback', r.stderr)


class ExportTests(unittest.TestCase):
    def test_export_has_complete_independent_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'plugin'; export(output)
            self.assertEqual(load(output/'.claude-plugin/plugin.json')['name'],'graph-authoring')
            for name in SKILLS:
                skill = output/'skills'/name
                text = (skill/'SKILL.md').read_text()
                self.assertTrue(text.startswith('---\nname: '+name+'\n'))
                self.assertLess(len(text.splitlines()),500)
                self.assertTrue((skill/'references/authoring-contract.md').is_file())
                self.assertTrue((skill/'assets/graph-proposal.schema.json').is_file())
                self.assertEqual((skill/'scripts/graph_authoring.py').read_bytes(),
                                 (ROOT/'scripts/lib/graph_authoring.py').read_bytes())
                args=[sys.executable,str(skill/'scripts/validate.py'),
                      '--proposal',str(FIX/'proposal.json'),'--baseline',str(FIX/'baseline.json'),
                      '--workspace','default','--project','order-demo']
                r=subprocess.run(args,capture_output=True,text=True,cwd=directory,timeout=30)
                self.assertEqual(r.returncode,0,r.stderr)

    def test_export_refuses_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            marker=Path(directory)/'keep.txt'; marker.write_text('user data')
            with self.assertRaises(FileExistsError):
                export(Path(directory))
            self.assertEqual(marker.read_text(),'user data')

    def test_export_refuses_symlink_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'real').mkdir()
            try:
                (root/'link').symlink_to(root/'real',target_is_directory=True)
            except (OSError,NotImplementedError):
                self.skipTest('symlinks unavailable')
            with self.assertRaises(ValueError):
                export(root/'link'/'plugin')


@unittest.skipUnless((ROOT/'scripts/lib/synapse_engine.py').is_file(), 'requires full source checkout')
class StagingIsolationTests(unittest.TestCase):
    def test_actual_synapse_scanner_excludes_proposal_staging(self):
        from lib.synapse_engine import _is_governed_source
        with tempfile.TemporaryDirectory() as directory:
            ws = Path(directory)
            self.assertTrue(_is_governed_source(ws/'draft.md', ws))
            for rel in ('.contextd/graph-authoring/proposal.md',
                        'projects/shop/.contextd/graph-authoring/notes.md',
                        '.contextd/graph-authoring/baseline.json'):
                self.assertFalse(_is_governed_source(ws/rel, ws), rel)


if __name__ == '__main__':
    unittest.main()
