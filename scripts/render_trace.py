#!/usr/bin/env python3
"""
render_trace.py — render contextd pipeline trace JSON as HTML.

Reads `.contextd/runs/{run_id}/*.json` (schema: templates/run-trace.schema.json)
and emits an HTML viewer for human inspection. Legacy `.claude/runs/` is used
as a read-only fallback for old traces. Stdlib only, no Python deps.

Modes:
  --run <id>       Render that run -> {run_dir}/trace.html
  --last           Render the latest run -> {run_dir}/trace.html
  --all            Render index of all runs -> .contextd/runs/index.html
  --watch          Poll the latest (or --run) run and re-render on change
  --out <path>     Override output path
  --project-dir    Override project_dir resolution (default: walk up from CWD)

Design doc: agents/pipeline/PIPELINE-VISUAL.md, agents/pipeline/observability.md.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import contextd_resolver  # noqa: E402

STAGE_FILES = [
    "run.json",
    "01-planner.json",
    "02-context.json",
    "04-builder.json",
    "05-review.json",
]
STAGE_KEYS = [s.replace(".json", "") for s in STAGE_FILES]
PIPELINE_STAGES = STAGE_KEYS[1:]  # skip "run"

WATCH_INTERVAL_SEC = 0.5
WATCH_TIMEOUT_SEC = 600  # 10 minutes

# ---------- discovery ----------


def find_project_dir(start: Path) -> Path | None:
    selected, _ = contextd_resolver.find_config(start)
    if selected is None or "global" in selected.kind:
        return None
    return selected.project_dir


def load_workspace_active(project_dir: Path) -> str | None:
    resolved = contextd_resolver.resolve(project_dir)
    workspace = resolved.get("workspace")
    return str(workspace) if workspace else None


def list_runs(runs_dir: Path) -> list[Path]:
    if not runs_dir.exists():
        return []
    return sorted(
        (p for p in runs_dir.iterdir() if p.is_dir()),
        key=lambda p: p.name,
    )


def select_runs_dir(project_dir: Path) -> Path:
    """Prefer canonical traces, fallback to legacy traces when no canonical run exists."""
    canonical = project_dir / ".contextd" / "runs"
    legacy = project_dir / ".claude" / "runs"
    if list_runs(canonical) or not list_runs(legacy):
        return canonical
    return legacy


def resolve_run(runs_dir: Path, run_id_or_prefix: str | None, use_last: bool) -> Path | None:
    runs = list_runs(runs_dir)
    if not runs:
        return None
    if use_last:
        return runs[-1]
    if not run_id_or_prefix:
        return None
    matches = [p for p in runs if p.name.startswith(run_id_or_prefix)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        sys.stderr.write(
            f"[render_trace] prefix '{run_id_or_prefix}' matched {len(matches)} runs:\n"
        )
        for p in matches:
            sys.stderr.write(f"  - {p.name}\n")
        return None
    return None


def load_run(run_dir: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "parse_errors": [],
    }
    for fn in STAGE_FILES:
        f = run_dir / fn
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            out[fn.replace(".json", "")] = data
        except (OSError, json.JSONDecodeError) as e:
            out["parse_errors"].append({"file": fn, "error": str(e)})
    out["mtimes"] = {
        fn: (run_dir / fn).stat().st_mtime if (run_dir / fn).exists() else 0
        for fn in STAGE_FILES
    }
    return out


# ---------- HTML helpers ----------


def esc(s: Any) -> str:
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def badge(text: str, kind: str) -> str:
    return f'<span class="badge badge-{esc(kind)}">{esc(text)}</span>'


def verdict_badge(verdict: str | None) -> str:
    if not verdict:
        return badge("(in progress)", "neutral")
    kind = {
        "APPROVED": "ok",
        "BLOCK": "block",
        "BLOCKED": "block",
        "VIOLATIONS": "warn",
        "INSUFFICIENT_CONTEXT": "warn",
        "INCOMPLETE": "neutral",
    }.get(verdict, "neutral")
    return badge(verdict, kind)


def fmt_ts(ts: str | None) -> str:
    if not ts:
        return "—"
    return ts


# ---------- Mermaid generator ----------


def mermaid_for_run(run: dict[str, Any]) -> str:
    """Generate sequenceDiagram for THIS run, greying missing stages."""
    stages_completed = set(run.get("run", {}).get("stages_completed", []))
    # Detect from individual stage files too
    for s in PIPELINE_STAGES:
        if s in run:
            stages_completed.add(s)

    def state(s: str) -> str:
        return "✓" if s in stages_completed else "·"

    lines = [
        "sequenceDiagram",
        "    autonumber",
        "    actor U as User",
        "    participant M as Main Agent",
        "    participant P as contextd-planner",
        "    participant CS as contextd-context-selector",
        "    participant R as contextd-reviewer",
        f"    U->>M: {state('01-planner')} task",
        f"    M->>P: {state('01-planner')} parse intent",
        f"    P-->>M: 01-planner.json",
        f"    M->>CS: {state('02-context')} retrieve + verify plan",
        f"    CS-->>M: 02-context.json (verdict) + current-task.md",
    ]
    ctx = run.get("02-context", {})
    if ctx.get("verdict") == "BLOCK":
        lines.append(f"    M-->>U: STOP — plan BLOCKED")
    else:
        lines += [
            f"    M->>M: {state('04-builder')} write code",
            f"    M->>R: {state('05-review')} review code",
            f"    R-->>M: 05-review.json",
        ]
    return "\n".join(lines)


# ---------- per-run HTML ----------


def render_stage_card(run: dict[str, Any], stage: str) -> str:
    data = run.get(stage)
    if not data:
        return f"""
