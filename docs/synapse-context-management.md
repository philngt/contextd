# Synapse Context Management and Loading Guide

## Purpose

This guide defines how maintainers and runtime consumers should author,
review, load, diagnose, and evolve context after enabling the synapse lifecycle
graph. It complements the normative
[synapse node/edge contract](../workspaces/default/platform/contracts/synapse-node-edge-schema.md)
and the implementation
[context projection pattern](../workspaces/default/platform/patterns/synapse-context-projection.md).

The goal is not to load the largest possible context. The goal is to load the
smallest governed context that is sufficient for the task while preserving
lineage to knowledge that was intentionally omitted.

## Capability Status

The distinction between current behavior and future policy is mandatory. Do
not document a proposed option as though the runtime already accepts it.

| Capability | v1 status |
|---|---|
| Workspace-scoped lifecycle graph | Implemented |
| Lifecycle/freshness-aware ranking | Implemented |
| One-hop active replacement expansion | Implemented |
| Category budgets and seven-document cap | Implemented |
| Context projection and selected-state warnings | Implemented |
| `lean`, `balanced`, or `audit` configuration profiles | Not implemented |
| Hard token limit | Not implemented; current estimate is advisory |
| Incremental graph rebuild/cache | Not implemented |
| Automatic runtime-memory promotion | Intentionally unsupported |

## Mental Model

```text
runtime memory               long-term governed knowledge
(host/session owned)         (workspace/Git owned)
       |                                  |
       | explicit review + canonical write|
       +--------------------------------->|
                                          v
                                rebuildable synapse
                                          |
                                task selection + budget
                                          v
                                  context projection
                                          |
                                     agent input
```

The boundaries are strict:

- Long-term knowledge is a reviewed file in the active workspace.
- Synapse is a disposable index over those files.
- Context is a task-scoped projection, not durable memory.
- Runtime memory belongs to the host or workflow and is not indexed as
  long-term knowledge.

## Authoring Knowledge Nodes

### Stable identity

Use an explicit `node_id` for contracts, patterns, decisions, runbooks, and
other documents expected to move or participate in relations. Treat it as a
stable public identity:

```yaml
node_id: contract.checkout-timeout.v2
```

Rules:

1. Do not change `node_id` merely because the file moves.
2. Do not reuse an ID for a different concept.
3. Use the path-derived fallback only for legacy or low-value documents.
4. Resolve duplicate-ID diagnostics before relying on graph traversal.

### Lifecycle and freshness

Lifecycle describes governance state; freshness describes currency. They must
not be collapsed into one field.

| Situation | Lifecycle | Freshness |
|---|---|---|
| Work is not approved | `draft` | `fresh` or `unknown` |
| Approved and usable | `active` | `fresh` or `unknown` |
| Still valid for compatibility, but discouraged | `deprecated` | independent |
| Replaced by another node | `superseded` | usually `stale`, but independent |
| Review deadline passed | unchanged | `stale` |

Use `review_by` when knowledge has a known review cadence:

```yaml
status: stable
freshness: fresh
review_by: 2026-12-31
```

An expired `review_by` makes the node stale for that evaluation date. Missing
freshness evidence remains `unknown`; file age or Git history must not be used
to invent a freshness claim.

### Supersession direction

The new active node declares that it supersedes the old node:

```yaml
---
node_id: contract.checkout-timeout.v2
status: stable
relations:
  - type: supersedes
    target: contract.checkout-timeout.v1
---
```

The old node remains present and should be marked `superseded`. Do not reverse
the edge, delete the old node, or make the old node point to an inferred
replacement.

### Relation selection

Use the narrowest relation that communicates reviewed intent:

| Relation | Use when |
|---|---|
| `supersedes` | The source replaces the target |
| `implements` | The source is an implementation or operational realization of the target |
| `depends_on` | The source cannot be applied correctly without the target |
| `supports` | The source provides corroborating guidance or evidence |
| `contradicts` | The source records a reviewed conflict that consumers must surface |
| `derived_from` | The source was produced from the target |
| `related_to` | A useful relation exists but no stronger type is justified |

Relations are explicit governance statements. Do not generate them from every
Markdown link or from model similarity.

## Runtime Loading Workflow

Use the following workflow for normal tasks:

1. Run `contextd resolve` to confirm workspace and packs.
2. Run `contextd context "task" --preview` to build the task projection.
3. Inspect `budget_report`, `warnings`, and `context_projection`.
4. Run `contextd explain "task" --text` when selection is surprising.
5. Run `contextd synapse --preview --text` when the issue concerns lifecycle,
   freshness, graph errors, or replacement lineage.
6. Materialize only after the projection is acceptable.

The current v1 selection order is:

```text
collect deterministic candidates
  -> attach long-term node state
  -> expand one-hop active replacements
  -> apply lifecycle/freshness score adjustments
  -> apply category budgets and max-doc cap
  -> slice selected content
  -> emit context projection and warnings
```

The compiler may select a stale node when it remains highly relevant or when
no better source exists. This is intentional: stale knowledge is visible and
warned, not silently erased.

## Operational Loading Modes

v1 does not expose configurable load-profile fields. The following modes are
operator workflows using supported commands, not config values.

### Normal task mode

Use `contextd context`. Consume `referenced_docs` and the materialized context
pack. This is the default for implementation, review, product, and design
tasks.

### Selection diagnosis mode

Use `contextd explain`. Inspect selected and dropped documents, state score
adjustments, replacement expansion, category budget exhaustion, and gaps. Do
not solve a bad selection by manually appending untracked prompt text; fix the
canonical metadata or retrieval map.

### Lifecycle audit mode

