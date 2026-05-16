# Service: observability

## Purpose

Debug + measure efficacy của 5-stage pipeline (`/use-wiki`). Trace per-run JSON dưới `.claude/runs/{run_id}/`, aggregate cho long-term insights, visualize traces.

## Input

3 commands:
- `/wiki-trace {run_id}` — render 1 run timeline
- `/wiki-eval` — aggregate eval report (optional date range filter)
- `/wiki-viz` — HTML viewer + live watch (optional `{run_id}`)

## Output

- `/wiki-trace`: Markdown timeline report.
- `/wiki-eval`: Markdown eval report (hallucination rate, top knowledge gaps, plan-block rate, violation hotspots).
- `/wiki-viz`: HTML viewer file.

## Flow

Applies platform pattern:
→ [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md)

```
/wiki-trace:
  workspace resolve → read .claude/runs/{run_id}/*.json → validate vs run-trace.schema.json
  → invoke scripts/render_trace.py → markdown output

/wiki-eval:
  workspace resolve → aggregate .claude/runs/{run_id}/* across N runs
  → cross-reference {ws}/eval/golden-tasks/* → derive scorecards via templates/task-scorecard.md
  → markdown report

/wiki-viz:
  workspace resolve → emit HTML viewer (single-file, optional live-watch mode)
```

## Config

```yaml
trace_dir: ".claude/runs/"
trace_schema: "templates/run-trace.schema.json"
render_script: "scripts/render_trace.py"
golden_tasks_dir: "{ws}/eval/golden-tasks/"      # per-workspace
scorecard_template: "templates/task-scorecard.md"

wiki_eval:
  default_date_range: last_30_days
  metrics:
    - hallucination_rate
    - knowledge_gaps_top_N
    - plan_block_rate                            # Stage 2.5 BLOCK frequency
    - violation_hotspots                         # Stage 4 violation counts
```

## Config Overrides

| Parameter | Platform Default | This Service | Reason |
|-----------|-----------------|--------------|--------|
| _(none — engine-level)_ | | | |

## Failure Handling

| Scenario | Action |
|----------|--------|
| `{run_id}` không tồn tại trong `.claude/runs/` | STOP, hint list available run_ids |
| Trace JSON invalid (schema fail) | STOP, hint regenerate qua `/use-wiki` rerun |
| `scripts/render_trace.py` not found | STOP, hint engine setup |
| `/wiki-viz` browser unavailable | Output HTML path, user manual open |
| `/wiki-eval` empty traces (no runs in range) | Render với "no data in range" report |

## Notes

- 3 commands độc lập với core flow — read-only consumers của `.claude/runs/{run_id}/` traces.
- Trace JSON schema versioned trong `templates/run-trace.schema.json` — schema migration cần coordinate khi update.
- `/wiki-viz` orphaned trong `.claude/commands/README.md` index Section "Pipeline observability" — separate session sẽ fix qua `/update-wiki` (per ADR `../../decisions/`'s F-023 action item).
- Manual A/B đánh giá: `{ws}/eval/golden-tasks/README.md` (per-workspace) + `templates/task-scorecard.md`.

## Related

- Pattern: [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md)
- Service: [wiki-usage.md](wiki-usage.md) (`/use-wiki` emits traces consumed by these 3 commands)
- Engine source: `.claude/commands/wiki-trace.md`, `wiki-eval.md`, `wiki-viz.md`
- Engine spec: `agents/pipeline/observability.md`
- Templates: `templates/run-trace.schema.json`, `templates/task-scorecard.md`
- Scripts: `scripts/render_trace.py`, `scripts/emit_trace.py`
- Source: F-017e, evidence `2026-05-08-engine-bootstrap-wiki-template`
