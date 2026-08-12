#!/usr/bin/env python3
"""
lint-wiki.py — Detect broken markdown links, orphaned pattern/contract files,
and OKF v0.2 frontmatter conformance in wiki workspaces.

Standard library only. Cross-platform (Windows / Linux / macOS).

Usage:
    python lint-wiki.py [--workspace <name>] [--wiki-root <path>] [--all-workspaces]

Behavior:
- If --workspace omitted: use the shared contextd resolver.
- If --wiki-root omitted: resolve canonical knowledge_root per agents/system-prompt.md rule:
    absolute -> use as-is
    relative -> resolve relative to project root
    null/empty -> fallback global contextd/legacy config
- --all-workspaces: iterate every directory under {wiki-root}/workspaces/*/.

Checks per workspace:
- workspace.md — exists; all md links resolve.
- patterns-index.md — all md links resolve.
- projects/*/knowledge-map.md — all md links resolve.
- Cross-check: every platform/patterns/*.md and platform/contracts/*.md
  is referenced by patterns-index.md (warn-only orphan).
- OKF v0.2 conformance (warn-only) on every concept .md file:
  frontmatter parseable, `type` present & non-empty, type in known set,
  `status` in {draft, stable, deprecated}, each `sources[]` entry has a
  `resource`, and every body footnote `[^id]` matches a `sources[].id`
  (an uncited id is valid). Index/config files (README.md, INDEX.md,
  _index.md, patterns-index.md, workspace.md, knowledge-map.md) are skipped.

Output:
- JSON to stdout: combined result (single workspace -> dict; multi -> list).
- Human summary to stderr.

Exit codes:
- 0: clean
- 1: broken_links present
- 2: only warnings (orphans and/or OKF findings)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from lib import contextd_resolver
from lib.stdio import configure_stdio

# Markdown inline link: [text](target)
# - Skips images (preceding '!') by using a negative lookbehind.
# - Captures link text (allowing nested brackets minimally) and target up to first ')' or whitespace.
# - Strips optional title: [text](target "title")
LINK_RE = re.compile(
    r"(?<!\!)\[([^\]\n]+)\]\(\s*([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)"
)

# --- OKF v0.2 (Open Knowledge Format) conformance -------------------------
# Spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
# All OKF findings are warnings (exit 2 class) — consistent with OKF's
# "consumers MUST tolerate unknown keys/types" stance.
OKF_KNOWN_TYPES = frozenset({
    "Contract", "Pattern", "Decision", "Evidence", "Runbook",
    "Report", "Tool", "Service", "Domain", "Reference", "Recipe",
    "Brief", "Requirement", "Design",
})
OKF_STATUSES = frozenset({"draft", "stable", "deprecated"})
# Filenames treated as index/config roles, not concept documents. OKF reserves
# index.md/log.md; this project also uses README.md / INDEX.md / _index.md /
# patterns-index.md as indexes, knowledge-map.md as context map, and
# workspace.md as config.
OKF_NON_CONCEPT_NAMES = frozenset({
    "README.md", "INDEX.md", "_index.md", "patterns-index.md",
    "workspace.md", "knowledge-map.md",
})
FOOTNOTE_RE = re.compile(r"\[\^([^\]]+)\]")


def parse_yaml_subset(text: str) -> dict:
    """Parse the YAML subset used in OKF frontmatter (stdlib only).

    Handles the constructs this project emits: `key: scalar`, flow
    collections `[a, b]` / `{k: v, k2: v2}`, and block lists of dicts
    (e.g. `sources:` with `- id: ...` + indented continuation lines).
    Anything beyond that is best-effort; unknown keys are preserved as
    scalars and never rejected.
    """
    data: dict = {}
    lines = text.split("\n")
    i, n = 0, len(lines)
    while i < n:
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        key, _, rest = stripped.partition(":")
        key = key.strip()
        if not rest.strip():
            value, i = _parse_block(lines, i + 1)
            data[key] = value
            continue
        data[key] = _parse_flow(rest)
        i += 1
    return data


def _parse_flow(value: str):
    """Parse an inline YAML scalar or flow collection."""
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [_scalar(x) for x in inner.split(",") if x.strip()] if inner else []
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        out: dict = {}
        if not inner:
            return out
        for pair in inner.split(","):
            k, _, v = pair.partition(":")
            out[k.strip()] = _scalar(v)
        return out
    return _scalar(value)


def _scalar(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("\"", "'"):
        return s[1:-1]
    # YAML inline comment: ` #` after the value (never strip quoted values)
    ci = s.find(" #")
    if ci != -1:
        s = s[:ci].strip()
    return s


def _parse_block(lines: list[str], i: int) -> tuple[Any, int]:
    """Parse an indented block under a key. Returns (value, next_i)."""
    n = len(lines)
    indent: int | None = None
    items: list = []
    is_list = False
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        cur_indent = len(line) - len(line.lstrip())
        if indent is None:
            indent = cur_indent
            is_list = line.strip().startswith("- ")
            if not is_list:
                return _parse_dict_block(lines, i, cur_indent)
        if cur_indent < indent:
            break
        s = line.strip()
        if not is_list or not s.startswith("- "):
            break
        item = s[2:].strip()
        if ":" in item:
            entry: dict = {}
            k, _, v = item.partition(":")
            entry[k.strip()] = _parse_flow(v)
            j = i + 1
            while j < n and lines[j].strip():
                if len(lines[j]) - len(lines[j].lstrip()) <= indent:
                    break
                sk = lines[j].strip()
                if sk.startswith("- "):
                    break
                skk, _, skv = sk.partition(":")
                entry[skk.strip()] = _parse_flow(skv)
                j += 1
            items.append(entry)
            i = j
        else:
            items.append(_scalar(item))
            i += 1
    return items, i


def _parse_dict_block(lines: list[str], i: int, indent: int) -> tuple[dict, int]:
    d: dict = {}
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if len(line) - len(line.lstrip()) < indent:
            break
        s = line.strip()
        if s.startswith("- "):
            break
        k, _, rest = s.partition(":")
        k = k.strip()
        if rest.strip():
            d[k] = _parse_flow(rest)
            i += 1
        else:
            value, i = _parse_block(lines, i + 1)
            d[k] = value
    return d, i


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """Split md text into (frontmatter_dict|None, body). None => no/closed-fence missing."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text  # opening fence without closing — not a valid frontmatter
    return parse_yaml_subset(text[4:end]), text[end + 4:]


