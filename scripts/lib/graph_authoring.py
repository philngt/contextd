"""Opt-in graph proposal validation. Never extracts, applies, or builds task context.

The caller supplies an owner-produced baseline and explicit workspace/project binding.
Source locators are inert strings: no network, source-code execution or source scanning.
jsonschema is an optional authoring dependency, not a dependency of context compilation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")
MAX_INPUT_BYTES = 4 * 1024 * 1024


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


def _nonfinite(_: str) -> None:
    raise ValueError("Non-finite JSON number")


def read_json(path: Path) -> Any:
    """Read one explicitly selected regular file, never a symlink or a source locator."""
    path = path.absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("Symlink inputs are not supported")
    if not path.is_file():
        raise ValueError("Input must be a regular file")
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("Input exceeds 4 MiB")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                      parse_constant=_nonfinite)


def _profile(profile: Any) -> None:
    """Only vocabulary is configurable. Profiles are data, never plugins or code."""
    keys = {"artifact_type", "id", "version", "node_types", "evidence_type", "edge_types", "principles"}
    if (not isinstance(profile, dict) or set(profile) != keys
            or profile["artifact_type"] != "contextd_ontology_profile.v1"
            or not isinstance(profile["id"], str) or not ID.fullmatch(profile["id"])
            or not isinstance(profile["version"], str) or not profile["version"]
            or not isinstance(profile["node_types"], dict) or not profile["node_types"]
            or len(profile["node_types"]) > 100
            or not isinstance(profile["edge_types"], dict) or len(profile["edge_types"]) > 100
            or not isinstance(profile["evidence_type"], str)
            or profile["evidence_type"] not in profile["node_types"]
            or not isinstance(profile["principles"], list)
            or any(not isinstance(x, str) for x in profile["principles"])):
        raise ValueError("Unsupported or malformed ontology profile")
    for name, definition in profile["node_types"].items():
        if (not isinstance(name, str) or not ID.fullmatch(name)
                or not isinstance(definition, dict) or set(definition) != {"module", "description"}
                or any(not isinstance(x, str) or not x for x in definition.values())):
            raise ValueError("Invalid profile node definition")
    for name, alternatives in profile["edge_types"].items():
        if (not isinstance(name, str) or not ID.fullmatch(name)
                or not isinstance(alternatives, list) or not alternatives or len(alternatives) > 100):
            raise ValueError("Invalid profile relation definition")
        for definition in alternatives:
            if not isinstance(definition, dict) or set(definition) != {"from", "to"}:
                raise ValueError("Invalid profile relation signature")
            for side in ("from", "to"):
                values = definition[side]
                if (not isinstance(values, list) or not values
                        or any(not isinstance(v, str) or v not in {*profile["node_types"], "*"}
                               for v in values)):
                    raise ValueError("Invalid profile relation endpoint types")


def validate(proposal: Any, baseline: Any, profile: Any, *, workspace: str,
             project_id: str, schemas: dict[str, dict]) -> dict:
    """Check shape/references/binding without modifying any input or resolving meaning.

    Schemas are trusted bundled resources. Do not expose arbitrary schema loading as an
    API: remote references are intentionally not part of the authoring contract.
    A matching caller-supplied revision is not proof that a live project has not changed.
    """
    from jsonschema import Draft202012Validator

    _profile(profile)
    if (not isinstance(workspace, str) or not isinstance(project_id, str)
            or not ID.fullmatch(workspace) or not ID.fullmatch(project_id)):
        raise ValueError("Expected workspace and project must be valid local IDs")
    errors: list[dict] = []
    warnings: list[dict] = []

    def error(code: str, at: str) -> None:
        errors.append({"code": code, "at": at})

    def warn(code: str, at: str) -> None:
        warnings.append({"code": code, "at": at})

    for label, value in (("proposal", proposal), ("baseline", baseline)):
        for problem in Draft202012Validator(schemas[label]).iter_errors(value):
            # Do not echo source prose or jsonschema messages that may contain secrets.
            error("invalid-shape:" + str(problem.validator),
                  label + "/" + "/".join(map(str, problem.absolute_path)))

    def report() -> dict:
        return {
            "artifact_type": "contextd_graph_proposal_report.v1",
            "valid": not errors,
            "review_input_hash": _digest({"proposal": proposal, "baseline": baseline,
                                           "profile": profile}),
            "errors": sorted(errors, key=lambda x: (x["at"], x["code"])),
            "warnings": sorted(warnings, key=lambda x: (x["at"], x["code"])),
            "apply_supported": False, "execution_authorized": False,
            "semantic_review_required": True, "sources_verified": False,
            "live_baseline_verified": False,
        }

    if errors:
        return report()
    expected_ontology = {"id": profile["id"], "version": profile["version"]}
    for name, value in (("proposal", proposal), ("baseline", baseline)):
        if value["workspace"] != workspace:
            error("workspace-mismatch", name)
        if value["project_id"] != project_id:
            error("project-mismatch", name)
        if value["ontology"] != expected_ontology:
            error("ontology-mismatch", name)
    if proposal["base_revision"] != baseline["revision"]:
        error("stale-base-revision", "proposal/base_revision")

    types = profile["node_types"]
    evidence_type = profile["evidence_type"]
    node_types: dict[str, str] = {}
    existing: set[str] = set()
    for i, node in enumerate(baseline["nodes"]):
        if node["id"] in existing:
            error("duplicate-baseline-id", f"baseline/nodes/{i}")
        existing.add(node["id"])
        node_types[node["id"]] = node["type"]
        if node["type"] not in types:
            error("unsupported-node-type", f"baseline/nodes/{i}")
    for i, value in enumerate(baseline["reserved_ids"]):
        if value in existing:
            error("duplicate-baseline-id", f"baseline/reserved_ids/{i}")
        existing.add(value)

    new_ids: set[str] = set()
    for collection in ("nodes", "evidence", "claims", "edges", "issues"):
        for i, item in enumerate(proposal[collection]):
            if item["id"] in existing or item["id"] in new_ids:
                error("identity-collision", f"proposal/{collection}/{i}")
            new_ids.add(item["id"])
    for collection in ("nodes", "evidence"):
        for i, node in enumerate(proposal[collection]):
            node_types[node["id"]] = node["type"]
            if node["type"] not in types:
                error("unsupported-node-type", f"proposal/{collection}/{i}")
            if ((collection == "evidence") != (node["type"] == evidence_type)):
                error("evidence-record-required", f"proposal/{collection}/{i}")

    source_ids: set[str] = set()
    for i, source in enumerate(proposal["sources"]):
        if source["id"] in source_ids:
            error("duplicate-source-id", f"proposal/sources/{i}")
        source_ids.add(source["id"])
        if source["revision"] is None or source["content_hash"] is None:
            warn("incomplete-source-baseline", f"proposal/sources/{i}")
            if not source["limitations"]:
                error("missing-baseline-limitation", f"proposal/sources/{i}")
    for i, evidence in enumerate(proposal["evidence"]):
        if evidence["source_id"] not in source_ids:
            error("missing-source", f"proposal/evidence/{i}")

    evidence_ids = {item["id"] for item in proposal["evidence"]}
    for collection in ("nodes", "claims", "edges", "identity_matches", "issues"):
        for i, item in enumerate(proposal[collection]):
            if not set(item["evidence_refs"]) <= evidence_ids:
                error("missing-evidence", f"proposal/{collection}/{i}")
    for i, claim in enumerate(proposal["claims"]):
        if claim["subject"] not in node_types:
            error("missing-claim-subject", f"proposal/claims/{i}")
        if claim["verification"] in {"inferred", "unknown"}:
            warn("claim-needs-verification", f"proposal/claims/{i}")
        if claim["freshness"] == "stale":
            warn("stale-claim", f"proposal/claims/{i}")

    edge_keys = set()
    for i, edge in enumerate(proposal["edges"]):
        at = f"proposal/edges/{i}"
        kind = profile["edge_types"].get(edge["kind"])
        if kind is None:
            error("unsupported-edge-kind", at)
            continue
        if edge["from"] == edge["to"]:
            error("self-edge", at)
        for side in ("from", "to"):
            if edge[side] not in node_types:
                error("missing-edge-endpoint", at + "/" + side)
        if all(edge[side] in node_types for side in ("from", "to")) and not any(
            all("*" in signature[side] or node_types[edge[side]] in signature[side]
                for side in ("from", "to")) for signature in kind
        ):
            error("invalid-edge-endpoint-type", at)
        key = (edge["kind"], edge["from"], edge["to"], _digest(edge["qualifiers"]))
        if key in edge_keys:
            error("duplicate-edge", at)
        edge_keys.add(key)

    candidates = set()
    baseline_nodes = {node["id"]: node["type"] for node in baseline["nodes"]}
    for i, match in enumerate(proposal["identity_matches"]):
        at = f"proposal/identity_matches/{i}"
        if match["candidate_id"] in candidates or match["candidate_id"] in node_types:
            error("ambiguous-candidate-id", at)
        candidates.add(match["candidate_id"])
        if match["target_id"] not in baseline_nodes:
            error("missing-reuse-target", at)
        if match["basis"] == "suggested":
            warn("identity-review-required", at)
    subjects = set(node_types) | {x["id"] for x in proposal["claims"] + proposal["edges"]}
    for i, issue in enumerate(proposal["issues"]):
        if not set(issue["subjects"]) <= subjects:
            error("missing-issue-subject", f"proposal/issues/{i}")
        warn("review-issue:" + issue["kind"], f"proposal/issues/{i}")
    if not proposal["nodes"] and not proposal["claims"] and not proposal["edges"]:
        warn("no-model-additions", "proposal")
    return report()


def main(argv: list[str] | None = None, *, resources: Path) -> int:
    parser = argparse.ArgumentParser(description="Validate an additive graph proposal; never apply it.")
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--workspace", required=True, help="Explicit resolved workspace ID")
    parser.add_argument("--project", required=True, help="Canonical product/project ID, not a folder name")
    parser.add_argument("--profile", type=Path, help="Optional versioned vocabulary JSON")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on warnings as well as errors")
    args = parser.parse_args(argv)
    try:
        result = validate(read_json(args.proposal), read_json(args.baseline),
                          read_json(args.profile or resources / "product-software.v1.json"),
                          workspace=args.workspace, project_id=args.project,
                          schemas={key: read_json(resources / filename) for key, filename in (
                              ("proposal", "graph-proposal.schema.json"),
                              ("baseline", "graph-baseline.schema.json"))})
        print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=True))
    except ImportError:
        print('Graph authoring requires the optional jsonschema dependency. In an authorized '
              'environment install contextd with the [authoring] extra.', file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, RecursionError):
        # Do not echo untrusted file contents, paths, JSON fragments or exception messages.
        print("Invalid, unsafe or unreadable graph-authoring input; inspect the local files.", file=sys.stderr)
        return 2
    return 1 if not result["valid"] or (args.strict and result["warnings"]) else 0