<details class="card card-missing">
  <summary><span class="card-title">{esc(stage)}</span> {badge('(missing or skipped)', 'neutral')}</summary>
  <p class="card-empty">File <code>{esc(stage)}.json</code> chưa được sinh.</p>
</details>"""

    flags: list[str] = []
    body_html = ""

    if stage == "01-planner":
        unverified = data.get("unverified_count", 0)
        if unverified > 0:
            flags.append("danger")
        intent = data.get("intent") or {}
        body_html = f"""
<dl class="kv">
  <dt>type</dt><dd>{esc(intent.get('type'))}</dd>
  <dt>workspace</dt><dd>{esc(intent.get('workspace'))}</dd>
  <dt>domain</dt><dd>{esc(intent.get('domain'))}</dd>
  <dt>scope</dt><dd>{esc(intent.get('scope'))}</dd>
  <dt>components</dt><dd>{esc(', '.join(intent.get('components') or []))}</dd>
  <dt>patterns_needed</dt><dd>{esc(', '.join(intent.get('patterns_needed') or []))}</dd>
  <dt>contracts_touched</dt><dd>{esc(', '.join(intent.get('contracts_touched') or []))}</dd>
  <dt>unverified_count</dt><dd>{esc(unverified)} {'⚠️' if unverified > 0 else ''}</dd>
</dl>
{render_verify_table('Patterns', data.get('patterns_verified') or [])}
{render_verify_table('Contracts', data.get('contracts_verified') or [])}
"""

    elif stage == "02-context":
        gaps = data.get("gaps") or []
        verdict = data.get("verdict")
        if verdict == "BLOCK" or any(g.get("blocking_hint") for g in gaps):
            flags.append("danger")
        elif gaps or (data.get("issues") and any(i.get("severity") == "warning" for i in data.get("issues", []))):
            flags.append("warn")
        issues = data.get("issues") or []
        body_html = f"""
<p>Verdict: {verdict_badge(verdict)}</p>
<dl class="kv">
  <dt>context_file</dt><dd><code>{esc(data.get('context_file'))}</code></dd>
  <dt>file_count</dt><dd>{esc(data.get('file_count'))}</dd>
  <dt>gap_count</dt><dd>{esc(data.get('gap_count'))}</dd>
  <dt>total_chars</dt><dd>{esc(data.get('total_chars'))}</dd>
</dl>
<h4>Referenced docs</h4>
{render_docs_table(data.get('referenced_docs') or [])}
<h4>Knowledge gaps</h4>
{render_gaps_table(gaps)}
{render_issues_table(issues) if issues else ''}
{render_checks_summary(data.get('checks_summary') or {})}
"""

    elif stage == "04-builder":
        a_count = data.get("assumptions_count", 0)
        if a_count > 0:
            flags.append("warn")
        if data.get("self_check_passed") is False:
            flags.append("danger")
        body_html = f"""
<dl class="kv">
  <dt>self_check_passed</dt><dd>{esc(data.get('self_check_passed'))}</dd>
  <dt>assumptions_count</dt><dd>{esc(a_count)} {'⚠️' if a_count > 0 else ''}</dd>
  <dt>files_modified</dt><dd>{esc(len(data.get('files_modified') or []))}</dd>
</dl>
<h4>Files modified</h4>
<ul class="files">{''.join(f'<li><code>{esc(f)}</code></li>' for f in (data.get('files_modified') or [])) or '<li>(none)</li>'}</ul>
<h4>Used docs</h4>
{render_docs_table(data.get('used_docs') or [], used=True)}
"""

    elif stage == "05-review":
        v_count = data.get("violation_count", 0)
        h_count = data.get("hallucination_count", 0)
        if v_count > 0 or h_count > 0:
            flags.append("danger")
        body_html = f"""
