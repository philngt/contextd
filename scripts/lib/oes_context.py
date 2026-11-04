"""Opt-in OES graph input; OES owns ontology and source-text validation.

Only sources already captured by the active workspace Synapse scan enter the
temporary validation snapshot. Graphs never provide executable configuration.
The adapter selects one-hop evidence sources; it does not infer new assertions.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from typing import Dict, Iterable, Mapping, Optional

from .context_security import block_reason, is_relative_to, redact_text
from .synapse_engine import SourceRecord, resolve_workspace_dir


DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_GRAPH_BYTES = 5 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 50 * 1024 * 1024
NODE_TEXT_FIELDS = ("label", "name", "title", "statement", "summary")


@dataclass(frozen=True)
class OESRequest:
    graph: Optional[Path] = None
    cli: Optional[Path] = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class OESSelection:
    metadata: Dict
    citations_by_path: Dict[str, list]


def add_arguments(parser) -> None:
    parser.add_argument(
        "--oes-graph", default=None,
        help="OES graph within the active workspace (relative to knowledge_root)",
    )
    parser.add_argument(
        "--oes-cli", default=None,
        help="Trusted local OES bin/oes.mjs entrypoint (default: oes on PATH)",
    )
    parser.add_argument(
        "--oes-timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS,
        help="OES validator timeout in seconds (default: %(default)s)",
    )


def request_from_args(args) -> Optional[OESRequest]:
    graph = getattr(args, "oes_graph", None)
    cli = getattr(args, "oes_cli", None)
    timeout = getattr(args, "oes_timeout", DEFAULT_TIMEOUT_SECONDS)
    if graph is None and cli is None and timeout == DEFAULT_TIMEOUT_SECONDS:
        return None
    return OESRequest(
        graph=Path(graph) if graph is not None else None,
        cli=Path(cli) if cli is not None else None,
        timeout_seconds=timeout,
    )


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("OES graph contains duplicate JSON keys")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("OES graph contains a non-JSON numeric constant")


def _graph_snapshot(request: OESRequest, root: Path, workspace_dir: Path):
    if request.graph is None:
        raise ValueError("--oes-cli/--oes-timeout requires --oes-graph")
    path = Path(request.graph).expanduser()
    path = path if path.is_absolute() else root / path
    try:
        actual = path.resolve()
        if not is_relative_to(actual, workspace_dir):
            raise ValueError("OES graph must stay inside the active workspace")
        if block_reason(path) or block_reason(actual):
            raise ValueError("OES graph is blocked by the source security policy")
        if not actual.is_file() or actual.stat().st_size > MAX_GRAPH_BYTES:
            raise ValueError("OES graph must be a local file of at most 5 MiB")
        payload = actual.read_bytes()
        if len(payload) > MAX_GRAPH_BYTES:
            raise ValueError("OES graph exceeds 5 MiB")
        graph = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_unique_object,
            parse_constant=_invalid_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RuntimeError) as exc:
        raise ValueError("Cannot read OES graph as a local UTF-8 JSON file") from exc
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list):
        raise ValueError("OES input must be a graph object with a nodes array")
    metadata = graph.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("workspace") != workspace_dir.name:
        raise ValueError("OES graph metadata.workspace must match the active workspace")
    if not isinstance(metadata.get("id"), str) or not metadata["id"].strip():
        raise ValueError("OES graph metadata.id must be a nonempty string")
    if not isinstance(graph.get("template"), str) or not graph["template"].strip():
        raise ValueError("OES graph template must be a nonempty string")
    if metadata.get("ontologyVersion") is not None and not isinstance(metadata["ontologyVersion"], str):
        raise ValueError("OES graph metadata.ontologyVersion must be a string when supplied")
    return actual, payload, graph


def _source_snapshots(graph: Dict, root: Path, workspace_dir: Path,
                      records: Mapping[str, SourceRecord]):
    """Map only governed local source records; never reread workspace bytes."""
    sources, payloads = {}, {}
    total = 0
    for node in graph["nodes"]:
        if not isinstance(node, dict) or node.get("type") != "Source":
            continue
        props = node.get("properties") or {}
        uri = props.get("uri") if isinstance(props, dict) else None
        if (
            not isinstance(uri, str) or not uri
            or re.search(r"^[a-zA-Z][a-zA-Z\d+.-]*:|[\\\x00-\x1f\x7f%?#]", uri)
            or uri.startswith("/")
            or any(part in ("", ".", "..") for part in uri.split("/"))
        ):
            raise ValueError("OES Source.uri must be a literal workspace-relative path")
        relative = PurePosixPath(uri)
        target = workspace_dir.joinpath(*relative.parts)
        try:
            actual = target.resolve()
        except (OSError, RuntimeError) as exc:
            raise ValueError("OES source path cannot be resolved safely") from exc
        if not is_relative_to(actual, workspace_dir):
            raise ValueError("OES source resolves outside the active workspace")
        if block_reason(target) or block_reason(actual):
            raise ValueError("OES source is blocked by the source security policy")
        path = target.relative_to(root).as_posix()
        source = records.get(path)
        if source is None:
            raise ValueError(
                "OES source is not in the governed active-workspace snapshot: " + uri
            )
        payload = source.text.encode("utf-8")
        if hashlib.sha256(payload).hexdigest() != source.source_hash:
            raise ValueError("OES source record does not match its captured byte hash")
        if uri not in payloads:
            total += len(payload)
            if total > MAX_SNAPSHOT_BYTES:
                raise ValueError("OES source snapshot exceeds 50 MiB")
            payloads[uri] = payload
        source_id = node.get("id")
        if not isinstance(source_id, str):
            raise ValueError("OES Source node needs a string id")
        sources[source_id] = {"path": path, "source_hash": source.source_hash}
    return sources, payloads


def _validator_command(request: OESRequest) -> list:
    if request.cli is not None:
        cli = Path(request.cli).expanduser().resolve()
        if not cli.is_file():
            raise ValueError("OES CLI entrypoint does not exist; pass --oes-cli /path/to/bin/oes.mjs")
        node = shutil.which("node")
        if node is None:
            raise ValueError("OES graph input requires Node.js 20+ on PATH")
        return [node, str(cli)]
    installed = shutil.which("oes")
    if installed is None:
        raise ValueError("OES CLI not found; pass --oes-cli /path/to/oes/bin/oes.mjs")
    return [installed]


def _validate(request: OESRequest, graph_bytes: bytes, payloads: Dict,
              evidence_count: int) -> Dict:
    if (
        not isinstance(request.timeout_seconds, (int, float))
        or isinstance(request.timeout_seconds, bool)
        or not math.isfinite(request.timeout_seconds)
        or request.timeout_seconds <= 0
    ):
        raise ValueError("OES timeout must be a finite positive number")
    command = _validator_command(request)
    try:
        with tempfile.TemporaryDirectory(prefix="contextd-oes-") as temp:
            snapshot = Path(temp)
            source_root = snapshot / "sources"
            source_root.mkdir()
            for uri, payload in payloads.items():
                target = source_root.joinpath(*PurePosixPath(uri).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            graph_path = snapshot / "graph.json"
            graph_path.write_bytes(graph_bytes)
            result = subprocess.run(
                command + [
                    "check-graph", str(graph_path), "--with-evidence",
                    "--source-root", str(source_root), "--warnings-as-errors", "--json",
                ],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=request.timeout_seconds, check=False,
            )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("OES validator timed out; context build refused") from exc
    except OSError as exc:
        raise ValueError("Cannot execute OES validator or prepare its source snapshot") from exc
    try:
        report = json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "OES validator must support check-graph --with-evidence --json; "
            "update the OES checkout"
        ) from exc
    if not isinstance(report, dict):
        raise ValueError("OES returned an invalid validation report")
    evidence = report.get("evidence")
    diagnostics = report.get("diagnostics")
    if (
        result.returncode != 0 or report.get("passed") is not True
        or report.get("command") != "check-graph"
        or diagnostics != [] or not isinstance(evidence, dict)
        or evidence.get("checked") != evidence_count or evidence.get("skipped") != 0
        or evidence_count == 0
    ):
        codes = sorted({
            str(item.get("code", "validation-error"))
            for item in diagnostics if isinstance(item, dict)
        }) if isinstance(diagnostics, list) else []
        detail = ", ".join(codes[:10]) or "incomplete structural/evidence validation report"
        raise ValueError("OES validation failed: " + redact_text(detail)[0])
    return {
        "structural": "passed", "evidence": "passed",
        "checked": evidence_count, "skipped": 0,
    }


def _matches(keyword: str, text: str) -> bool:
    body = r"[\s\-_/]+".join(re.escape(part) for part in keyword.split())
    return bool(body and re.search(r"(?<!\w)" + body + r"(?!\w)", text, re.IGNORECASE))


def _node_ref(node: Dict) -> Dict:
    props = node.get("properties") or {}
    result = {"id": node["id"], "type": node["type"]}
    for field in (*NODE_TEXT_FIELDS, "status"):
        if isinstance(props.get(field), str):
            result[field] = props[field]
    return result


def _redact(value):
    if isinstance(value, str):
        return redact_text(value)[0]
    if isinstance(value, dict):
        return {key: _redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def load_selection(request: OESRequest, *, wiki_root: Path, workspace: str,
                   task: str, keywords: Iterable[str],
                   source_records: Mapping[str, SourceRecord]) -> OESSelection:
    root = wiki_root.resolve()
    workspace_dir = resolve_workspace_dir(root, workspace)
    if workspace_dir is None or not workspace_dir.is_dir():
        raise ValueError("OES graph input requires a valid active workspace")
    graph_path, graph_bytes, graph = _graph_snapshot(request, root, workspace_dir)
    sources, payloads = _source_snapshots(graph, root, workspace_dir, source_records)
    evidence_count = sum(
        isinstance(node, dict) and node.get("type") == "Evidence" for node in graph["nodes"]
    )
    validation = _validate(request, graph_bytes, payloads, evidence_count)
    # OES has now checked the ontology, identities, edges, evidence references,
    # exact source line spans, and any declared source hashes on these bytes.
    nodes = {node["id"]: node for node in graph["nodes"]}
    words = sorted({word for word in keywords if isinstance(word, str) and word})
    matched = set()
    for node in nodes.values():
        if node["type"] in ("Source", "Evidence"):
            continue
        props = node.get("properties") or {}
        text = "\n".join([node["id"]] + [
            props[field] for field in NODE_TEXT_FIELDS if isinstance(props.get(field), str)
        ])
        if any(_matches(word, text) for word in words) or _matches(node["id"], task):
            matched.add(node["id"])
    graph_hash = hashlib.sha256(graph_bytes).hexdigest()
    graph_id = graph["metadata"]["id"]
    citations, matched_edges = {}, []
    for edge in sorted(graph["edges"], key=lambda item: item["id"]):
        seeds = sorted(matched.intersection((edge["from"], edge["to"])))
        if not seeds:
            continue
        refs = edge.get("evidenceIds") or []
        if not refs and edge["type"] == "supportedBy" and nodes[edge["to"]]["type"] == "Evidence":
            refs = [edge["to"]]
        if not refs:
            continue
        matched_edges.append(edge["id"])
        for evidence_id in sorted(set(refs)):
            props = nodes[evidence_id]["properties"]
            source_id = props["sourceId"]
            source = sources[source_id]
            citation = {
                "graph_id": graph_id, "graph_hash": graph_hash,
                "template": graph["template"], "edge_id": edge["id"],
                "relation": edge["type"],
                "from_node": _node_ref(nodes[edge["from"]]),
                "to_node": _node_ref(nodes[edge["to"]]),
                "assertion_status": edge.get("assertionStatus") or "asserted",
                "matched_node_ids": seeds,
                "evidence_id": evidence_id, "source_id": source_id,
                "source_path": source["path"], "source_hash": source["source_hash"],
                "locator": props["locator"], "excerpt": props["excerpt"],
                "evidence_check": "matched",
            }
            if edge.get("properties"):
                citation["relation_properties"] = edge["properties"]
            for source_field, target_field in (
                ("confidence", "confidence"), ("validFrom", "valid_from"), ("validTo", "valid_to"),
            ):
                if source_field in edge:
                    citation[target_field] = edge[source_field]
            safe_citation = _redact(citation)
            if safe_citation != citation:
                safe_citation["redacted"] = True
            citations.setdefault(source["path"], []).append(safe_citation)
    metadata = _redact({
        "graph_path": graph_path.relative_to(root).as_posix(),
        "graph_hash": graph_hash, "graph_id": graph_id,
        "template": graph["template"],
        "ontology_version": graph["metadata"].get("ontologyVersion"),
        "validation": validation, "matched_node_ids": sorted(matched),
        "matched_edge_ids": matched_edges,
    })
    return OESSelection(metadata, dict(sorted(citations.items())))


def render_evidence(citations: list) -> str:
    """Render provenance as quoted data, with uncertainty explicit for agents."""
    if not citations:
        return ""
    lines = [
        "", "#### OES evidence", "",
        "OES checked graph structure and exact source excerpts. These checks do "
        "not establish semantic truth or approve an assertion. Assertion and "
        "claim statuses below remain the graph author's declarations.", "",
    ]
    for citation in citations:
        # JSON strings escape embedded newlines; prefix every data line as a
        # blockquote so source content cannot break out of a generated fence.
        lines.append(
            f"- ({citation['source_path']}:{citation['locator']}) — "
            f"{citation['assertion_status']}; excerpt matched"
        )
        lines.append("")
        lines.append(
            "> " + json.dumps(citation, sort_keys=True, ensure_ascii=False)
        )
        lines.append("")
    return "\n".join(lines).rstrip()