def check_okf_file(file: Path, findings: list[dict]) -> None:
    """Append OKF conformance warnings for one concept file."""
    text = file.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        findings.append({
            "file": str(file),
            "kind": "okf_missing_frontmatter",
            "detail": "concept file has no YAML frontmatter (or unclosed fence)",
        })
        return
    ctype = fm.get("type")
    if not isinstance(ctype, str) or not ctype.strip():
        findings.append({
            "file": str(file),
            "kind": "okf_missing_type",
            "detail": "frontmatter has no non-empty `type`",
        })
    elif ctype not in OKF_KNOWN_TYPES:
        findings.append({
            "file": str(file),
            "kind": "okf_unknown_type",
            "detail": f"type {ctype!r} not in known set {sorted(OKF_KNOWN_TYPES)}",
        })
    status = fm.get("status")
    if isinstance(status, str) and status not in OKF_STATUSES:
        findings.append({
            "file": str(file),
            "kind": "okf_bad_status",
            "detail": f"status {status!r} not in {sorted(OKF_STATUSES)}",
        })
    sources = fm.get("sources")
    if isinstance(sources, list):
        # OKF v0.2: `resource` is required per source entry; `id` is optional
        # and only the join key for per-claim footnotes — an uncited id is valid.
        source_ids: set[str] = set()
        for src in sources:
            if not isinstance(src, dict):
                continue
            resource = src.get("resource")
            if not isinstance(resource, str) or not resource.strip():
                findings.append({
                    "file": str(file),
                    "kind": "okf_source_missing_resource",
                    "detail": "sources[] entry has no non-empty `resource`",
                })
            sid = src.get("id")
            if isinstance(sid, str):
                source_ids.add(sid)
        for fid in set(FOOTNOTE_RE.findall(body)):
            if fid not in source_ids:
                findings.append({
                    "file": str(file),
                    "kind": "okf_footnote_unresolved",
                    "detail": f"body footnote [^{fid}] has no matching sources[].id",
                })


