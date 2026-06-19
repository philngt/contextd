# Runbook: Context Quality Degradation

## Symptom

`contextd context` succeeds but the agent receives weak or surprising context: wrong docs selected, important contracts missing, context is over-budget, stale `.contextd/context/current-task.*` is reused, or an adapter behaves differently from the canonical JSON artifact.

## Likely Causes

1. The active workspace or active packs do not match the codebase.
2. The task text does not contain the component/domain/project keywords needed by deterministic retrieval.
3. A pack `retrieval-map.md` points to missing, unsafe, or too-broad paths.
4. Category budgets drop the expected docs.
5. Runtime adapters are stale and still rely on legacy context paths.

## Diagnosis Steps

```bash
# Check canonical config, workspace, packs, and safety drift.
contextd doctor --format text

# Build the canonical artifact without writing runtime artifacts.
contextd context "describe the failing task here" --format json --no-materialize

# Inspect selected and dropped docs.
contextd explain "describe the failing task here" --format text
```

Key signals to look for:
- `doctor` reports missing packs, unsafe retrieval-map paths, or adapter drift.
- `explain` shows expected docs under dropped docs with `category_budget_exhausted` or `max_docs_exhausted`.
- `gaps[]` includes missing contracts, missing pattern docs, or blocked security-policy entries.
- `budget_report.estimated_tokens_by_category` is dominated by a category unrelated to the task.

## Fix

| Cause | Fix |
|-------|-----|
| Wrong workspace | Update `<project>/.contextd/config.json#workspace`, then rerun `contextd resolve`. |
| Missing active pack | Add the pack to `.contextd/config.json#packs` or workspace `workspace.md ## Packs`. |
| Weak component detection | Add precise `pack.yaml#keywords` for the component, or make the task prompt include the expected component/domain/project name. |
| Unsafe retrieval-map path | Rewrite the path to `{ws}/...`, `packs/{active-pack}/...`, or `templates/...`; remove absolute paths and `..`. |
| Over-budget context | Narrow the retrieval map, split broad docs, or tune category budgets in the engine follow-up. |
| Stale artifacts | Delete `.contextd/context/` and rerun `contextd context`; runtime artifacts are generated output. |
| Adapter drift | Regenerate exports with `contextd export` and verify adapters consume `contextd_task_context.v1`. |

## Verification

```bash
contextd doctor --format json
contextd explain "describe the fixed task here" --format json
```

Confirm:
- `doctor.status` is `ok` or only expected warnings.
- The expected contract/pattern/runbook appears under `selection_trace.selected_docs`.
- `gaps[]` contains no unexpected blocking gap.
- `budget_report.selected_docs` is within `retrieval_policy.max_docs`.

## Escalation

Escalate if `doctor` is clean but `explain` repeatedly drops required contracts or selects another workspace's docs. Include `contextd resolve --format json`, `contextd explain --format json`, the active pack list, and the relevant `retrieval-map.md` rows.

## Related

> Mọi link nằm trong cùng workspace (`{ws}/...`).

- [runtime-adapter-drift.md](runtime-adapter-drift.md)
- [context-artifact-generation-failure.md](context-artifact-generation-failure.md)
- [materialized-context-pack-stale.md](materialized-context-pack-stale.md)
- [../platform/patterns/workspace-resolve-step0.md](../platform/patterns/workspace-resolve-step0.md)