<p>Verdict: {verdict_badge(data.get('verdict'))}</p>
<dl class="kv">
  <dt>violation_count</dt><dd>{esc(v_count)} {'⚠️' if v_count > 0 else ''}</dd>
  <dt>hallucination_count</dt><dd>{esc(h_count)} {'⚠️' if h_count > 0 else ''}</dd>
  <dt>files_reviewed</dt><dd>{esc(len(data.get('files_reviewed') or []))}</dd>
</dl>
<h4>Violations</h4>
{render_violations_table(data.get('violations') or [])}
<h4>Hallucinated refs</h4>
{render_halluc_table(data.get('hallucinated_refs') or [])}
"""

    flag_class = " ".join(f"flag-{f}" for f in flags)
    duration = data.get("duration_ms")
    duration_html = f' <span class="muted">⌛ {esc(duration)}ms</span>' if duration else ""
    return f"""
<details class="card {flag_class}" open>
  <summary>
    <span class="card-title">{esc(stage)}</span>
    <span class="muted">⏱ {esc(data.get('ts') or '—')}</span>{duration_html}
  </summary>
  {body_html}
</details>"""


def render_verify_table(title: str, items: list[dict]) -> str:
    if not items:
        return ""
    rows = "".join(
        f"<tr class=\"{'row-bad' if not it.get('exists') else ''}\">"
        f"<td><code>{esc(it.get('name'))}</code></td>"
        f"<td>{'✓' if it.get('exists') else '✗'}</td>"
        f"<td><code>{esc(it.get('path') or '—')}</code></td></tr>"
        for it in items
    )
    return f"""
<h4>{esc(title)} verification</h4>
<table class="t"><thead><tr><th>Name</th><th>Exists</th><th>Path</th></tr></thead><tbody>{rows}</tbody></table>"""


def render_docs_table(items: list[dict], used: bool = False) -> str:
    if not items:
        return '<p class="muted">(none)</p>'
    rows = "".join(
        f"<tr><td>{esc(it.get('category', '—'))}</td>"
        f"<td><code>{esc(it.get('path'))}</code></td>"
        f"<td>{esc(it.get('section') if used else ', '.join(it.get('sections') or []) or '—')}</td></tr>"
        for it in items
    )
    return f'<table class="t"><thead><tr><th>Category</th><th>Path</th><th>Section{"s" if not used else ""}</th></tr></thead><tbody>{rows}</tbody></table>'


def render_gaps_table(items: list[dict]) -> str:
    if not items:
        return '<p class="muted">(none)</p>'
    rows = "".join(
        f'<tr class="{"row-bad" if it.get("blocking_hint") else "row-warn"}">'
        f"<td>{esc(it.get('category'))}</td>"
        f"<td><code>{esc(it.get('missing'))}</code></td>"
        f"<td>{'blocking' if it.get('blocking_hint') else 'warn'}</td></tr>"
        for it in items
    )
    return f'<table class="t"><thead><tr><th>Category</th><th>Missing</th><th>Severity</th></tr></thead><tbody>{rows}</tbody></table>'


def render_issues_table(items: list[dict]) -> str:
    if not items:
        return '<p class="muted">(no issues)</p>'
    rows = "".join(
        f'<tr class="{"row-bad" if it.get("severity") == "blocking" else "row-warn"}">'
        f"<td>{esc(it.get('id'))}</td>"
        f"<td>{esc(it.get('category'))}</td>"
        f"<td>{esc(it.get('severity'))}</td>"
        f"<td>{esc(it.get('detail'))}</td>"
        f"<td><code>{esc(it.get('evidence') or '—')}</code></td></tr>"
        for it in items
    )
    return f'<h4>Issues</h4><table class="t"><thead><tr><th>ID</th><th>Category</th><th>Sev</th><th>Detail</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table>'


def render_checks_summary(cs: dict) -> str:
    if not cs:
        return ""
    return f"""
<h4>Checks summary</h4>
<dl class="kv">
  <dt>patterns_verified</dt><dd>{esc(cs.get('patterns_verified'))}</dd>
  <dt>contracts_verified</dt><dd>{esc(cs.get('contracts_verified'))}</dd>
  <dt>components_covered</dt><dd>{esc(', '.join(cs.get('components_covered') or []))}</dd>
  <dt>blocking_gaps</dt><dd>{esc(cs.get('blocking_gaps'))}</dd>
  <dt>conflicts</dt><dd>{esc(cs.get('conflicts'))}</dd>