def check_workspace_okf(ws_root: Path) -> list[dict]:
    """Run OKF conformance checks on every concept .md under the workspace."""
    findings: list[dict] = []
    for f in sorted(ws_root.rglob("*.md")):
        if f.name in OKF_NON_CONCEPT_NAMES:
            continue
        rel_parts = f.relative_to(ws_root).parts
        # Runtime artifact subtrees — not knowledge concepts:
        # evidence/ (raw.md, analysis, qa batches — generated + pipeline-validated)
        # .observations/ (cluster state)
        if "evidence" in rel_parts or ".observations" in rel_parts:
            continue
        check_okf_file(f, findings)
    return findings


def parse_links(md_text: str) -> list[tuple[str, str]]:
    """Return list of (link_text, raw_target) for inline markdown links."""
    out: list[tuple[str, str]] = []
    for m in LINK_RE.finditer(md_text):
        text = m.group(1).strip()
        target = m.group(2).strip()
        out.append((text, target))
    return out


def is_external(target: str) -> bool:
    """True if target is a URL, mailto, or anchor-only link we should skip."""
    if not target:
        return True
    if target.startswith("#"):
        return True
    parsed = urlparse(target)
    if parsed.scheme in ("http", "https", "mailto", "ftp", "ftps", "file", "data"):
        return True
    return False


def resolve_link_target(source_file: Path, target: str) -> Path:
    """Resolve a link target relative to source_file's directory.

    Drops fragment (#anchor) and query (?...). URL-decodes percent-encoded chars.
    """
    # Strip fragment / query
    raw = target
    for sep in ("#", "?"):
        i = raw.find(sep)
        if i != -1:
            raw = raw[:i]
    raw = unquote(raw)
    if not raw:
        # pure anchor — shouldn't reach here
        return source_file
    p = Path(raw)
    if p.is_absolute():
        return p
    return (source_file.parent / p).resolve()


def check_file_links(
    source_file: Path, broken: list[dict]
) -> None:
    """Parse source_file, append broken links to broken list."""
    try:
        text = source_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        broken.append({
            "source_file": str(source_file),
            "link_text": "<self>",
            "target": "<file missing>",
            "resolved_to": str(source_file),
        })
        return
    for text_label, target in parse_links(text):
        if is_external(target):
            continue
        resolved = resolve_link_target(source_file, target)
        # Allow link to a directory (e.g. [foo](platform/contracts/)) — accept if dir exists
        if not (resolved.is_file() or resolved.is_dir()):
            broken.append({
                "source_file": str(source_file),
                "link_text": text_label,
                "target": target,
                "resolved_to": str(resolved),
            })


def lint_workspace(ws_root: Path) -> dict:
    """Run all checks on a single workspace directory."""
    result: dict = {
        "workspace": ws_root.name,
        "broken_links": [],
        "orphans": [],
        "okf": [],
        "summary": {"broken": 0, "orphaned": 0, "okf": 0},
    }

    if not ws_root.is_dir():
        result["broken_links"].append({
            "source_file": str(ws_root),
            "link_text": "<workspace>",
            "target": "<missing>",
            "resolved_to": str(ws_root),
        })
        result["summary"]["broken"] = 1
        return result

    broken: list[dict] = result["broken_links"]

    # 1. workspace.md
    workspace_md = ws_root / "workspace.md"
    if not workspace_md.is_file():
        broken.append({
            "source_file": str(workspace_md),
            "link_text": "<workspace.md>",
            "target": "<missing>",
            "resolved_to": str(workspace_md),
        })
    else:
        check_file_links(workspace_md, broken)

    # 2. patterns-index.md
    patterns_index = ws_root / "patterns-index.md"
    patterns_index_text = ""
    if not patterns_index.is_file():
        broken.append({
            "source_file": str(patterns_index),
            "link_text": "<patterns-index.md>",
            "target": "<missing>",
            "resolved_to": str(patterns_index),
        })
    else:
        check_file_links(patterns_index, broken)
        patterns_index_text = patterns_index.read_text(encoding="utf-8")

    # 3. every projects/*/knowledge-map.md
    projects_dir = ws_root / "projects"
    if projects_dir.is_dir():
        for proj in sorted(projects_dir.iterdir()):
            if not proj.is_dir():
                continue
            km = proj / "knowledge-map.md"
            if km.is_file():
                check_file_links(km, broken)
            # else: not an error — project may not have one yet.

    # 4. orphan check — patterns and contracts not referenced in patterns-index
    orphans: list[dict] = result["orphans"]
    referenced_paths: set[Path] = set()
    if patterns_index_text:
        for _label, target in parse_links(patterns_index_text):
            if is_external(target):
                continue
            resolved = resolve_link_target(patterns_index, target)
            try:
                referenced_paths.add(resolved.resolve())
            except OSError:
                referenced_paths.add(resolved)

    for sub in ("platform/patterns", "platform/contracts"):
        d = ws_root / sub
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            try:
                fr = f.resolve()
            except OSError:
                fr = f
            if fr not in referenced_paths:
                orphans.append({
                    "file": str(f),
                    "reason": f"not referenced by patterns-index.md ({sub})",
                })

    # 5. OKF v0.2 conformance (warn-only) — every concept file
    okf_findings: list[dict] = result["okf"]
    okf_findings.extend(check_workspace_okf(ws_root))

    result["summary"]["broken"] = len(broken)
    result["summary"]["orphaned"] = len(orphans)
    result["summary"]["okf"] = len(okf_findings)
    return result


