"""OES-native pending proposals, with contextd-owned review workflow checks.

The v2 payload is a complete oes.graph/v1 snapshot. OES defines its vocabulary
and validates its graph and quotations. This adapter never migrates the legacy
15-type profile, approves a proposal, or applies changes to an owner graph.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

if __package__:
    from .context_security import block_reason
    from .graph_authoring import ID, _digest
    from .oes_validation import OESRequest, compile_template, load_graph_schema, validate_snapshot
else:  # Self-contained exported skill scripts, without the contextd runtime.
    from context_security import block_reason
    from graph_authoring import ID, _digest
    from oes_validation import OESRequest, compile_template, load_graph_schema, validate_snapshot


MAX_SOURCE_BYTES = 5 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 50 * 1024 * 1024


@dataclass(frozen=True)
class NativeResult:
    report: dict
    graph_bytes: bytes | None = None
    proposal_bytes: bytes | None = None


def encode(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def import_graph(graph: dict, *, baseline: dict, workspace: str, project_id: str,
                 proposal_id: str, reviewed: list[str], not_reviewed: list[str]) -> dict:
    """Wrap a supplied native graph as a pending copy; never infer approval."""
    candidate = deepcopy(graph)
    if not isinstance(candidate, dict) or not isinstance(candidate.get("metadata"), dict):
        raise ValueError("An imported OES graph must have metadata")
    candidate["metadata"]["contextdProposal"] = {"id": proposal_id, "status": "pending"}
    return {
        "artifact_type": "contextd_graph_proposal.v2", "proposal_id": proposal_id,
        "workspace": workspace, "project_id": project_id,
        "base_revision": baseline.get("revision"), "status": "pending",
        "scope": {"reviewed": list(reviewed), "not_reviewed": list(not_reviewed)},
        "graph": candidate, "identity_matches": [], "issues": [],
    }


def _source_snapshots(graph: dict, source_root: Path) -> tuple[dict, list]:
    """Capture only explicitly named files, once, with literal relative paths.

    Unlike context consumption this accepts a selected authoring source root,
    including code. It does not make those sources governed workspace knowledge.
    """
    # The caller explicitly selects this root. Resolve aliases such as macOS
    # /var -> /private/var once; source-controlled descendants cannot redirect it.
    root = source_root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Authoring source root must be an existing directory")
    payloads: dict[str, bytes] = {}
    sources = []
    total = 0
    for node in graph["nodes"]:
        if node["type"] != "Source":
            continue
        props = node["properties"]
        uri = props.get("uri")
        if (not isinstance(uri, str) or not uri
                or re.search(r"^[A-Za-z][A-Za-z\d+.-]*:|[\\\x00-\x1f\x7f%?#]", uri)
                or uri.startswith("/")
                or any(part in ("", ".", "..") for part in uri.split("/"))):
            raise ValueError("Authoring Source.uri must be a literal path under --source-root")
        target = root.joinpath(*PurePosixPath(uri).parts)
        if (any(part.is_symlink() for part in (target, *target.parents))
                or block_reason(target) or not target.is_file()):
            raise ValueError("Authoring source is missing, blocked or a symlink")
        if uri not in payloads:
            with target.open("rb") as stream:
                raw = stream.read(MAX_SOURCE_BYTES + 1)
            if len(raw) > MAX_SOURCE_BYTES:
                raise ValueError("Authoring source exceeds 5 MiB")
            total += len(raw)
            if total > MAX_SNAPSHOT_BYTES:
                raise ValueError("Authoring source snapshot exceeds 50 MiB")
            payloads[uri] = raw
        digest = hashlib.sha256(payloads[uri]).hexdigest()
        expected = props.get("sha256")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            raise ValueError("Every authoring Source must declare its complete raw-byte sha256")
        if expected.lower() != digest:
            raise ValueError("Authoring source bytes differ from the declared sha256")
        sources.append({"id": node["id"], "uri": uri, "sha256": digest,
                        "bytes": len(payloads[uri])})
    return payloads, sorted(sources, key=lambda item: item["id"])


def _without_records(graph: dict) -> dict:
    header = {key: deepcopy(value) for key, value in graph.items() if key not in ("nodes", "edges")}
    header["metadata"].pop("contextdProposal", None)
    return header


def _is_claim(node: dict, template: dict) -> bool:
    """Inspect OES's compiled inheritance only to enforce pending review state."""
    definitions = template["entityTypes"]
    current, seen = node["type"], set()
    while current in definitions and current not in seen:
        if current == "Claim":
            return True
        seen.add(current)
        current = definitions[current].get("parent")
    return False