</dl>"""


def render_violations_table(items: list[dict]) -> str:
    if not items:
        return '<p class="muted">(none)</p>'
    rows = "".join(
        f'<tr class="{"row-bad" if it.get("severity") == "blocking" else "row-warn"}">'
        f"<td>{esc(it.get('id'))}</td>"
        f"<td><code>{esc(it.get('rule'))}</code></td>"
        f"<td><code>{esc(it.get('file_line'))}</code></td>"
        f"<td>{esc(it.get('severity'))}</td>"
        f"<td>{esc(it.get('fix') or '—')}</td></tr>"
        for it in items
    )
    return f'<table class="t"><thead><tr><th>ID</th><th>Rule</th><th>File:Line</th><th>Sev</th><th>Fix</th></tr></thead><tbody>{rows}</tbody></table>'


def render_halluc_table(items: list[dict]) -> str:
    if not items:
        return '<p class="muted">(none)</p>'
    rows = "".join(
        f'<tr class="row-bad">'
        f"<td><code>{esc(it.get('ref'))}</code></td>"
        f"<td>{esc(it.get('found_in'))}</td>"
        f"<td>{esc(it.get('reason') or '—')}</td></tr>"
        for it in items
    )
    return f'<table class="t"><thead><tr><th>Ref</th><th>Found in</th><th>Reason</th></tr></thead><tbody>{rows}</tbody></table>'


def render_diff_panel(run: dict) -> str:
    """Side-by-side: retrieved (Stage 2) vs used (Stage 4)."""
    ctx = run.get("02-context") or {}
    bld = run.get("04-builder") or {}
    retrieved = {d.get("path"): d for d in (ctx.get("referenced_docs") or [])}
    used = {d.get("path"): d for d in (bld.get("used_docs") or [])}

    if not retrieved and not used:
        return ""

    all_paths = sorted(set(retrieved) | set(used))
    rows = []
    counts = {"both": 0, "retrieved_unused": 0, "used_not_retrieved": 0}
    for p in all_paths:
        in_r = p in retrieved
        in_u = p in used
        if in_r and in_u:
            cls, label = "row-ok", "✓ both"
            counts["both"] += 1
        elif in_r:
            cls, label = "row-warn", "retrieved, unused"
            counts["retrieved_unused"] += 1
        else:
            cls, label = "row-bad", "used, NOT retrieved (hallucination?)"
            counts["used_not_retrieved"] += 1
        cat = (retrieved.get(p) or used.get(p) or {}).get("category", "—")
        rows.append(
            f'<tr class="{cls}"><td>{esc(cat)}</td><td><code>{esc(p)}</code></td><td>{esc(label)}</td></tr>'
        )

    summary = (
        f"both: <b>{counts['both']}</b> · "
        f"retrieved-unused: <b class=\"warn\">{counts['retrieved_unused']}</b> · "
        f"used-not-retrieved: <b class=\"danger\">{counts['used_not_retrieved']}</b>"
    )

    return f"""
<details class="card" open>
  <summary><span class="card-title">Retrieved vs Used (context utilization)</span></summary>
  <p class="muted">{summary}</p>
  <table class="t">
    <thead><tr><th>Category</th><th>Path</th><th>Status</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</details>"""


def render_divergence(run: dict) -> str:
    """Auto-heuristic divergence detection — copies contextd-trace.md heuristic."""
    notes = []
    planner = run.get("01-planner") or {}
    ctx = run.get("02-context") or {}
    builder = run.get("04-builder") or {}
    review = run.get("05-review") or {}

    # 1. Planner proposed pattern not retrieved
    proposed = set((planner.get("intent") or {}).get("patterns_needed") or [])
    retrieved_paths = set(d.get("path", "") for d in (ctx.get("referenced_docs") or []))
    retrieved_names = {p.rsplit("/", 1)[-1].replace(".md", "") for p in retrieved_paths}
    missing_in_ctx = proposed - retrieved_names
    if missing_in_ctx:
        notes.append(
            f"Planner đề xuất pattern <code>{esc(', '.join(sorted(missing_in_ctx)))}</code> nhưng không thấy trong "
            f"<code>02-context.referenced_docs</code> — kiểm <code>task-to-docs-map.md</code> mapping."
        )

    # 2. Context-selector APPROVED but final reviewer found violations
    if ctx.get("verdict") == "APPROVED" and review.get("verdict") == "VIOLATIONS":
        notes.append(
            "Context-selector APPROVED nhưng final reviewer thấy <b>VIOLATIONS</b> — "
            "kiểm <code>04-builder.used_docs</code> xem builder có ignore Referenced Docs không."
        )

    # 3. Builder reference path not in retrieved
    used_paths = set(d.get("path", "") for d in (builder.get("used_docs") or []))
    halluc_paths = used_paths - retrieved_paths
    if halluc_paths:
        notes.append(
            f"Builder reference <code>{esc(', '.join(sorted(halluc_paths)))}</code> không có trong "
            f"<code>02-context.referenced_docs</code> — hallucination, có thể wiki thiếu hoặc agent tự nghĩ."
        )

    # 4. High retrieved but low used
    if ctx.get("file_count", 0) > 0 and len(used_paths) > 0:
        ratio = len(used_paths) / ctx.get("file_count", 1)
        if ratio < 0.4:
            notes.append(
                f"Context utilization thấp ({ratio:.0%}): builder dùng {len(used_paths)}/{ctx.get('file_count')} docs. "
                "Có thể context-filter retrieve quá nhiều file thừa."
            )

    if not notes:
        return ""
    items = "".join(f"<li>{n}</li>" for n in notes)
    return f"""
