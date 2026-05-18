# Service: wiki-usage

## Purpose

3 commands chính cho task wiki-aware: planning before code (`/contextd-use`), syncing wiki sau code change (`/contextd-update`), full re-validation (`/contextd-rebase`).

## Input

- `/contextd-use` — task description (free-text)
- `/contextd-update` — optional `--scope` for narrow target
- `/contextd-rebase` — no args

## Output

- `/contextd-use`: invokes 5-stage pipeline; writes `.claude/context/current-task.md`; emits trace `.claude/runs/{run_id}/`; Builder produces code per task
- `/contextd-update`, `/contextd-rebase`: edits files trong `{ws}/...` qua `wiki-curator` subagent

## Flow

Applies platform pattern:
→ [../../platform/patterns/multi-stage-subagent-pipeline.md](../../platform/patterns/multi-stage-subagent-pipeline.md) (`/contextd-use` 5-stage flow)
→ [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md) (all 3 commands)

```
/contextd-use:
  Stage 0 → Stage 1 (planner) → Stage 2 (context-selector) → Stage 2.5 (plan-reviewer GATE)
                                                                ↓ APPROVED
                                                            Stage 3 (Builder)
                                                                ↓
                                                            Stage 4 (reviewer, optional)

/contextd-update, /contextd-rebase:
  workspace resolve → detect changes → delegate to wiki-curator → main agent verify path
```

## Config

```yaml
use_wiki:
  emit_trace: true
  trace_dir: ".claude/runs/{run_id}/"
  stage_4_enabled_default: true        # validator step
update_wiki:
  curator_delegation: required          # use --inline only when curator unavailable
rebase_wiki:
  scope_default: full_workspace
```

## Config Overrides

| Parameter | Platform Default | This Service | Reason |
|-----------|-----------------|--------------|--------|
| _(none — engine-level service, no overrides)_ | | | |

## Failure Handling

| Scenario | Action |
|----------|--------|
| Stage 2.5 BLOCK (`/contextd-use`) | STOP, output reasons; user fix gap → retry |
| Sub-agent unavailable (`/contextd-update`) | STOP với `CURATOR UNAVAILABLE` error; rerun với `--inline` if needed |
| `/contextd-rebase` detects unresolvable conflict | Output report; user manual merge |
| Trace emit fail | Warn nhưng tiếp tục pipeline (observability không block flow) |
| Builder violates context (caught Stage 4) | Output violation report; KHÔNG tự fix — user decide |

## Notes

- `/contextd-use` là entry-point chính cho mọi task wiki-aware (implement_feature, fix_bug, design, incident, review).
- `/contextd-update` vs `/contextd-rebase`:
  - `contextd-update`: incremental, dựa vào git diff → curator áp dụng changes.
  - `contextd-rebase`: full scan, wiki vs codebase, vá mọi drift.
- Stage 4 (wiki-reviewer) là OPTIONAL — recommended cho task wiki-aware nhưng có thể skip cho rapid iteration.

## Related

- Pattern: [../../platform/patterns/multi-stage-subagent-pipeline.md](../../platform/patterns/multi-stage-subagent-pipeline.md)
- Pattern: [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md)
- Sub-agents doc: [agents.md](agents.md) (wiki-planner, wiki-context-selector, wiki-plan-reviewer, wiki-curator, wiki-reviewer)
- Engine source: `.claude/commands/contextd-use.md`, `contextd-update.md`, `contextd-rebase.md`
- Engine spec: `agents/pipeline/multi-agent-pipeline.md`, `prompt-template.md`, `validator-rules.md`
- Source: F-017b, evidence `2026-05-08-engine-bootstrap-wiki-template`
