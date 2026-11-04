"""Shared, stdlib-only transport to a trusted local OES installation.

Callers own source selection, workflow policy and schema validation. OES owns
ontology and exact excerpt checks. Only retained bytes enter the temporary
source tree; graph data never selects an executable or follows a remote URL.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from typing import Dict, Optional


DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class OESRequest:
    graph: Optional[Path] = None
    cli: Optional[Path] = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


def validator_command(request: OESRequest) -> list:
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


def _run(request: OESRequest, args: list):
    if (
        not isinstance(request.timeout_seconds, (int, float))
        or isinstance(request.timeout_seconds, bool)
        or not math.isfinite(request.timeout_seconds)
        or request.timeout_seconds <= 0
    ):
        raise ValueError("OES timeout must be a finite positive number")
    try:
        return subprocess.run(
            validator_command(request) + args,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=request.timeout_seconds, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("OES validator timed out; requested validation refused") from exc
    except OSError as exc:
        raise ValueError("Cannot execute OES validator") from exc


def _report(result, command: str) -> dict:
    try:
        report = json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "OES validator must support check-graph --with-evidence --json; "
            "update the OES checkout"
        ) from exc
    if not isinstance(report, dict):
        raise ValueError("OES returned an invalid validation report")
    diagnostics = report.get("diagnostics")
    if (result.returncode != 0 or report.get("passed") is not True
            or report.get("command") != command or diagnostics != []):
        # Diagnostics can contain source text. Surface bounded code tokens only.
        codes = sorted({
            item["code"] if isinstance(item.get("code"), str)
            and re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", item["code"])
            else "validation-error"
            for item in diagnostics if isinstance(item, dict)
        }) if isinstance(diagnostics, list) else []
        detail = ", ".join(codes[:10]) or "incomplete structural/evidence validation report"
        raise ValueError("OES validation failed: " + detail)
    return report


def validate_snapshot(request: OESRequest, graph_bytes: bytes, payloads: Dict,
                      evidence_count: int, *, require_hash: bool = False,
                      allow_empty_evidence: bool = False) -> Dict:
    """Validate exactly these graph/source bytes, never the live source files.

    An explicitly empty owner baseline can request structural-only validation.
    Every nonempty candidate must contain evidence and receive a complete,
    warning-free textual report. No report can silently skip a source.
    """
    empty = evidence_count == 0 and allow_empty_evidence
    if empty:
        try:
            graph = json.loads(graph_bytes)
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid empty OES baseline") from exc
        if not isinstance(graph, dict) or graph.get("nodes") != [] or graph.get("edges") != []:
            raise ValueError("Only an empty owner baseline may omit evidence")
    try:
        with tempfile.TemporaryDirectory(prefix="contextd-oes-") as temp:
            snapshot = Path(temp)
            source_root = snapshot / "sources"
            source_root.mkdir()
            for uri, payload in payloads.items():
                if (not isinstance(uri, str) or not uri
                        or re.search(r"^[A-Za-z][A-Za-z\d+.-]*:|[\\\x00-\x1f\x7f%?#]", uri)
                        or uri.startswith("/")
                        or any(part in ("", ".", "..") for part in uri.split("/"))):
                    raise ValueError("Unsafe OES source snapshot path")
                target = source_root.joinpath(*PurePosixPath(uri).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            graph_path = snapshot / "graph.json"
            graph_path.write_bytes(graph_bytes)
            args = ["check-graph", str(graph_path), "--warnings-as-errors", "--json"]
            if not empty:
                args += ["--with-evidence", "--source-root", str(source_root)]
                if require_hash:
                    args.append("--require-hash")
            result = _run(request, args)
    except OSError as exc:
        raise ValueError("Cannot prepare the OES source snapshot") from exc
    report = _report(result, "check-graph")
    if empty:
        if "evidence" in report:
            raise ValueError("OES returned an invalid empty-baseline report")
        return {"structural": "passed", "evidence": "not-applicable", "checked": 0, "skipped": 0}
    evidence = report.get("evidence")
    if (not isinstance(evidence, dict)
            or type(evidence.get("checked")) is not int
            or evidence["checked"] != evidence_count
            or type(evidence.get("skipped")) is not int
            or evidence["skipped"] != 0 or evidence_count <= 0):
        raise ValueError("OES validation failed: incomplete structural/evidence validation report")
    return {"structural": "passed", "evidence": "passed", "checked": evidence_count, "skipped": 0}


def load_graph_schema(request: OESRequest) -> dict:
    """Read OES's envelope schema from the same trusted installation as its CLI."""
    entrypoint = Path(validator_command(request)[-1]).resolve()
    path = entrypoint.parent.parent / "contracts" / "graph-envelope.schema.json"
    try:
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("OES graph schema exceeds the supported size")
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("OES installation must include contracts/graph-envelope.schema.json") from exc
    if not isinstance(schema, dict):
        raise ValueError("OES graph schema must be an object")

    def local_references(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("$ref", "$dynamicRef") and (
                    not isinstance(item, str) or not item.startswith("#")
                ):
                    raise ValueError("OES schema must not require external reference retrieval")
                local_references(item)
        elif isinstance(value, list):
            for item in value:
                local_references(item)

    local_references(schema)
    return schema


def compile_template(request: OESRequest, template: str) -> dict:
    """Use OES to resolve the template and bind review to its compiled contents."""
    if not isinstance(template, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}", template):
        raise ValueError("Invalid OES template ID")
    try:
        with tempfile.TemporaryDirectory(prefix="contextd-oes-template-") as temp:
            path = Path(temp) / "template.json"
            result = _run(request, ["compile-template", template, "-o", str(path), "--json"])
            _report(result, "compile-template")
            compiled = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Cannot read the OES compiled template") from exc
    if (not isinstance(compiled, dict) or compiled.get("apiVersion") != "oes/v1"
            or compiled.get("kind") != "OntologyTemplate"
            or not isinstance(compiled.get("metadata"), dict)
            or compiled["metadata"].get("id") != template
            or not isinstance(compiled["metadata"].get("version"), str)
            or not compiled["metadata"]["version"]
            or not isinstance(compiled.get("entityTypes"), dict)
            or not isinstance(compiled.get("relationTypes"), dict)):
        raise ValueError("OES returned an invalid compiled template")
    return compiled