<details class="card flag-warn" open>
  <summary><span class="card-title">Divergence analysis (heuristic)</span></summary>
  <ul>{items}</ul>
</details>"""


def render_workspace_warning(run: dict, workspace_active: str | None) -> str:
    rj = run.get("run") or {}
    war = rj.get("workspace_at_run")
    if war and workspace_active and war != workspace_active:
        return f"""
<div class="banner banner-warn">
  ⚠️ Workspace mismatch: trace ghi nhận <code>{esc(war)}</code> nhưng workspace active hiện là <code>{esc(workspace_active)}</code>.
</div>"""
    return ""


def render_parse_errors(run: dict) -> str:
    errs = run.get("parse_errors") or []
    if not errs:
        return ""
    rows = "".join(
        f"<tr><td><code>{esc(e['file'])}</code></td><td>{esc(e['error'])}</td></tr>"
        for e in errs
    )
    return f"""
<details class="card flag-warn">
  <summary><span class="card-title">Parse errors</span></summary>
  <table class="t"><thead><tr><th>File</th><th>Error</th></tr></thead><tbody>{rows}</tbody></table>
</details>"""


def render_per_run_html(run: dict, workspace_active: str | None, watch: bool = False) -> str:
    rj = run.get("run") or {}
    final_verdict = rj.get("final_verdict")
    refresh_meta = '<meta http-equiv="refresh" content="2">' if watch else ""

    user_task = rj.get("user_task", "")
    if not user_task:
        # Try planner intent.scope/approach
        intent = (run.get("01-planner") or {}).get("intent") or {}
        user_task = intent.get("approach") or "(unknown)"

    cards = "".join(render_stage_card(run, s) for s in PIPELINE_STAGES)
    diff = render_diff_panel(run)
    divergence = render_divergence(run)
    parse_errs = render_parse_errors(run)
    ws_warn = render_workspace_warning(run, workspace_active)

    mermaid_src = mermaid_for_run(run)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
{refresh_meta}
<title>contextd Trace — {esc(run['run_id'])}</title>
<style>{CSS}</style>
</head>
<body>
<header class="page-header">
  <h1>contextd Trace <small>{esc(run['run_id'])}</small></h1>
  <p>
    Workspace: <code>{esc(rj.get('workspace_at_run') or '—')}</code> ·
    Started: {esc(fmt_ts(rj.get('ts_start')))} ·
    Ended: {esc(fmt_ts(rj.get('ts_end')))} ·
    Stages: {esc(len(rj.get('stages_completed') or []))}/4 ·
    Final: {verdict_badge(final_verdict)}
    {' · <span class="badge badge-warn">LIVE — auto-refresh 2s</span>' if watch else ''}
  </p>
  <p class="task"><b>Task:</b> {esc(user_task)}</p>
</header>
{ws_warn}

<section class="diagram">
  <h2>Pipeline flow</h2>
  <div class="mermaid" data-raw="{esc(mermaid_src)}">{esc(mermaid_src)}</div>
</section>

<section>
  <h2>Stages</h2>
  {cards}
</section>

<section>
  <h2>Cross-stage analysis</h2>
  {diff}
  {divergence}
  {parse_errs}
</section>

<footer class="page-footer">
  <p>Generated {esc(datetime.now(timezone.utc).isoformat(timespec='seconds'))} ·
  Source: <code>{esc(run['run_dir'])}</code> ·
  Schema: <code>templates/run-trace.schema.json</code></p>
</footer>

<script type="module">
{MERMAID_LOADER}
</script>
</body>
</html>"""


