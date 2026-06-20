# Measuring contextd Effectiveness

contextd should be evaluated by whether it makes agent inputs more reliable, not by broad claims about model quality. The runtime already emits enough data to measure the first useful signals.

## What contextd Can Prove Today

| Signal | How to observe it | Why it matters |
|---|---|---|
| Deterministic selection | Run `contextd explain "task" --format json` and compare selected docs plus `source_hashes`. | Same source knowledge and task should produce the same build inputs. |
| Governance coverage | Run `contextd policy-check "task" --format json` and inspect required docs, contracts, categories, gaps, and violations. | Required context is selected or reported as missing before the agent works. |
| Agent efficiency proxy | Inspect `budget_report`, selected doc count, dropped docs, and estimated tokens. | The artifact stays focused instead of dumping an entire wiki into the agent. |

## Minimal Demo Scorecard

Use this for a new user or team rollout:

```bash
contextd resolve --format json
contextd doctor --format json
contextd context "prepare agent context for product requirements" --format json --no-materialize
contextd explain "prepare agent context for product requirements" --format json
contextd eval --golden --workspace default --format json
```

Good first-run signals:

- `resolve` reports the expected workspace and `knowledge_root`.
- `doctor` returns `ok` before an agent session starts.
- `context` emits `artifact_type=contextd_task_context.v1`.
- `explain.summary.referenced_doc_count` is small enough to inspect.
- `explain.summary.gap_count` is either zero or actionable.
- `explain.summary.budget_report` shows selected, considered, dropped, and estimated token counts.
- `artifact.source_hashes` names the exact source docs behind the build.
- `eval --golden` passes for the bundled demo tasks.

## What Not To Claim Yet

Do not claim contextd reduces tokens by a fixed percentage, improves model answer quality by a fixed percentage, or beats a code graph/vector search system unless a reproducible benchmark exists.

Recommended wording:

- "contextd reports selected docs, dropped docs, gaps, source hashes, and budget estimates."
- "contextd makes context selection auditable before the agent works."
- "contextd helps teams test context selection with golden tasks."

Avoid wording such as:

- "contextd guarantees better answers."
- "contextd replaces code intelligence."
- "contextd is a memory database."
- "contextd reduces tokens by N percent."

## Team Rollout Metrics

For real teams, track 5 to 10 recurring tasks and record:

- expected docs selected vs actual docs selected
- required contracts present or reported as gaps
- wrong-workspace incidents
- policy violations caught before agent output
- number of corrective prompts caused by missing context
- context artifact size and estimated selected tokens

These metrics keep the product thesis grounded: contextd is useful when it turns maintained team knowledge into reliable agent inputs.
