#!/usr/bin/env python3
"""Deterministic decision-context delivery/safety tests, not model benchmarks."""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft7Validator
import pack_loader
import mcp_server
from lib import decision_context as dc, pack_validation, task_context_engine as engine

ROOT = Path(__file__).resolve().parent.parent
PACK = "pack-ui-ux"
TASK = "Review keyboard navigation and screen reader behavior"
FOUNDATION = f"{PACK}/accessibility/semantics-basics"
PROCEDURE = f"{PACK}/accessibility/document-accessibility"
SAMPLE = """# Example

A preface constraint remains visible: `pack-sample-preface`.

## Global Principles

`pack-sample-safe` — MUST preserve authorization and actual verification.

## Component: sample

### Mental Model
An observed state with a project-specific definition: LOCAL_DEFINITION.

### Standards
Required recovery and approval steps remain here: REQUIRED_PROCEDURE.

### Strategy
Compare bounded alternatives by objective, evidence and reversibility.

### Judgment
An expert comparison task may differ from a novice single-task flow.

### Failure Signals
A convincing explanation is not an observed outcome.

### Evidence And Stop Conditions
Stop when permission is missing; verify durable outcomes with tools.

### Foundation: basics
OPTIONAL_FOUNDATION explains a generic concept.

### Procedure: recipe
OPTIONAL_RECIPE supplies a suggested sequence, not mandatory execution.
"""
MANIFEST = {"name": "pack-sample", "manifest_version": 3, "context_profile": dc.PROFILE, "components": ["sample"]}


def sample_doc(text=SAMPLE):
    return {"path": "packs/pack-sample/knowledge.md", "source_hash": hashlib.sha256(text.encode()).hexdigest(), "content_full": text}


class DecisionContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "packs", self.root / "packs")
        ws = self.root / "workspaces/default"
        (ws / "agents").mkdir(parents=True)
        (ws / "platform/contracts").mkdir(parents=True)
        (ws / "platform/design").mkdir(parents=True)
        (ws / "workspace.md").write_text("# Workspace\n\n## Packs\n\n- pack-ui-ux\n", encoding="utf-8")
        (ws / "agents/constraints.md").write_text("# Rules\nWorkspace authorization cannot be omitted.\n", encoding="utf-8")
        (ws / "platform/contracts/keyboard.contract.md").write_text("# Keyboard contract\n\n## Rule\nA local definition is authoritative.\n", encoding="utf-8")
        (ws / "platform/design/a11y.md").write_text("# Accessibility\n\n## Flow\nKnown local behavior.\n", encoding="utf-8")
        (self.root / "agents").mkdir()
        (self.root / "agents/constraints.md").write_text("# Engine\nENGINE_AUTHORIZATION\n", encoding="utf-8")
        other = self.root / "workspaces/other/platform/design"
        other.mkdir(parents=True)
        (other / "a11y.md").write_text("FOREIGN_WORKSPACE_SECRET", encoding="utf-8")
        (self.root / ".contextd").mkdir()
        (self.root / ".contextd/config.json").write_text(json.dumps({"workspace": "default", "knowledge_root": ".", "packs": [PACK]}), encoding="utf-8")

    def build(self, request=None, task=TASK, packs=None):
        return engine.build_context_snapshot(task, self.root, "default", packs or [PACK],
                                             project_dir=self.root, synapse_as_of=date(2026, 9, 18), support_request=request)

    def knowledge(self, artifact):
        return next(d for d in artifact["static_context"] if d["path"] == f"packs/{PACK}/knowledge.md")

    def test_default_keeps_decision_core_and_no_mandatory_skill(self):
        a, _ = self.build()
        text = self.knowledge(a)["content"]
        for h in ("### Strategy", "### Judgment", "### Standards", "### Evidence And Stop Conditions"):
            self.assertIn(h, text)
        self.assertNotIn("### Foundation:", text)
        self.assertNotIn("### Procedure:", text)
        self.assertEqual([], a["decision_context"]["packs"][0]["loaded"])
        self.assertEqual("direct-unless-required-by-contract", a["decision_context"]["execution"])
        self.assertIn("pack-ui-ux-accessibility", text)
        self.assertTrue(any("Workspace authorization" in d["content"] for d in a["static_context"]))
        self.assertTrue(any("ENGINE_AUTHORIZATION" in d["content"] for d in a["static_context"]))

    def test_foundation_request_does_not_pull_procedure(self):
        a, _ = self.build({"foundations": [FOUNDATION]})
        text = self.knowledge(a)["content"]
        self.assertIn("### Foundation: semantics-basics", text)
        self.assertNotIn("### Procedure:", text)
        self.assertEqual("explicit-request", a["decision_context"]["packs"][0]["loaded"][0]["reason"])

    def test_procedure_request_does_not_pull_foundation(self):
        a, _ = self.build({"procedures": [PROCEDURE]})
        self.assertIn("### Procedure: document-accessibility", self.knowledge(a)["content"])
        self.assertNotIn("### Foundation:", self.knowledge(a)["content"])

    def test_full_includes_only_selected_components(self):
        a, _ = self.build({"detail": "full"})
        text = self.knowledge(a)["content"]
        self.assertIn("### Foundation:", text)
        self.assertIn("### Procedure:", text)
        self.assertNotIn("## Component: design-system", text)
        self.assertEqual([], a["decision_context"]["packs"][0]["deferred"])

    def test_no_component_keeps_globals_without_teaching(self):
        a, _ = self.build(task="Tune a PostgreSQL index")
        self.assertEqual(["Global Principles"], self.knowledge(a)["sections"])
        self.assertEqual([], a["decision_context"]["packs"][0]["deferred"])
        self.assertNotIn("### Foundation:", self.knowledge(a)["content"])

    def test_unknown_inactive_wrong_kind_or_unrouted_request_fails(self):
        for request in ({"foundations": [FOUNDATION + "-missing"]},
                        {"procedures": [FOUNDATION]},
                        {"foundations": ["pack-inactive/accessibility/basics"]},
                        {"foundations": [f"{PACK}/design-system/hierarchy-basics"]}):
            with self.subTest(request=request), self.assertRaises(ValueError):
                self.build(request)
        self.assertFalse((self.root / ".contextd/context").exists())

    def test_requests_reject_paths_and_invalid_types(self):
        for value in (False, [], {"detail": "smart"}, {"confidence": 1}, {"procedures": True},
                      {"foundations": "abc"}, {"foundations": [None]},
                      {"foundations": ["../../other/private"]},
                      {"foundations": ["/etc/passwd"]}, {"foundations": ["https://example.test/x"]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.build(value)

    def test_request_order_and_duplicates_are_canonical(self):
        task = "Review design system and keyboard navigation"
        refs = [FOUNDATION, f"{PACK}/design-system/hierarchy-basics"]
        a, _ = self.build({"foundations": refs}, task)
        b, _ = self.build({"foundations": list(reversed(refs)) + refs}, task)
        self.assertEqual(a["contextPack"], b["contextPack"])
        self.assertEqual(a["decision_context"], b["decision_context"])

    def test_projection_identity_distinguishes_same_raw_sources(self):
        builds = [self.build(r)[0] for r in (None, {"detail": "full"}, {"foundations": [FOUNDATION]}, {"procedures": [PROCEDURE]})]
        self.assertEqual(4, len({a["contextPack"]["packKey"] for a in builds}))
        self.assertTrue(all(a["source_hashes"] == builds[0]["source_hashes"] for a in builds))
        repeat, _ = self.build()
        self.assertEqual(builds[0]["contextPack"], repeat["contextPack"])

    def test_provenance_and_budget_use_projected_content(self):
        a, _ = self.build()
        full, _ = self.build({"detail": "full"})
        d = self.knowledge(a)
        self.assertEqual(hashlib.sha256((self.root / d["path"]).read_bytes()).hexdigest(), d["source_hash"])
        self.assertEqual(sum(engine._estimate_tokens(d["content"]) for d in a["static_context"]), a["budget_report"]["estimated_tokens_static"])
        self.assertLess(a["budget_report"]["estimated_tokens_total"], full["budget_report"]["estimated_tokens_total"])
        self.assertEqual(a["context_projection"], full["context_projection"])

    def test_contracts_and_workspace_evidence_unchanged(self):
        a, _ = self.build()
        b, _ = self.build({"detail": "full"})
        self.assertEqual(a["referenced_docs"], b["referenced_docs"])
        self.assertEqual(a["gaps"], b["gaps"])
        self.assertEqual(a["governance_report"], b["governance_report"])
        self.assertNotIn("FOREIGN_WORKSPACE_SECRET", json.dumps(a))

    def test_governance_still_reports_missing_required_contract(self):
        policy = self.root / "workspaces/default/policy/context-policy.json"
        policy.parent.mkdir()
        policy.write_text(json.dumps({"rules": [{"id": "must-have-approval", "severity": "error", "require": {"contracts": ["missing-approval"]}}]}))
        a, _ = self.build()
        self.assertEqual("error", a["governance_report"]["status"])
        self.assertIn("missing-approval", json.dumps(a["governance_report"]))

    def test_unprofiled_v3_and_v2_keep_legacy_loading(self):
        path = self.root / f"packs/{PACK}/pack.yaml"
        path.write_text(path.read_text().replace("context_profile: decision-first\n", ""))
        a, _ = self.build()
        self.assertNotIn("decision_context", a)
        self.assertIn("### Foundation:", self.knowledge(a)["content"])
        v2, _ = self.build(packs=["pack-dba"])
        self.assertNotIn("decision_context", v2)
        self.assertTrue(any(d["path"].endswith("agents/coding-rules.md") for d in v2["static_context"]))

    def test_mixed_pack_report_does_not_claim_v2_is_selective(self):
        a, _ = self.build(packs=[PACK, "pack-dba"])
        self.assertEqual(["pack-dba"], a["decision_context"]["unprofiled_packs"])
        self.assertTrue(any(d["path"] == "packs/pack-dba/agents/coding-rules.md" for d in a["static_context"]))

    def test_profile_fails_closed_on_missing_source_and_bad_version(self):
        path = self.root / f"packs/{PACK}/pack.yaml"
        original = path.read_text()
        for text in (original.replace("context_profile: decision-first", "context_profile: automatic"),
                     original.replace("manifest_version: 3", "manifest_version: 2"),
                     original.replace("knowledge: knowledge.md", "knowledge: missing.md")):
            with self.subTest(text=text[:90]):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    self.build()
        path.write_text(original)

    def test_pack_source_symlink_escape_is_rejected(self):
        path = self.root / f"packs/{PACK}/knowledge.md"
        path.unlink()
        path.symlink_to(self.root / "workspaces/other/platform/design/a11y.md")
        with self.assertRaisesRegex(ValueError, "boundary"):
            self.build()

    def test_materialization_separates_modes_and_reuses_snapshot(self):
        a, graph = self.build()
        full, full_graph = self.build({"detail": "full"})
        with patch.object(Path, "read_bytes", side_effect=AssertionError("unexpected reread")):
            saved = engine.materialize_context(a, self.root, synapse_snapshot=graph)
            saved_full = engine.materialize_context(full, self.root, synapse_snapshot=full_graph)
        self.assertNotEqual(saved["materialized"]["pack"], saved_full["materialized"]["pack"])
        text = (self.root / saved["materialized"]["pack"]).read_text()
        self.assertNotIn("### Foundation:", text)
        self.assertNotIn("### Procedure:", text)
        self.assertIn(FOUNDATION, text)  # discoverable metadata, not deferred body
        self.assertEqual("materialized", saved["synapse"]["status"])

    def test_tampered_projection_is_refused_before_any_write(self):
        a, graph = self.build()
        for target in ("content", "request", "key", "missing-report"):
            b = copy.deepcopy(a)
            if target == "content":
                self.knowledge(b)["content"] += "\nUnexpected content"
            elif target == "request":
                b["decision_context"]["request"]["detail"] = "full"
            elif target == "key":
                b["contextPack"]["packKey"] = "invalid"
            else:
                b.pop("decision_context")
            with self.subTest(target=target), self.assertRaises(ValueError):
                engine.materialize_context(b, self.root, synapse_snapshot=graph)
        self.assertFalse((self.root / ".contextd/context").exists())

    def test_markdown_and_explain_expose_support_without_body(self):
        a, _ = self.build()
        md = engine.render_markdown(a)
        self.assertIn("### Strategy", md)
        self.assertIn(FOUNDATION, md)
        self.assertNotIn("A semantic role describes", md)
        explain = engine.build_context_explanation(TASK, self.root, "default", [PACK])
        self.assertEqual(a["decision_context"], explain["artifact"]["decision_context"])

    def test_cli_context_explain_and_legacy_alias(self):
        for cmd in ("context", "task-context", "explain"):
            args = [sys.executable, str(ROOT / "scripts/cli.py"), cmd, TASK, "--format", "json", "--foundation", FOUNDATION]
            if cmd == "context":
                args += ["--preview"]
            result = subprocess.run(args, cwd=self.root, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            a = payload["artifact"] if cmd == "explain" else payload
            self.assertIn("### Foundation:", self.knowledge(a)["content"])
        bad = subprocess.run([sys.executable, str(ROOT / "scripts/cli.py"), "context", TASK, "--foundation", "../private"], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(0, bad.returncode)
        self.assertFalse((self.root / ".contextd/context").exists())

    def test_mcp_input_and_canonical_artifact_parity(self):
        options = mcp_server.ServerOptions(knowledge_root=self.root, workspace="default", cwd=self.root)
        result = mcp_server.call_tool("contextd.context", {"task": TASK, "procedures": [PROCEDURE]}, options)
        a = result["structuredContent"]
        self.assertIn("### Procedure:", self.knowledge(a)["content"])
        self.assertNotIn("### Foundation:", self.knowledge(a)["content"])
        with self.assertRaises(ValueError):
            mcp_server.call_tool("contextd.context", {"task": TASK, "foundations": ["/private"]}, options)
        definition = next(t for t in mcp_server.tool_definitions() if t["name"] == "contextd.context")
        self.assertIn("foundations", definition["inputSchema"]["properties"])

    def test_schema_validates_new_artifact_and_rejects_bad_request(self):
        schema = json.loads((ROOT / "templates/task-context.schema.json").read_text())
        a, _ = self.build()
        Draft7Validator(schema).validate(a)
        a["decision_context"]["request"]["foundations"] = ["../escape"]
        self.assertFalse(Draft7Validator(schema).is_valid(a))

    def test_fenced_examples_do_not_create_sections(self):
        sample = SAMPLE.replace("OPTIONAL_FOUNDATION", "```markdown\n## Component: fake\n### Procedure: hidden\n```\nOPTIONAL_FOUNDATION")
        d = dc.project(sample_doc(sample), MANIFEST, ["sample"], dc.normalize_request())
        self.assertNotIn("OPTIONAL_FOUNDATION", d["content"])
        self.assertEqual(2, len(d["decision_support"]["deferred"]))
        self.assertIn("pack-sample-preface", d["content"])
        self.assertIn("LOCAL_DEFINITION", d["content"])
        self.assertIn("REQUIRED_PROCEDURE", d["content"])

    def test_core_survives_optional_support_requests(self):
        a = dc.project(sample_doc(), MANIFEST, ["sample"], dc.normalize_request())
        b = dc.project(sample_doc(), MANIFEST, ["sample"], dc.normalize_request({"detail": "full"}))
        for token in ("pack-sample-preface", "pack-sample-safe", "LOCAL_DEFINITION", "REQUIRED_PROCEDURE", "### Judgment", "### Evidence And Stop Conditions"):
            self.assertIn(token, a["content"])
            self.assertIn(token, b["content"])
        self.assertNotIn("OPTIONAL_RECIPE", a["content"])
        self.assertNotIn("OPTIONAL_FOUNDATION", a["content"])

    def test_malformed_or_required_optional_content_rejected(self):
        examples = [SAMPLE + "\n```\n", SAMPLE.replace("### Strategy", "### Strategee"),
                    SAMPLE.replace("### Judgment", "### Strategy"),
                    SAMPLE + "\n### Foundation: basics\nDuplicate", SAMPLE.replace("Foundation: basics", "Foundation: ../bad"),
                    SAMPLE.replace("OPTIONAL_FOUNDATION", "MUST verify authorization"),
                    SAMPLE.replace("OPTIONAL_FOUNDATION", "`pack-sample-hidden-rule`"),
                    SAMPLE.replace("### Foundation: basics", "### Procedure: recipe"),
                    SAMPLE.replace("## Global Principles", "## Global Principles\n\n### Foundation: forbidden\nTeaching")]
        for sample in examples:
            with self.subTest(sample=sample[-80:]), self.assertRaises(ValueError):
                dc.validate_knowledge(sample, ["sample"])

    def test_pack_validation_checks_profile_not_only_section_labels(self):
        p = self.root / f"packs/{PACK}/knowledge.md"
        p.write_text(p.read_text().replace("### Judgment", "### Not judgment", 1))
        report = pack_validation.validate_packs(self.root)
        self.assertIn("pack.decision-context", json.dumps(report))
        self.assertNotEqual("ok", report["status"])

    def test_self_route_cannot_reintroduce_deferred_body(self):
        manifest = self.root / f"packs/{PACK}/pack.yaml"
        manifest.write_text(manifest.read_text().replace('accessibility: [platform/design/a11y.md]', f'accessibility: [packs/{PACK}/knowledge.md]'))
        a, _ = self.build()
        for d in a["referenced_docs"] + a["static_context"]:
            if d["path"] == f"packs/{PACK}/knowledge.md":
                self.assertNotIn("### Foundation:", d["content"])
                self.assertNotIn("### Procedure:", d["content"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