# ---------- index HTML ----------


def render_index_html(runs_data: list[dict], workspace_active: str | None, runs_dir: Path) -> str:
    rows = []
    for r in runs_data:
        rj = r.get("run") or {}
        review = r.get("05-review") or {}
        ctx_idx = r.get("02-context") or {}
        planner = r.get("01-planner") or {}

        war = rj.get("workspace_at_run") or "—"
        is_other_ws = workspace_active and war != workspace_active

        verdict = rj.get("final_verdict") or (
            "BLOCKED" if ctx_idx.get("verdict") == "BLOCK" else "INCOMPLETE"
        )
        halluc = (planner.get("unverified_count", 0) or 0) + (review.get("hallucination_count", 0) or 0)
        viol = review.get("violation_count", 0) or 0
        task = (rj.get("user_task") or "")[:80]
        date = (rj.get("ts_start") or "")[:10]
        stages_n = len(rj.get("stages_completed") or [])

        # link relative from index.html (in runs_dir) to run/trace.html
        link = f"./{r['run_id']}/trace.html"

        cls = "row-other-ws" if is_other_ws else ""
        rows.append(f"""
<tr class="{cls}" data-workspace="{esc(war)}" data-verdict="{esc(verdict)}" data-halluc="{halluc}" data-viol="{viol}" data-date="{esc(date)}">
  <td><code>{esc(r['run_id'])}</code></td>
  <td>{esc(date)}</td>
  <td><code>{esc(war)}</code></td>
  <td>{esc(task)}</td>
  <td>{stages_n}/4</td>
  <td>{verdict_badge(verdict)}</td>
  <td class="{'danger' if halluc > 0 else ''}">{halluc}</td>
  <td class="{'danger' if viol > 0 else ''}">{viol}</td>
  <td><a href="{esc(link)}">open →</a></td>
</tr>""")

    workspaces = sorted({(r.get("run") or {}).get("workspace_at_run") for r in runs_data} - {None})
    ws_options = "".join(f'<option value="{esc(w)}">{esc(w)}</option>' for w in workspaces)

    total = len(runs_data)
    in_active_ws = sum(
        1 for r in runs_data
        if (r.get("run") or {}).get("workspace_at_run") == workspace_active
    )

    if not rows:
        body_main = '<p class="muted empty">Chưa có run nào. Chạy <code>/use-contextd "..."</code> để có run đầu tiên.</p>'
    else:
        body_main = f"""
<div class="filters">
  <label>Workspace
    <select id="f-ws"><option value="">all</option>{ws_options}</select>
  </label>
  <label>Verdict
    <select id="f-verdict">
      <option value="">all</option>
      <option>APPROVED</option>
      <option>VIOLATIONS</option>
      <option>BLOCKED</option>
      <option>INCOMPLETE</option>
    </select>
  </label>
  <label><input type="checkbox" id="f-halluc"> Has hallucination</label>
  <label><input type="checkbox" id="f-viol"> Has violation</label>
  <label>Since (YYYY-MM-DD)
    <input type="text" id="f-since" placeholder="2026-01-01">
  </label>
  <span class="muted" id="visible-count"></span>
</div>
<table class="t" id="runs-table">
  <thead><tr>
    <th>Run ID</th><th>Date</th><th>Workspace</th><th>Task</th><th>Stages</th>
    <th>Verdict</th><th>Halluc</th><th>Viol</th><th></th>
  </tr></thead>
  <tbody>{''.join(rows)}</tbody>
</table>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>contextd Runs — index</title>
<style>{CSS}</style>
</head>
<body>
<header class="page-header">
  <h1>contextd Runs</h1>
  <p>
    Total: <b>{total}</b> ·
    Active workspace: <code>{esc(workspace_active or '—')}</code>
    ({in_active_ws} run trong workspace này) ·
    Source: <code>{esc(str(runs_dir))}</code>
  </p>
</header>

{body_main}

<footer class="page-footer">
  <p>Generated {esc(datetime.now(timezone.utc).isoformat(timespec='seconds'))} ·
  Runs ngoài workspace active được mờ đi. Mỗi row click <code>open</code> mở <code>trace.html</code> của run đó.</p>
</footer>

<script>{INDEX_JS}</script>
</body>
</html>"""


# ---------- assets ----------


