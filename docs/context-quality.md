# Context Quality

contextd is deterministic by default: it compiles task context from the active workspace, active packs, contracts, patterns, runbooks, and selected workspace docs. Advisory search can help discovery, but it must not override deterministic contracts or task artifacts.

## Production Flow

```bash
contextd resolve --format json
contextd doctor --format text
contextd synapse --format text --no-materialize
contextd context "debug checkout timeout" --format json --no-materialize
contextd explain "debug checkout timeout" --format text
```

- `resolve` confirms canonical `.contextd/config.json`, `knowledge_root`, workspace, and packs.
- `doctor` catches setup drift before the agent works.
- `context` emits the canonical `contextd_task_context.v1` artifact.
- `synapse` reports lifecycle, freshness, edge, and graph diagnostics.
- `explain` shows why docs were selected or dropped.

## Selection Signals

`contextd context` classifies intent and workstream, detects active pack components, collects deterministic candidates, ranks them, slices relevant sections, and emits source hashes. The JSON artifact includes:

Matched pack routes are explicit selection evidence: exact files named by a
component retrieval map receive deterministic route priority, while expanded
directories remain budgeted candidates. Manifest-v3 packs additionally load
only Global Principles plus matched component knowledge. This avoids making pack
ownership depend on accidental English/Vietnamese word overlap.

- `referenced_docs`: selected docs and sliced content.
- `gaps`: missing contracts, missing pack docs, unsafe retrieval-map paths, or other non-guessed context.
- `warnings`: compatibility, redaction, or runtime advisory messages.
- `synapse`: reference to the rebuildable workspace lifecycle graph.
- `context_projection`: selected long-term knowledge node IDs, states, and relevant typed edges.
- `contextPack`: deterministic static context pack reference.
- `budget_report`: deterministic estimates for referenced, static, and total
  compiled context, including deduplicated overlap.

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
| Currency | Selected nodes are active and fresh/unknown, or stale selection is explicitly warned. | Deprecated or stale guidance silently behaves as current truth. |
| Lineage | Supersession and support edges explain the selected knowledge. | Old and replacement documents are indistinguishable. |
| Operator control | The user can name the goal, current stage, open decision, next evidence, and stop condition; AI recommendations are explicit. | AI silently expands scope/direction and the user cannot tell what to do next or when to stop. |

## Budget Report

The budget estimator is intentionally model-neutral. It uses a stable character-based approximation so repeated runs produce the same result without depending on a specific LLM tokenizer.

Use it to answer:

- How many docs were considered vs selected.
- Which category consumed budget.
- Which docs were dropped due to `max_docs` or category budget.
- Whether a pack is too broad for a task.
- How much context comes from `referenced_docs` versus `static_context`.
- Whether the actual deduplicated total stays within the intended prompt budget.

The key fields are `estimated_tokens_referenced`, `estimated_tokens_static`, and
`estimated_tokens_total`. `static_docs` lists the pack/engine inputs included in
the compiled prompt; `deduplicated_overlap_docs` records content counted only
once. Older `estimated_tokens_selected` remains available as a compatibility
alias for selected referenced content.

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

1. `summary.budget_report`: referenced/static/total cost and whether selected
   docs hit max-doc or category limits.
2. `selection_trace.selected_docs`: the docs the runtime actually emitted.
3. `selection_trace.dropped_docs`: docs that were considered but lost to score, duplicate detection, category budget, max docs, or safety policy.
4. `artifact.gaps`: missing required docs, unsafe paths, unresolved placeholders, or invalid contract-index entries.
5. `artifact.source_hashes`: whether the artifact reflects the source files you expected.
6. `artifact.context_projection`: selected node lifecycle/freshness and typed edges.
7. `artifact.synapse.summary`: graph diagnostics and state counts for the evaluation date.

If the selected docs are wrong, fix source knowledge first: pack keywords,
manifest-v3 retrieval (or v2 retrieval-map paths), workspace project maps, or
policy expectations. Use `contextd find` only for discovery; it should not
become the hidden source of truth.

## Related

- [Build system model](build-system-model.md)
- [Comparison and positioning](comparison.md)
- [Synapse context management and loading](synapse-context-management.md)
- [Measuring contextd effectiveness](effectiveness.md)
- [MCP adapter](mcp.md)
- [Runbooks index](../workspaces/default/runbooks/README.md)
- [Workspace resolution](../agents/pipeline/workspace-resolution.md)
- [Operator steering and wayfinding](../packs/pack-operator-steering/README.md)
