# Context Quality

contextd is deterministic by default: it compiles task context from the active workspace, active packs, contracts, patterns, runbooks, and selected workspace docs. Advisory search can help discovery, but it must not override deterministic contracts or task artifacts.

## Production Flow

```bash
contextd resolve --format json
contextd doctor --format text
contextd context "debug checkout timeout" --format json --no-materialize
contextd explain "debug checkout timeout" --format text
```

- `resolve` confirms canonical `.contextd/config.json`, `knowledge_root`, workspace, and packs.
- `doctor` catches setup drift before the agent works.
- `context` emits the canonical `contextd_task_context.v1` artifact.
- `explain` shows why docs were selected or dropped.

## Selection Signals

`contextd context` classifies intent and workstream, detects active pack components, collects deterministic candidates, ranks them, slices relevant sections, and emits source hashes. The JSON artifact includes:

- `referenced_docs`: selected docs and sliced content.
- `gaps`: missing contracts, missing pack docs, unsafe retrieval-map paths, or other non-guessed context.
- `warnings`: compatibility, redaction, or runtime advisory messages.
- `contextPack`: deterministic static context pack reference.
- `budget_report`: lightweight deterministic budget estimate.

## Quality Dimensions

Good context is not "more text." It has a few observable properties:

| Dimension | Healthy Signal | Bad Signal |
|---|---|---|
| Relevance | Selected docs match task intent, workstream, active packs, and project scope. | Generic contracts or unrelated project docs dominate the artifact. |
| Completeness | Required contracts, requirements, runbooks, or design docs are present. | The agent has to infer missing rules from vague prose. |
| Isolation | All workspace docs stay under the active `workspaces/{workspace}/`. | Docs from another workspace appear or influence retrieval. |
| Explainability | `contextd explain` names selected/dropped docs and reasons. | Users cannot tell why a doc was included. |
| Budget focus | Drops are expected and category budgets are understandable. | High-value docs are dropped while low-value docs consume slots. |
| Governance | Policy checks pass or fail with actionable rule IDs. | Policy violations appear only after agent output. |
| Safety | Secret-like paths are skipped and inline secrets are redacted. | Raw credentials or immutable evidence sources enter `referenced_docs`. |

## Budget Report

The budget estimator is intentionally model-neutral. It uses a stable character-based approximation so repeated runs produce the same result without depending on a specific LLM tokenizer.

Use it to answer:

- How many docs were considered vs selected.
- Which category consumed budget.
- Which docs were dropped due to `max_docs` or category budget.
- Whether a pack is too broad for a task.

`contextd explain` is the easiest way to inspect this because it includes selected and dropped docs with reasons.

## Safety Guard

Runtime reads block obvious secret-bearing paths before reading content, including `.env`, key/certificate files, `secrets/`, `credentials/`, and common production credential config names.

When normal markdown contains suspicious inline secrets, contextd redacts the value before the content enters `referenced_docs` and adds a warning. The posture is conservative: skipped or redacted context is better than leaked context.

## Evaluating Effectiveness

Use a small scorecard for real tasks:

| Signal | Good outcome |
|---|---|
| Required contract present | The artifact includes the contract or reports a blocking gap. |
| Wrong workspace avoided | `resolve.workspace` matches the codebase. |
| Budget is focused | Selected docs are under budget and category drops are explainable. |
| Gaps are explicit | Missing docs appear in `gaps[]`, not as agent guesses. |
| Adapter agreement | Claude/Codex/Cursor/MCP use the same JSON artifact shape. |

For a team rollout, keep 5 to 10 golden tasks and compare agent output with and without `contextd context`. Track whether the agent used the expected contract, avoided wrong-workspace knowledge, and needed fewer corrective prompts.

## Reading `explain`

Use `contextd explain "task" --format json` when context feels wrong.

Start with:

1. `summary.budget_report`: whether the selected docs hit max-doc or category limits.
2. `selection_trace.selected_docs`: the docs the runtime actually emitted.
3. `selection_trace.dropped_docs`: docs that were considered but lost to score, duplicate detection, category budget, max docs, or safety policy.
4. `artifact.gaps`: missing required docs, unsafe paths, unresolved placeholders, or invalid contract-index entries.
5. `artifact.source_hashes`: whether the artifact reflects the source files you expected.

If the selected docs are wrong, fix source knowledge first: pack keywords, retrieval-map paths, workspace project maps, or policy expectations. Use `contextd find` only for discovery; it should not become the hidden source of truth.

## Related

- [Build system model](build-system-model.md)
- [Comparison and positioning](comparison.md)
- [Measuring contextd effectiveness](effectiveness.md)
- [MCP adapter](mcp.md)
- [Runbooks index](../workspaces/default/runbooks/README.md)
- [Workspace resolution](../agents/pipeline/workspace-resolution.md)