CSS = """
* { box-sizing: border-box; }
body { font: 14px/1.5 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 24px; max-width: 1200px; margin: 0 auto; color: #222; background: #fafafa; }
h1 { font-size: 22px; margin: 0 0 4px; }
h1 small { font-size: 12px; color: #888; font-weight: normal; font-family: monospace; }
h2 { font-size: 16px; margin: 24px 0 12px; padding-bottom: 4px; border-bottom: 1px solid #ddd; }
h4 { font-size: 13px; margin: 12px 0 6px; color: #444; }
code { font-family: 'SF Mono', Consolas, monospace; font-size: 12px; background: #f0f0f0; padding: 1px 4px; border-radius: 3px; }
.page-header { background: white; padding: 16px; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 16px; }
.page-header p { margin: 4px 0; color: #555; }
.task { padding: 8px; background: #f5f5f5; border-left: 3px solid #888; margin-top: 8px !important; }
.page-footer { margin-top: 32px; padding-top: 12px; border-top: 1px solid #ddd; color: #888; font-size: 12px; }
.muted { color: #888; }
.empty { padding: 32px; text-align: center; }
.danger { color: #c00; }
.warn { color: #c80; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
.badge-ok { background: #d4edda; color: #155724; }
.badge-block, .badge-warn { background: #fff3cd; color: #856404; }
.badge-block { background: #f8d7da; color: #721c24; }
.badge-neutral { background: #e9ecef; color: #495057; }
.banner { padding: 8px 12px; border-radius: 4px; margin: 12px 0; }
.banner-warn { background: #fff3cd; border: 1px solid #ffeeba; color: #856404; }
.card { background: white; border: 1px solid #ddd; border-radius: 6px; margin: 8px 0; padding: 0; }
.card > summary { padding: 10px 14px; cursor: pointer; font-weight: bold; user-select: none; list-style: none; }
.card > summary::-webkit-details-marker { display: none; }
.card > summary::before { content: "▶ "; font-size: 10px; color: #888; }
.card[open] > summary::before { content: "▼ "; }
.card .card-title { font-family: monospace; font-size: 13px; }
.card > * { padding: 0 14px; }
.card > summary { padding: 10px 14px; }
.card > *:last-child { padding-bottom: 12px; }
.card.flag-danger { border-left: 4px solid #c00; }
.card.flag-warn { border-left: 4px solid #c80; }
.card.card-missing { opacity: 0.5; }
.card-empty { color: #888; font-style: italic; }
.kv { display: grid; grid-template-columns: max-content 1fr; gap: 4px 12px; font-size: 13px; }
.kv dt { color: #666; font-weight: 600; }
.kv dd { margin: 0; }
.t { width: 100%; border-collapse: collapse; font-size: 12px; margin: 4px 0; }
.t th, .t td { padding: 6px 8px; text-align: left; border-bottom: 1px solid #eee; vertical-align: top; }
.t th { background: #f5f5f5; font-weight: 600; }
.t .row-bad { background: #fdf3f3; }
.t .row-warn { background: #fffaf0; }
.t .row-ok { background: #f3faf3; }
.files { margin: 4px 0; padding-left: 20px; }
.files li { font-size: 12px; }
.diagram { background: white; padding: 16px; border: 1px solid #ddd; border-radius: 6px; }
.mermaid { text-align: center; min-height: 80px; }
.filters { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; padding: 12px; background: white; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 8px; font-size: 13px; }
.filters select, .filters input[type=text] { font: inherit; padding: 3px 6px; }
.row-other-ws { opacity: 0.4; }
.row-other-ws:hover { opacity: 0.8; }
"""

MERMAID_LOADER = """
(async () => {
  const els = document.querySelectorAll('.mermaid');
  if (!els.length) return;
  try {
    const m = (await import('https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs')).default;
    m.initialize({ startOnLoad: true, theme: 'default', securityLevel: 'loose' });
    await m.run();
  } catch (e) {
    els.forEach(el => {
      const raw = el.dataset.raw || el.textContent;
      el.innerHTML = '<details><summary style="color:#888;cursor:pointer">[Mermaid offline — view raw]</summary><pre style="text-align:left;background:#f5f5f5;padding:8px">' + raw.replace(/</g,'&lt;') + '</pre></details>';
    });
  }
})();
"""

INDEX_JS = """
(function() {
  const tbody = document.querySelector('#runs-table tbody');
  if (!tbody) return;
  const rows = Array.from(tbody.rows);
  const ws = document.getElementById('f-ws');
  const v = document.getElementById('f-verdict');
  const halluc = document.getElementById('f-halluc');
  const viol = document.getElementById('f-viol');
  const since = document.getElementById('f-since');
  const counter = document.getElementById('visible-count');

  function apply() {
    let n = 0;
    rows.forEach(r => {
      let show = true;
      if (ws.value && r.dataset.workspace !== ws.value) show = false;
      if (v.value && r.dataset.verdict !== v.value) show = false;
      if (halluc.checked && parseInt(r.dataset.halluc) <= 0) show = false;
      if (viol.checked && parseInt(r.dataset.viol) <= 0) show = false;
      if (since.value && r.dataset.date < since.value) show = false;
      r.style.display = show ? '' : 'none';
      if (show) n++;
    });
    counter.textContent = n + ' / ' + rows.length + ' shown';
  }
  [ws, v, halluc, viol].forEach(el => el.addEventListener('change', apply));
  since.addEventListener('input', apply);
  apply();
})();
"""