def print_human_summary(res: dict, stream) -> None:
    ws = res["workspace"]
    b = res["summary"]["broken"]
    o = res["summary"]["orphaned"]
    k = res["summary"]["okf"]
    print(f"[workspace: {ws}] broken={b} orphaned={o} okf={k}", file=stream)
    for item in res["broken_links"]:
        print(
            f"  BROKEN  {item['source_file']}  ->  {item['target']}  "
            f"(resolved: {item['resolved_to']})",
            file=stream,
        )
    for item in res["orphans"]:
        print(f"  ORPHAN  {item['file']}  ({item['reason']})", file=stream)
    for item in res["okf"]:
        print(f"  OKF-WARN  {item['file']}  ({item['kind']}: {item['detail']})",
              file=stream)


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    ap = argparse.ArgumentParser(description="Lint wiki workspaces for broken links and orphans.")
    ap.add_argument("--workspace", help="Workspace name (under {wiki-root}/workspaces/)")
    ap.add_argument("--wiki-root", help="Override wiki root directory")
    ap.add_argument("--all-workspaces", action="store_true",
                    help="Lint every workspace under {wiki-root}/workspaces/")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 2 on OKF warnings (default: warnings don't affect exit code)")
    args = ap.parse_args(argv)

    # Resolve project config (only needed if wiki-root or workspace not provided).
    resolved: dict = {}
    if args.wiki_root is None or (args.workspace is None and not args.all_workspaces):
        resolved = contextd_resolver.resolve(Path.cwd())

    # Resolve knowledge_root.
    if args.wiki_root:
        p = Path(args.wiki_root)
        wiki_root = p.resolve() if p.is_absolute() else p.resolve()
    else:
        root = resolved.get("knowledge_root") or resolved.get("wiki_root")
        if not root:
            print("ERROR: no .contextd/config.json or legacy config found by walking up from cwd; "
                  "pass --wiki-root explicitly.", file=sys.stderr)
            return 3
        wiki_root = Path(str(root)).resolve()

    workspaces_dir = wiki_root / "workspaces"
    if not workspaces_dir.is_dir():
        print(f"ERROR: {workspaces_dir} does not exist", file=sys.stderr)
        return 3

    targets: list[Path] = []
    if args.all_workspaces:
        targets = sorted([d for d in workspaces_dir.iterdir() if d.is_dir()])
    else:
        ws_name = args.workspace or resolved.get("workspace")
        if not ws_name:
            print("ERROR: workspace not specified and not found in contextd config",
                  file=sys.stderr)
            return 3
        targets = [workspaces_dir / ws_name]

    results = [lint_workspace(t) for t in targets]

    # JSON output
    payload: Any = results[0] if (len(results) == 1 and not args.all_workspaces) else results
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

    # Human summary
    total_broken = 0
    total_orphan = 0
    total_okf = 0
    for r in results:
        print_human_summary(r, sys.stderr)
        total_broken += r["summary"]["broken"]
        total_orphan += r["summary"]["orphaned"]
        total_okf += r["summary"]["okf"]
    print(f"TOTAL: broken={total_broken} orphaned={total_orphan} okf={total_okf}",
          file=sys.stderr)

    if total_broken > 0:
        return 1
    if total_orphan > 0:
        return 2
    if total_okf > 0 and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