def validate(proposal: Any, baseline: Any, *, workspace: str, project_id: str,
             schemas: dict[str, dict], request: OESRequest, source_root: Path) -> NativeResult:
    """Validate a complete candidate against a captured owner baseline.

    Matching revision strings are review preconditions, not a live-owner check.
    Returned export bytes are exactly the pending graph bytes checked by OES.
    """
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
    from referencing.exceptions import Unresolvable

    if (not isinstance(workspace, str) or not ID.fullmatch(workspace)
            or not isinstance(project_id, str) or not ID.fullmatch(project_id)):
        raise ValueError("Expected workspace and project must be valid local IDs")
    errors: list[dict] = []
    warnings: list[dict] = []
    graph_schema, template, sources = None, None, []
    graph_bytes = None
    validation = {"schema": "not-run", "structural": "not-run", "evidence": "not-run"}
    additions = {"nodes": [], "edges": []}

    def error(code: str, at: str, detail: str | None = None):
        errors.append({"code": code, "at": at, **({"detail": detail} if detail else {})})

    def warn(code: str, at: str):
        warnings.append({"code": code, "at": at})

    def finish() -> NativeResult:
        report = {
            "artifact_type": "contextd_graph_proposal_report.v2", "valid": not errors,
            "review_input_hash": _digest({
                "proposal": proposal, "baseline": baseline, "schemas": schemas,
                "oes_schema": graph_schema, "oes_template": template, "sources": sources,
            }),
            "errors": sorted(errors, key=lambda item: (item["at"], item["code"])),
            "warnings": sorted(warnings, key=lambda item: (item["at"], item["code"])),
            "validation": validation, "additions": additions, "sources": sources,
            "apply_supported": False, "execution_authorized": False,
            "semantic_review_required": True, "live_baseline_verified": False,
            "sources_verified": validation["evidence"] == "passed",
        }
        if graph_bytes is not None:
            report["graph_hash"] = hashlib.sha256(graph_bytes).hexdigest()
        if template is not None:
            report["ontology"] = {"id": template["metadata"]["id"],
                                  "version": template["metadata"]["version"],
                                  "compiled_hash": _digest(template)}
        return NativeResult(report, graph_bytes if not errors else None,
                            encode(proposal) if not errors else None)

    for label, value in (("proposal", proposal), ("baseline", baseline)):
        for problem in Draft202012Validator(schemas[label]).iter_errors(value):
            error("invalid-shape:" + str(problem.validator),
                  label + "/" + "/".join(map(str, problem.absolute_path)))
    if errors:
        return finish()
    try:
        graph_schema = load_graph_schema(request)
        Draft202012Validator.check_schema(graph_schema)
    except SchemaError:
        error("invalid-oes-contract", "graph", "The OES graph envelope schema is malformed")
        validation["schema"] = "failed"
        return finish()
    except ValueError as exc:
        error("oes-contract-unavailable", "graph", str(exc))
        return finish()
    try:
        for label, value in (("proposal", proposal), ("baseline", baseline)):
            for problem in Draft202012Validator(graph_schema).iter_errors(value["graph"]):
                error("invalid-oes-shape:" + str(problem.validator),
                      label + "/graph/" + "/".join(map(str, problem.absolute_path)))
    except (SchemaError, Unresolvable, RecursionError):
        error("invalid-oes-contract", "graph", "The OES graph envelope schema has an invalid local reference")
        validation["schema"] = "failed"
        return finish()
    validation["schema"] = "failed" if errors else "passed"
    if errors:
        return finish()

    candidate, previous = proposal["graph"], baseline["graph"]
    for label, value in (("proposal", proposal), ("baseline", baseline)):
        if value["workspace"] != workspace or value["graph"]["metadata"]["workspace"] != workspace:
            error("workspace-mismatch", label)
        if value["project_id"] != project_id or value["graph"]["metadata"]["projectId"] != project_id:
            error("project-mismatch", label)
    if proposal["base_revision"] != baseline["revision"]:
        error("stale-base-revision", "proposal/base_revision")
    if candidate["metadata"]["contextdProposal"]["id"] != proposal["proposal_id"]:
        error("proposal-marker-mismatch", "proposal/graph/metadata/contextdProposal")
    if _digest(_without_records(candidate)) != _digest(_without_records(previous)):
        error("graph-header-changed", "proposal/graph")

    existing: dict[str, tuple[str, dict]] = {}
    for collection in ("nodes", "edges"):
        for i, record in enumerate(previous[collection]):
            if record["id"] in existing:
                error("duplicate-baseline-id", f"baseline/graph/{collection}/{i}")
            existing[record["id"]] = (collection, record)
    reserved = set(baseline["reserved_ids"])
    if reserved.intersection(existing):
        error("duplicate-baseline-id", "baseline/reserved_ids")
    proposed: dict[str, tuple[str, dict]] = {}
    for collection in ("nodes", "edges"):
        for i, record in enumerate(candidate[collection]):
            identifier = record["id"]
            proposed[identifier] = (collection, record)
            if identifier in reserved:
                error("identity-collision", f"proposal/graph/{collection}/{i}")
            if identifier not in existing:
                additions[collection].append(identifier)
    for identifier, record in existing.items():
        if _digest(proposed.get(identifier)) != _digest(record):
            error("existing-record-changed", "proposal/graph/" + record[0])
    for collection in additions:
        additions[collection].sort()
    if errors:
        return finish()

    nodes = {node["id"]: node for node in candidate["nodes"]}
    evidence_ids = {identifier for identifier, node in nodes.items() if node["type"] == "Evidence"}
    baseline_nodes = {node["id"] for node in previous["nodes"]}
    candidate_ids = set()
    for i, match in enumerate(proposal["identity_matches"]):
        at = f"proposal/identity_matches/{i}"
        if match["candidate_id"] in candidate_ids or match["candidate_id"] in proposed or match["candidate_id"] in reserved:
            error("ambiguous-candidate-id", at)
        candidate_ids.add(match["candidate_id"])
        if match["target_id"] not in baseline_nodes:
            error("missing-reuse-target", at)
        if not set(match["evidence_refs"]) <= evidence_ids:
            error("missing-evidence", at)
        if match["basis"] == "suggested":
            warn("identity-review-required", at)
    issue_ids = set()
    for i, issue in enumerate(proposal["issues"]):
        at = f"proposal/issues/{i}"
        if issue["id"] in proposed or issue["id"] in reserved or issue["id"] in issue_ids or issue["id"] in candidate_ids:
            error("identity-collision", at)
        issue_ids.add(issue["id"])
        if not set(issue["subjects"]) <= set(proposed):
            error("missing-issue-subject", at)
        if not set(issue["evidence_refs"]) <= evidence_ids:
            error("missing-evidence", at)
        warn("review-issue:" + issue["kind"], at)
    if not any(additions.values()):
        warn("no-model-additions", "proposal")
    if errors:
        return finish()

    try:
        template = compile_template(request, candidate["template"])
    except ValueError as exc:
        error("oes-template-unavailable", "proposal/graph/template", str(exc))
        return finish()
    if candidate["metadata"]["ontologyVersion"] != template["metadata"]["version"]:
        error("ontology-version-mismatch", "proposal/graph/metadata/ontologyVersion")
    for i, node in enumerate(candidate["nodes"]):
        if node["id"] in existing or not _is_claim(node, template):
            continue
        if node["properties"].get("status") != "proposed":
            error("new-claim-not-proposed", f"proposal/graph/nodes/{i}/properties/status")
        if node["properties"].get("review", "draft") != "draft":
            error("new-claim-not-draft", f"proposal/graph/nodes/{i}/properties/review")
    if errors:
        return finish()
    graph_bytes = encode(candidate)
    try:
        payloads, sources = _source_snapshots(candidate, source_root)
        checked = validate_snapshot(request, graph_bytes, payloads, len(evidence_ids), require_hash=True)
        validation.update(checked)
        # check-graph resolves the installation's registry in a separate OES
        # process. Refuse an ordinary concurrent template update after the
        # pending-state checks instead of binding review to stale semantics.
        if _digest(compile_template(request, candidate["template"])) != _digest(template):
            error("ontology-changed-during-validation", "proposal/graph/template")
            validation["structural"] = "not-passed"
    except (ValueError, OSError, RuntimeError) as exc:
        # Our snapshot and OES transport exceptions contain no source prose.
        detail = str(exc) if isinstance(exc, ValueError) else "Cannot capture the selected authoring source files"
        error("oes-validation-failed", "proposal/graph", detail)
        validation.update({"structural": "not-passed", "evidence": "not-passed"})
    return finish()


def export(result: NativeResult, *, graph_path: Path | None = None,
           proposal_path: Path | None = None) -> None:
    """Write only validated pending snapshots to explicitly chosen new files."""
    if not result.report["valid"] or result.graph_bytes is None:
        raise ValueError("Only a validated pending proposal can be exported")
    outputs = []
    for path, payload in ((graph_path, result.graph_bytes), (proposal_path, result.proposal_bytes)):
        if path is None:
            continue
        path = path.expanduser().absolute()
        if path.is_symlink():
            raise ValueError("Export destination must not be a symlink")
        # Destination parents are explicit caller choices; preserve portable
        # aliases while exclusively creating a new final file.
        outputs.append((path.parent.resolve(strict=True) / path.name, payload))
    if len({path for path, _ in outputs}) != len(outputs):
        raise ValueError("Export destinations must be distinct new files")
    for path, _ in outputs:
        if (any(part.is_symlink() for part in (path, *path.parents))
                or not path.parent.is_dir() or path.exists()):
            raise ValueError("Export requires a new file under an existing non-symlink directory")
    for path, payload in outputs:
        with path.open("xb") as stream:
            stream.write(payload)
