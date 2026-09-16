"""Standalone unit/schema tests: python scripts/test_graph_projection.py."""
from __future__ import annotations
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.graph_projection import ProjectionRequest, project_graph, render_text

ROOT = Path(__file__).resolve().parents[1]


def node(name, kind="pattern", **overrides):
    return {"id": name, "workspace": "demo", "kind": kind,
            "path": f"workspaces/demo/{name}.md", "memory_class": "long_term",
            "source_hash": hashlib.sha256(name.encode()).hexdigest(),
            "lifecycle": "active", "freshness": "unknown", **overrides}


def edge(source, target, kind="depends_on"):
    return {"id": f"{kind}:{source}:{target}", "source": source, "target": target, "type": kind}


def graph(nodes=None, edges=None):
    return {"artifact_type": "contextd_synapse.v1", "workspace": "demo",
            "synapse_hash": "a" * 64, "as_of": "2026-09-16",
            "nodes": nodes if nodes is not None else [node("a"), node("b"), node("c")],
            "edges": edges if edges is not None else [edge("a", "b"), edge("b", "c")],
            "diagnostics": []}


class ProjectionTests(unittest.TestCase):
    def project(self, g=None, **kwargs):
        return project_graph(g or graph(), ProjectionRequest(("a",), **kwargs))

    def test_two_hop_dependency_chain(self):
        result = self.project()
        self.assertEqual([n["id"] for n in result["nodes"]], ["a", "b", "c"])
        self.assertEqual(result["nodes"][2]["parent"], "b")
        self.assertEqual(result["nodes"][2]["seed"], "a")
        self.assertEqual(result["nodes"][2]["depth"], 2)
        self.assertEqual(result["summary"]["required_neighbor_gaps"], 0)
        self.assertFalse(result["execution_authorized"])

    def test_depth_zero_reports_missing_dependency(self):
        result = self.project(max_depth=0)
        self.assertEqual(len(result["nodes"]), 1)
        self.assertEqual(result["gaps"][0]["reason"], "depth-limit")

    def test_depth_one_reports_frontier_without_recursing(self):
        result = self.project(max_depth=1)
        self.assertEqual([n["id"] for n in result["nodes"]], ["a", "b"])
        self.assertEqual(result["gaps"][0]["target"], "c")

    def test_node_limit_reports_dependency(self):
        result = self.project(max_nodes=1)
        self.assertEqual(result["gaps"][0]["reason"], "node-limit")

    def test_cycles_terminate(self):
        g = graph(edges=[edge("a", "b"), edge("b", "c"), edge("c", "a")])
        result = self.project(g, max_depth=8)
        self.assertEqual(len(result["nodes"]), 3)
        self.assertEqual(len(result["edges"]), 3)

    def test_contract_is_preferred_under_node_pressure(self):
        g = graph([node("a"), node("b"), node("z", "contract")],
                  [edge("a", "b"), edge("a", "z", "implements")])
        result = self.project(g, max_nodes=2)
        self.assertEqual([n["id"] for n in result["nodes"]], ["a", "z"])

    def test_role_cannot_demote_contract_or_hide_implementation_gap(self):
        g = graph([node("a"), node("b", "contract")], [edge("a", "b", "implements")])
        result = project_graph(g, ProjectionRequest(("a",), max_nodes=1),
                               {"b": {"knowledge_role": "strategy"}})
        self.assertEqual(result["summary"]["required_neighbor_gaps"], 1)

    def test_explicit_seeds_are_not_evicted(self):
        result = project_graph(graph(), ProjectionRequest(("c", "a", "c"), max_nodes=2))
        self.assertEqual([n["id"] for n in result["nodes"]], ["a", "c"])
        self.assertEqual(result["request"]["seeds"], ["a", "c"])

    def test_missing_seed_is_not_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, "Unknown seed"):
            project_graph(graph(), ProjectionRequest(("a", "missing")))

    def test_invalid_policy_is_rejected(self):
        bad = [{"seeds": ()}, {"seeds": ("workspace://other/a",)},
               {"seeds": "a"}, {"max_depth": -1}, {"max_depth": 9},
               {"max_depth": True}, {"max_nodes": 0}, {"max_nodes": 129},
               {"max_boundary_edges": 0}, {"edge_types": ("causes",)},
               {"direction": "automatic"}, {"regions": ("../other",)},
               {"regions": "backend"}, {"seeds": ("a", "b"), "max_nodes": 1}]
        for change in bad:
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(ProjectionRequest(("a",)), **change).normalized()

    def test_cross_workspace_nodes_rejected(self):
        with self.assertRaisesRegex(ValueError, "workspace"):
            self.project(graph([node("a", workspace="other")], []))

    def test_unsafe_paths_rejected(self):
        for path in ["/etc/passwd", "workspaces/other/a.md", "workspaces/demo/../other/a.md",
                     "workspaces/demo/./a.md", "workspaces/demo/a\\b.md"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.project(graph([node("a", path=path)], []))

    def test_runtime_memory_rejected(self):
        with self.assertRaises(ValueError):
            self.project(graph([node("a", memory_class="runtime")], []))

    def test_duplicate_nodes_rejected(self):
        with self.assertRaises(ValueError):
            self.project(graph([node("a"), node("a")], []))

    def test_invalid_edges_rejected(self):
        cases = [[edge("a", "missing")], [edge("a", "a")],
                 [edge("a", "b", "causes")], [edge("a", "b"), edge("a", "b")]]
        for edges in cases:
            with self.subTest(edges=edges), self.assertRaises(ValueError):
                self.project(graph(edges=edges))

    def test_filter_cannot_hide_dependency_gap(self):
        result = self.project(edge_types=("supports",))
        self.assertEqual(result["gaps"][0]["reason"], "edge-filter")

    def test_incoming_traversal_preserves_edge_direction(self):
        result = project_graph(graph(), ProjectionRequest(("c",), direction="incoming"))
        self.assertEqual([n["id"] for n in result["nodes"]], ["c", "b", "a"])
        self.assertEqual(result["edges"][0]["source"], "a")

    def test_both_direction_traversal(self):
        result = project_graph(graph(), ProjectionRequest(("b",), direction="both"))
        self.assertEqual({n["id"] for n in result["nodes"]}, {"a", "b", "c"})

    def test_region_filter_is_explicit_no_directory_inference(self):
        metadata = {"a": {"regions": ["backend"]}, "b": {"regions": ["ux"]}}
        result = project_graph(graph(), ProjectionRequest(("a",), regions=("backend",)), metadata)
        self.assertEqual(len(result["nodes"]), 1)
        self.assertEqual(result["gaps"][0]["reason"], "region-boundary")

    def test_unscoped_seed_outside_region_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside requested regions"):
            self.project(regions=("backend",))

    def test_roles_do_not_replace_okf_kind(self):
        result = project_graph(graph(), ProjectionRequest(("a",)),
                               {"a": {"knowledge_role": "strategy", "regions": ["ux", "ux"]}})
        self.assertEqual(result["nodes"][0]["kind"], "pattern")
        self.assertEqual(result["nodes"][0]["knowledge_role"], "strategy")
        self.assertEqual(result["nodes"][0]["regions"], ["ux"])

    def test_bad_semantic_metadata_warns_and_falls_back(self):
        result = project_graph(graph(), ProjectionRequest(("a",)),
                               {"a": {"knowledge_role": [], "regions": "backend"}})
        self.assertEqual(result["nodes"][0]["knowledge_role"], "knowledge")
        self.assertEqual(result["summary"]["metadata_issues"], 2)

    def test_noncurrent_selected_nodes_warn(self):
        g = graph([node("a", lifecycle="draft", freshness="stale")], [])
        self.assertEqual(self.project(g)["warnings"][0]["code"], "selected-noncurrent-node")

    def test_incoming_contradiction_is_not_hidden_by_filter(self):
        g = graph(edges=[edge("b", "a", "contradicts")])
        result = self.project(edge_types=("depends_on",), g=g)
        self.assertEqual(result["warnings"][0]["code"], "contradiction-outside-projection")

    def test_incoming_replacement_is_visible(self):
        g = graph(edges=[edge("b", "a", "supersedes")])
        self.assertEqual(self.project(g)["warnings"][0]["code"], "replacement-outside-projection")

    def test_filtered_internal_relations_are_preserved(self):
        result = project_graph(graph(edges=[edge("a", "b", "contradicts")]),
                               ProjectionRequest(("a", "b"), edge_types=()))
        self.assertEqual(result["edges"][0]["type"], "contradicts")

    def test_frontier_truncation_keeps_true_totals(self):
        g = graph([node("a")] + [node(f"n{i}") for i in range(10)],
                  [edge("a", f"n{i}") for i in range(10)])
        result = self.project(g, max_nodes=1, max_boundary_edges=2)
        self.assertEqual(len(result["gaps"]), 2)
        self.assertEqual(result["summary"]["required_neighbor_gaps"], 10)
        self.assertEqual(result["summary"]["gaps_truncated"], 8)

    def test_input_order_does_not_change_projection(self):
        g = graph([node("a"), node("b"), node("c"), node("z", "contract")],
                  [edge("a", "b"), edge("a", "c"), edge("b", "z"), edge("c", "z")])
        expected = self.project(g)
        for i in range(20):
            shuffled = copy.deepcopy(g)
            random.Random(i).shuffle(shuffled["nodes"])
            random.Random(i + 1).shuffle(shuffled["edges"])
            self.assertEqual(self.project(shuffled), expected)

    def test_request_order_does_not_change_hash(self):
        one = ProjectionRequest(("a", "b"), edge_types=("supports", "depends_on"))
        two = ProjectionRequest(("b", "a"), edge_types=("depends_on", "supports"))
        self.assertEqual(project_graph(graph(), one), project_graph(graph(), two))

    def test_hash_tracks_semantics_not_wall_clock(self):
        g = graph()
        before = self.project(g)
        g["generated_at"] = "2099-01-01T00:00:00Z"
        self.assertEqual(self.project(g)["projection_hash"], before["projection_hash"])
        changed = project_graph(g, ProjectionRequest(("a",)), {"a": {"knowledge_role": "mechanism"}})
        self.assertNotEqual(changed["projection_hash"], before["projection_hash"])

    def test_projection_does_not_mutate_graph_or_metadata(self):
        g = graph()
        metadata = {"a": {"regions": ["ux", "backend"]}}
        original = copy.deepcopy((g, metadata))
        project_graph(g, ProjectionRequest(("a",)), metadata)
        self.assertEqual((g, metadata), original)

    def test_no_document_body_or_arbitrary_fields_are_exported(self):
        g = graph()
        g["nodes"][0]["content"] = "sensitive-body-marker"
        g["nodes"][0]["title"] = "sensitive-title-marker"
        g["diagnostics"] = [{"severity": "warning", "code": "known-warning", "message": "private-marker"}]
        result = self.project(g)
        serialized = json.dumps(result)
        self.assertNotIn("sensitive-", serialized)
        self.assertNotIn("private-marker", serialized)
        self.assertEqual(result["diagnostic_counts"], {"known-warning": 1})

    def test_invalid_artifact_and_hash_rejected(self):
        for update in [{"artifact_type": "other"}, {"synapse_hash": "bad"}, {"as_of": "not-a-date"}]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.project(graph() | update)

    def test_text_declares_advisory_boundary(self):
        text = render_text(self.project())
        self.assertIn("not execution context", text)
        self.assertIn("normal context/policy checks", text)

    def test_schema_and_projection_hash(self):
        import jsonschema
        schema = json.loads((ROOT / "templates/graph-projection.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        result = self.project()
        jsonschema.validate(result, schema, format_checker=jsonschema.FormatChecker())
        claimed = result.pop("projection_hash")
        encoded = json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        self.assertEqual(claimed, hashlib.sha256(encoded.encode()).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