Use `contextd synapse --preview`. Inspect all nodes, edge diagnostics,
lifecycle counts, freshness counts, and `review_by` outcomes without loading
all document content into an agent prompt.

### Historical investigation mode

Build normal context first, then inspect referenced stale/superseded node paths
from the graph. Load full historical content only when the task explicitly
requires migration, incident reconstruction, or decision history.

## Context Cost and Efficiency Rules

Synapse improves relevance before it improves token count. The following rules
keep that distinction observable:

1. Prefer active replacements over stale or superseded content.
2. Keep omitted historical nodes as IDs/edges in lineage instead of copying
   their full content into the prompt.
3. Treat `budget_report.estimated_tokens_selected` as a comparison signal, not
   an exact provider bill.
4. Do not increase `max_docs` to hide weak classification or retrieval maps.
5. Keep engine and pack static context separate from workspace synapse nodes;
   shared inputs still participate in the compiled pack.
6. Reuse a materialized graph only when artifact type, workspace, resolved
   knowledge root, `synapse_hash`, evaluation date, policy version, projection
   content, and selected/static source hashes match.
7. Invalidate task context when selected source hashes, active packs, task
   text, workspace, or synapse policy changes.
8. Never cache across workspaces.

Within one `contextd context` invocation, graph projection and materialization
must reuse the same immutable in-memory synapse snapshot. Do not rebuild or
rehash workspace source files during materialization: this avoids a second full
linear scan and ensures `current-task.json` and `synapse.json` describe the same
source snapshot. Source changes are observed by the next build or explicit
diagnostic.

The builder reads each governed source as raw bytes once, hashes those exact
bytes, and retains only a transient decoded source record plus precomputed
path/ID/replacement lookups for the current invocation. These helpers are not a
persistent cache and are never written as knowledge. This removes duplicate
I/O and repeated graph-map construction without introducing cross-run or
cross-workspace invalidation risk.

Because v1 still fills category budgets up to the document cap, adding
synapse does not guarantee fewer tokens. A future hard-token policy must be
introduced through a versioned contract and evaluated against golden tasks.

## Runtime-to-Long-Term Promotion

Promotion is a review workflow, not a graph operation:

```text
runtime observation
  -> candidate statement with provenance
  -> human/domain review
  -> choose canonical contract/pattern/project doc
  -> write inside active workspace
  -> assign lifecycle/freshness metadata
  -> rebuild synapse
```

Reject promotion when provenance is missing, the target workspace is unclear,
the observation contains secrets, or it conflicts with a higher-priority
contract. Never write conversation summaries directly into long-term nodes.

## Diagnostics and Remediation

| Signal | Meaning | Preferred action |
|---|---|---|
| `invalid-node-id` | Explicit identity is malformed | Fix the canonical frontmatter |
| `duplicate-node-id` | More than one source claims one identity | Assign unique stable IDs and review relations |
| `dangling-edge` | Target is absent from the active graph | Correct the ID or add the missing governed source |
| `cross-workspace-edge` | Relation attempts workspace mixing | Remove it; do not copy the foreign target implicitly |
| `supersede-cycle` | Replacement lineage is contradictory | Choose a single forward replacement direction |
| Selected `stale` node | Relevant knowledge missed its review boundary | Review, replace, or explicitly retain it |
| High dropped-doc count | Candidate set is broad | Tighten keywords, retrieval maps, or task scope |
| High selected-token estimate | Context is content-heavy | Improve slicing or introduce a versioned hard-token policy |

Graph errors should fail `contextd synapse` and appear in `contextd doctor`.
Task compilation may continue with warnings so maintainers can inspect and
repair the knowledge rather than lose all context.

## Measurement Baseline

Track these signals per golden task before changing ranking or budgets:

- required-contract selection rate
- stale/deprecated selection rate
- active-replacement expansion rate
- selected and dropped document count
- estimated selected tokens
- correction prompts caused by missing or outdated context
- graph diagnostic count

Use the same task set, workspace snapshot, evaluation date, and policy version
for before/after comparisons. Do not claim cost reduction from fewer stale
selections alone; measure selected tokens or provider usage separately.

## Future Load Profiles

Configurable profiles may be added later, but they are not part of v1. Any
implementation must first define a versioned schema, compatibility behavior,
and golden-task expectations.

| Proposed profile | Intended behavior |
|---|---|
| `lean` | Active content first; stale/superseded lineage as compact references |
| `balanced` | Current lifecycle-aware selection with bounded replacement expansion |
| `audit` | Preserve more historical content and contradiction/supersession edges |

A profile must not weaken workspace isolation, secret blocking, contract
priority, or runtime-memory promotion rules.

## Review Checklist

Before merging knowledge or retrieval-policy changes:

- [ ] Active workspace is resolved and no foreign workspace was read.
- [ ] Durable concepts have stable, unique `node_id` values.
- [ ] Lifecycle and freshness express different concerns.
- [ ] `review_by` is evidence-based and uses an ISO date.
- [ ] New replacement points to old with `supersedes`.
- [ ] Runtime observations were reviewed before canonical write.
- [ ] `contextd synapse --preview` has no graph errors.
- [ ] `contextd explain` shows expected selection and drop reasons.
- [ ] Golden tasks preserve required contracts and acceptable budget signals.
- [ ] Wiki lint, doctor, schemas, and runtime tests pass.

## Related

- [Build system model](build-system-model.md)
- [Context quality](context-quality.md)
- [Synapse implementation plan](synapse-implementation-plan.md)
- [Workspace resolution](../agents/pipeline/workspace-resolution.md)
- [Task-to-docs map](../agents/pipeline/task-to-docs-map.md)