# ---------- commands ----------


def cmd_render_run(project_dir: Path, run_id: str | None, use_last: bool, out: Path | None, watch: bool) -> int:
    runs_dir = select_runs_dir(project_dir)
    run_dir = resolve_run(runs_dir, run_id, use_last)
    if not run_dir:
        sys.stderr.write(f"[render_trace] no run found in {runs_dir}\n")
        runs = list_runs(runs_dir)
        if runs:
            sys.stderr.write("Available runs:\n")
            for p in runs[-10:]:
                sys.stderr.write(f"  - {p.name}\n")
        return 1

    workspace_active = load_workspace_active(project_dir)
    out_path = out or (run_dir / "trace.html")

    if watch:
        return watch_loop(run_dir, workspace_active, out_path)

    run = load_run(run_dir)
    html_str = render_per_run_html(run, workspace_active)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_str, encoding="utf-8")
    print(f"[OK] rendered: {out_path}")
    return 0


def cmd_render_index(project_dir: Path, out: Path | None) -> int:
    runs_dir = select_runs_dir(project_dir)
    runs = list_runs(runs_dir)
    runs_data = [load_run(p) for p in runs]
    workspace_active = load_workspace_active(project_dir)
    html_str = render_index_html(runs_data, workspace_active, runs_dir)
    out_path = out or (runs_dir / "index.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_str, encoding="utf-8")
    print(f"[OK] rendered: {out_path} ({len(runs_data)} runs)")
    return 0


def watch_loop(run_dir: Path, workspace_active: str | None, out_path: Path) -> int:
    print(f"[watch] polling {run_dir} every {WATCH_INTERVAL_SEC}s, output {out_path}")
    print(f"[watch] timeout {WATCH_TIMEOUT_SEC}s, Ctrl+C to stop")
    last_state: dict[str, float] = {}
    start = time.monotonic()
    try:
        while True:
            current = {
                fn: (run_dir / fn).stat().st_mtime
                for fn in STAGE_FILES
                if (run_dir / fn).exists()
            }
            if current != last_state:
                run = load_run(run_dir)
                html_str = render_per_run_html(run, workspace_active, watch=True)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(html_str, encoding="utf-8")
                stages = len((run.get("run") or {}).get("stages_completed") or [])
                final = (run.get("run") or {}).get("final_verdict") or "INCOMPLETE"
                print(f"[watch] re-rendered ({stages}/4 stages, verdict={final})")
                last_state = current
                if final not in ("INCOMPLETE", None):
                    print(f"[watch] run finalized ({final}), exiting")
                    return 0
            if time.monotonic() - start > WATCH_TIMEOUT_SEC:
                print(f"[watch] timeout {WATCH_TIMEOUT_SEC}s reached, exiting")
                return 0
            time.sleep(WATCH_INTERVAL_SEC)
    except KeyboardInterrupt:
        print("\n[watch] stopped by user")
        return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Render contextd pipeline trace as HTML.")
    p.add_argument("--run", help="Run ID (or prefix)")
    p.add_argument("--last", action="store_true", help="Latest run")
    p.add_argument("--all", action="store_true", help="Render index of all runs")
    p.add_argument("--watch", action="store_true", help="Live watch mode (re-render on change)")
    p.add_argument("--out", help="Output path override")
    p.add_argument("--project-dir", help="Project dir (default: walk up from CWD to find .contextd/config.json or legacy adapter)")
    args = p.parse_args()

    if args.project_dir:
        project_dir = Path(args.project_dir).resolve()
    else:
        project_dir = find_project_dir(Path.cwd())
        if not project_dir:
            sys.stderr.write("[render_trace] no .contextd/config.json or legacy adapter found walking up from CWD\n")
            return 2

    out = Path(args.out).resolve() if args.out else None

    if args.all:
        return cmd_render_index(project_dir, out)

    if not (args.run or args.last or args.watch):
        # Default to --last
        args.last = True

    return cmd_render_run(project_dir, args.run, args.last, out, args.watch)


if __name__ == "__main__":
    sys.exit(main())
