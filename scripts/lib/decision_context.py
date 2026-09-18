"""Decision-first v3 pack projection. No model calls, tool execution or writes.

Only author-classified Foundation/Procedure sections are deferrable. Core
strategy, judgment, constraints and evidence always travel together. Requests
are exact task-scoped IDs, never paths to read or claims about model confidence.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Dict, Iterable, Mapping, Optional

PROFILE = "decision-first"
DETAILS = ("decision-first", "full")
REF_RE = re.compile(r"pack-[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*\Z")
SUPPORT_RE = re.compile(r"(Foundation|Procedure): ([a-z0-9][a-z0-9-]*)\Z")
RULE_RE = re.compile(r"`((?:engine-|ws-|pack-)[a-z0-9][a-z0-9-]*)`")
REQUIRED = {"Mental Model", "Standards", "Strategy", "Judgment", "Failure Signals", "Evidence And Stop Conditions"}


def normalize_request(value: Optional[Mapping] = None) -> Dict:
    if value is None:
        value = {}
    if not isinstance(value, Mapping) or set(value) - {"detail", "foundations", "procedures"}:
        raise ValueError("Decision context expects detail, foundations and procedures only")
    detail = value.get("detail", PROFILE)
    if detail not in DETAILS:
        raise ValueError("Decision context detail must be decision-first or full")
    out = {"detail": detail}
    for kind in ("foundations", "procedures"):
        refs = value.get(kind, [])
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not REF_RE.fullmatch(ref) for ref in refs):
            raise ValueError(f"{kind} must be a list of pack/component/section IDs")
        out[kind] = sorted(set(refs))
    return out


def enabled(manifest: Mapping) -> bool:
    if "context_profile" not in manifest:
        return False
    if manifest.get("context_profile") != PROFILE or manifest.get("manifest_version") != 3:
        raise ValueError("context_profile: decision-first requires manifest_version: 3")
    return True


def headings(text: str, level: int) -> list[tuple[str, int]]:
    """Recognize exact ATX headings outside backtick/tilde fenced examples."""
    found = []
    fence = None
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if marker:
            run, tail = marker.groups()
            if fence is None:
                fence = (run[0], len(run))
            elif run[0] == fence[0] and len(run) >= fence[1] and not tail.strip():
                fence = None
        elif fence is None:
            match = re.match(r"^" + "#" * level + r" (\S[^\r\n]*)\s*$", line)
            if match:
                found.append((match.group(1).strip(), offset))
        offset += len(line)
    if fence is not None:
        raise ValueError("Unclosed Markdown fence in decision-first knowledge")
    return found


def sections(text: str, level: int) -> list[tuple[str, str]]:
    marks = headings(text, level)
    return [(title, text[start:(marks[i + 1][1] if i + 1 < len(marks) else len(text))].strip())
            for i, (title, start) in enumerate(marks)]


def validate_knowledge(text: str, components: Iterable[str]) -> None:
    """Fail closed on ambiguous slices; lexical checks do not prove domain truth."""
    top = sections(text, 2)
    expected = {"Global Principles", *(f"Component: {c}" for c in components)}
    titles = [title for title, _ in top]
    if len(titles) != len(set(titles)) or set(titles) != expected:
        raise ValueError("Decision-first knowledge requires unique Global Principles and declared Component sections only")
    core = [text[:headings(text, 2)[0][1]]]
    optional = []
    for title, body in top:
        sub = sections(body, 3)
        names = [name for name, _ in sub]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate subsection in {title}")
        if title.startswith("Component:"):
            if not REQUIRED.issubset(names):
                raise ValueError(f"{title} missing decision core sections: {', '.join(sorted(REQUIRED - set(names)))}")
            for name, chunk in sub:
                if name in REQUIRED and not chunk.partition("\n")[2].strip():
                    raise ValueError(f"Empty {name} in {title}")
        marks = headings(body, 3)
        core.append(body[:marks[0][1]] if marks else body)
        ids = set()
        for name, chunk in sub:
            match = SUPPORT_RE.fullmatch(name)
            if name.lower().startswith(("foundation", "procedure")) and not match:
                raise ValueError(f"Invalid optional heading: {name}; use Foundation: slug or Procedure: slug")
            if not match:
                core.append(chunk)
                continue
            if title == "Global Principles":
                raise ValueError("Global Principles cannot contain optional support")
            if match[2] in ids:
                raise ValueError(f"Duplicate support ID {match[2]} in {title}")
            ids.add(match[2])
            if not chunk.partition("\n")[2].strip():
                raise ValueError(f"Empty support section {name}")
            # Normative obligations belong in core even when they describe a
            # foundation or an exact procedure. A human review is still needed.
            if re.search(r"\b(?:MUST|SHALL|PHẢI)\b", chunk):
                raise ValueError(f"Required instruction in optional {name}; keep it in core")
            optional.append(chunk)
    core_ids = set(RULE_RE.findall("\n".join(core)))
    optional_ids = set(RULE_RE.findall("\n".join(optional)))
    if optional_ids - core_ids:
        raise ValueError("Optional support cannot be the only definition of a stable rule ID")


def project(doc: Dict, manifest: Mapping, selected: Iterable[str], request: Mapping) -> Dict:
    text = doc["content_full"]
    validate_knowledge(text, manifest.get("components") or [])
    chosen = set(selected) & set(manifest.get("components") or [])
    chunks, titles, loaded, deferred, full_chunks = [], [], [], [], []
    pack = manifest["name"]
    prefix = text[:headings(text, 2)[0][1]].strip() or "# Pack Knowledge"
    for title, body in sections(text, 2):
        if title != "Global Principles" and title.split(": ", 1)[1] not in chosen:
            continue
        titles.append(title)
        full_chunks.append(body)
        if title == "Global Principles":
            chunks.append(body)
            continue
        marks = headings(body, 3)
        kept = [body[:marks[0][1]].strip()]
        component = title.split(": ", 1)[1]
        for name, content in sections(body, 3):
            match = SUPPORT_RE.fullmatch(name)
            if match is None:
                kept.append(content)
                continue
            kind = "foundations" if match[1] == "Foundation" else "procedures"
            ref = f"{pack}/{component}/{match[2]}"
            include = request["detail"] == "full" or ref in request[kind]
            item = {"ref": ref, "kind": kind,
                    "reason": "explicit-request" if ref in request[kind] else ("full-detail" if include else "on-demand")}
            (loaded if include else deferred).append(item)
            if include:
                kept.append(content)
        chunks.append("\n\n".join(kept))
    content = prefix + "\n\n" + "\n\n".join(chunks)
    full = prefix + "\n\n" + "\n\n".join(full_chunks)
    out = {"category": "pack-knowledge", "path": doc["path"], "source_hash": doc["source_hash"],
           "sections": titles, "content": content,
           "decision_support": {"pack": pack, "loaded": loaded, "deferred": deferred,
                                "estimated_tokens_full": max(1, len(full) // 4),
                                "estimated_tokens_selected": max(1, len(content) // 4)}}
    for key in ("redacted", "redaction_findings"):
        if key in doc:
            out[key] = doc[key]
    return out


def report_for(docs: list[Dict], packs: list[str], request: Mapping) -> Optional[Dict]:
    reports = sorted((d["decision_support"] for d in docs if "decision_support" in d), key=lambda r: r["pack"])
    available = {kind: {item["ref"] for r in reports for item in r["loaded"] + r["deferred"] if item["kind"] == kind}
                 for kind in ("foundations", "procedures")}
    for kind in available:
        missing = set(request[kind]) - available[kind]
        if missing:
            raise ValueError(f"Unknown, inactive or unrouted {kind}: {', '.join(sorted(missing))}. Inspect contextd explain for task-scoped support IDs.")
    if not reports and request == normalize_request():
        return None
    return {"version": "1", "request": dict(request), "packs": reports, "enabled_packs": list(packs),
            "unprofiled_packs": sorted(set(packs) - {r["pack"] for r in reports}),
            "execution": "direct-unless-required-by-contract",
            "selection_basis": "author-profile-and-explicit-request; not model self-confidence"}


def identity(report: Mapping, docs: list[Dict]) -> str:
    payload = {"report": report, "rendered_sources": sorted(
        ({"path": d["path"], "sections": d["sections"],
          "content_hash": hashlib.sha256(d["content"].encode("utf-8")).hexdigest()} for d in docs),
        key=lambda d: d["path"])}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def render_report(report: Optional[Mapping]) -> list[str]:
    if not report:
        return []
    lines = ["", "## Decision Context", f"Detail: {report['request']['detail']}",
             "Execution: direct; required contracts, permissions and verification still apply."]
    for pack in report["packs"]:
        lines.append(f"- {pack['pack']}: ~{pack['estimated_tokens_selected']} selected / ~{pack['estimated_tokens_full']} full pack-knowledge tokens")
        for status in ("loaded", "deferred"):
            for item in pack[status]:
                flag = "--foundation" if item["kind"] == "foundations" else "--procedure"
                lines.append(f"  - {status}: {item['ref']} ({item['reason']}; {flag} {item['ref']})")
    if report["unprofiled_packs"]:
        lines.append("- Unprofiled packs retain existing loading: " + ", ".join(report["unprofiled_packs"]))
    return lines


def add_arguments(parser) -> None:
    parser.add_argument("--context-detail", choices=DETAILS, default=PROFILE,
                        help="Profiled v3 packs: decision core (default) or full selected components")
    parser.add_argument("--foundation", action="append", default=[], metavar="PACK/COMPONENT/ID",
                        help="Include an exact task-scoped foundation section; repeatable")
    parser.add_argument("--procedure", action="append", default=[], metavar="PACK/COMPONENT/ID",
                        help="Include optional execution guidance; never required solely by a strategy")


def request_from_args(args) -> Dict:
    return {"detail": args.context_detail, "foundations": args.foundation, "procedures": args.procedure}
