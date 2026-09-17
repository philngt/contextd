#!/usr/bin/env python3
"""Pack delivery/regression tests, not a benchmark of agent reasoning quality.

Run with Python >= 3.10: python scripts/test_pack_cognition.py
"""
from __future__ import annotations

from datetime import date
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import pack_loader
from lib import pack_validation, task_context_engine as engine

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "scripts/test-fixtures/pack-cognition"
CASES = json.loads((FIXTURES / "scenarios.json").read_text(encoding="utf-8"))["cases"]
BASELINE = json.loads((FIXTURES / "compatibility.json").read_text(encoding="utf-8"))
LABELS = ("Observe", "Mechanism", "Choose", "Exception", "Verify", "Stop")
AS_OF = date(2026, 9, 17)


def manifest(name: str) -> dict:
    return pack_loader._parse_simple_yaml(
        (ROOT / "packs" / name / "pack.yaml").read_text(encoding="utf-8")
    )


def build(root: Path, task: str, names: list[str]) -> dict:
    return engine.build_context_artifact(
        task, root, "default", names, project_dir=root, synapse_as_of=AS_OF,
    )


class PackCognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        shutil.copytree(ROOT / "packs", cls.root / "packs")
        # Deliberately minimal workspace: missing domain knowledge must stay a
        # gap, never be borrowed from another workspace or silently fabricated.
        ws = cls.root / "workspaces/default"
        ws.mkdir(parents=True)
        (ws / "workspace.md").write_text("# Workspace\n\n## Packs\n", encoding="utf-8")
        sibling = cls.root / "workspaces/other/platform/design"
        sibling.mkdir(parents=True)
        (sibling / "a11y.md").write_text(
            "# Accessibility\n\nOTHER_WORKSPACE_PRIVATE_SENTINEL\n", encoding="utf-8",
        )

    def test_catalog_and_scenario_coverage(self) -> None:
        names = {p.name for p in (ROOT / "packs").glob("pack-*") if p.is_dir()}
        self.assertEqual(names, {case["pack"] for case in CASES})
        self.assertEqual(names, set(BASELINE["packs"]))
        self.assertEqual(15, len(names))
        self.assertEqual(18, len(CASES))
        for case in CASES:
            with self.subTest(pack=case["pack"], component=case["component"]):
                self.assertIn(case["component"], manifest(case["pack"])["components"])
                for field in ("review_scenario", "expected_evidence", "reject"):
                    self.assertGreater(len(case[field]), 35)
        # Semantic quality of these cases requires separate human/agent trials.

    def test_contracts_routes_and_validator_code_remain_compatible(self) -> None:
        for name, old in BASELINE["packs"].items():
            with self.subTest(pack=name):
                current = manifest(name)
                contract = {key: current[key] for key in BASELINE["contract_fields"]}
                contract_bytes = json.dumps(
                    contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                ).encode("utf-8")
                self.assertEqual(old["contract_sha256"],
                                 hashlib.sha256(contract_bytes).hexdigest(), name)
                digest = hashlib.sha256(
                    (ROOT / "packs" / name / "scripts/rules.py").read_bytes()
                ).hexdigest()
                self.assertEqual(old["validator_sha256"], digest)
        report = pack_validation.validate_packs(ROOT)
        self.assertEqual("ok", report["status"], report)
        self.assertEqual({
            "design-system": ["platform/design/design-system.md", "platform/design/tokens.md"],
            "accessibility": ["platform/design/a11y.md"],
            "user-flows": ["domains/{domain}/flows/*.md"],
            "ux-writing": ["platform/design/ux-writing.md"],
        }, manifest("pack-ui-ux")["retrieval"])

    def test_positive_and_neighboring_negative_routing(self) -> None:
        for case in CASES:
            with self.subTest(pack=case["pack"], component=case["component"]):
                self.assertEqual([case["component"]], engine.detect_components(
                    case["positive_task"], ROOT, [case["pack"]],
                ))
                self.assertEqual([], engine.detect_components(
                    case["negative_task"], ROOT, [case["pack"]],
                ))

    def test_every_declared_component_still_routes(self) -> None:
        for name in BASELINE["packs"]:
            for component, words in manifest(name)["keywords"].items():
                with self.subTest(pack=name, component=component):
                    self.assertIn(component, engine.detect_components(
                        f"Review {words[0]}", ROOT, [name],
                    ))

    def test_v2_lenses_are_delivered_and_bounded(self) -> None:
        count = 0
        for name in BASELINE["packs"]:
            if int(manifest(name)["manifest_version"]) != 2:
                continue
            count += 1
            with self.subTest(pack=name):
                artifact = build(self.root, "Review a neighboring task", [name])
                docs = {doc["path"]: doc for doc in artifact["static_context"]}
                doc = docs[f"packs/{name}/agents/coding-rules.md"]
                lens = doc["content"].split("## Domain Decision Lens\n", 1)[1]
                for label in LABELS:
                    self.assertRegex(lens, rf"\*\*{label}:\*\*\s+\S")
                self.assertLessEqual(engine._estimate_tokens(lens), 650)
                self.assertEqual([], artifact["intent"]["components"])
                # Explicitly enabled v2 guidance still loads for a negative
                # task; we do NOT assert nonexistent keyword-based pack elision.
        self.assertEqual(13, count)

    def test_ui_component_slices_reduce_static_pack_cost(self) -> None:
        for case in (case for case in CASES if case["pack"] == "pack-ui-ux"):
            with self.subTest(component=case["component"]):
                artifact = build(self.root, case["positive_task"], [case["pack"]])
                docs = {doc["path"]: doc for doc in artifact["static_context"]}
                knowledge = docs["packs/pack-ui-ux/knowledge.md"]
                self.assertEqual([
                    "Global Principles", f"Component: {case['component']}",
                ], knowledge["sections"])
                for label in LABELS:
                    self.assertIn(f"**{label}:**", knowledge["content"])
                self.assertFalse(any(
                    path.startswith("packs/pack-ui-ux/agents/") for path in docs
                ))
                pack_tokens = sum(engine._estimate_tokens(doc["content"])
                                  for path, doc in docs.items()
                                  if path.startswith("packs/pack-ui-ux/"))
                self.assertLess(pack_tokens, BASELINE["ui_v2_static_tokens"])
                self.assert_budget(artifact)

    def test_v3_globals_load_without_unselected_components(self) -> None:
        for name in ("pack-ui-ux", "pack-operator-steering"):
            with self.subTest(pack=name):
                artifact = build(self.root, "Tune PostgreSQL lock waits", [name])
                knowledge = next(doc for doc in artifact["static_context"]
                                 if doc["path"] == f"packs/{name}/knowledge.md")
                self.assertEqual(["Global Principles"], knowledge["sections"])
                self.assertNotIn("## Component:", knowledge["content"])
                if name == "pack-operator-steering":
                    lens = knowledge["content"].split("### Domain Decision Lens", 1)[1]
                    for label in LABELS:
                        self.assertIn(f"**{label}:**", lens)
                    self.assertLessEqual(engine._estimate_tokens(lens), 650)

    def assert_budget(self, artifact: dict) -> None:
        budget = artifact["budget_report"]
        static = sum(engine._estimate_tokens(doc["content"])
                     for doc in artifact["static_context"])
        self.assertEqual(static, budget["estimated_tokens_static"])
        self.assertEqual(sum(budget["estimated_tokens_static_by_category"].values()), static)
        self.assertLessEqual(budget["estimated_tokens_total"],
                             static + budget["estimated_tokens_referenced"])

    def test_multi_pack_determinism_budget_and_workspace_isolation(self) -> None:
        args = (self.root, "Review keyboard navigation and rules of hooks",
                ["pack-ui-ux", "pack-frontend-react"])
        first, second = build(*args), build(*args)
        self.assertEqual(first["contextPack"], second["contextPack"])
        self.assertEqual(first["source_hashes"], second["source_hashes"])
        self.assertEqual(first["static_context"], second["static_context"])
        self.assert_budget(first)
        self.assertLess(first["budget_report"]["estimated_tokens_total"], 12000)
        self.assertTrue(first["gaps"])
        self.assertNotIn("OTHER_WORKSPACE_PRIVATE_SENTINEL", json.dumps(first))
        for doc in first["referenced_docs"] + first["static_context"]:
            self.assertFalse(doc["path"].startswith("workspaces/other/"))
        # A pure snapshot must not materialize knowledge or artifacts.
        self.assertFalse((self.root / ".contextd").exists())

    def test_ui_validator_positive_and_safe_fixtures(self) -> None:
        path = ROOT / "packs/pack-ui-ux/scripts/rules.py"
        spec = importlib.util.spec_from_file_location("cognition_ui_rules", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def rules_at(path: str, text: str) -> set[str]:
            return {v["rule"] for rule in module.RULES
                    for v in rule(Path(path), text.splitlines(), {})}

        prefix = "pack-ui-ux-"
        examples = [
            ("hardcoded-color", "platform/design/example.md", "Accent #123456", "Accent uses an approved token."),
            ("missing-a11y-note", "platform/design/design-system.md", "# Component", "> A11y: keyboard and focus are specified."),
            ("flow-no-error-path", "domains/checkout/flows/guest.md", "# Success", "## Error and recovery paths"),
            ("contrast-unchecked", "platform/design/example.md", "color-primary-default", "color-primary-default; contrast 4.5:1"),
        ]
        for suffix, relative, bad, clean in examples:
            with self.subTest(rule=suffix):
                path = "/fixture/" + relative
                self.assertIn(prefix + suffix, rules_at(path, bad))
                self.assertNotIn(prefix + suffix, rules_at(path, clean))
        self.assertNotIn(prefix + "hardcoded-color", rules_at(
            "/fixture/platform/design/tokens.md", "Accent #123456",
        ))
        self.assertNotIn(prefix + "hardcoded-color", rules_at(
            "/fixture/platform/design/example.md", "```text\n#123456\n```",
        ))
        self.assertEqual(set(), rules_at("/fixture/notes.md", "Accent #123456"))
        canonical = (ROOT / "packs/pack-ui-ux/knowledge.md").read_text(encoding="utf-8")
        for suffix, *_ in examples:
            self.assertIn(prefix + suffix, canonical)
        self.assertIn("> A11y:", canonical)

    def test_scaffold_template_has_authoring_lenses(self) -> None:
        template = (ROOT / "templates/pack-knowledge.md").read_text(encoding="utf-8")
        for section in template.split("## Component:")[1:]:
            for label in LABELS:
                self.assertIn(f"**{label}:**", section)
            for heading in ("Mental Model", "Standards", "Failure Signals", "Evidence And Stop Conditions"):
                self.assertIn(f"### {heading}", section)


if __name__ == "__main__":
    unittest.main(verbosity=2)
