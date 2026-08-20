---
type: Pattern
title: "Pattern: synapse-context-projection"
description: "Build a workspace-scoped lifecycle graph and compile task context as a deterministic projection without creating a second memory store."
status: stable
node_id: pattern.synapse-context-projection.v1
freshness: fresh
relations:
  - type: implements
    target: contract.synapse-node-edge-schema.v1
---

# Pattern: synapse-context-projection

> PAIR pattern of contract `../contracts/synapse-node-edge-schema.md`. This
> pattern describes implementation flow; the contract defines invariants.

## Context

Flat file retrieval cannot distinguish current guidance from stale,
deprecated, or superseded knowledge. Deleting old knowledge loses audit
history. A rebuildable synapse index preserves every governed source as a node
while making lifecycle and relationships explicit during context compilation.

## Flow

```text
active workspace files
  -> safe source scan
  -> one raw-byte source snapshot
  -> metadata + hash normalization
  -> nodes + typed edges
  -> reusable path/ID/replacement lookups
  -> diagnostics + deterministic synapse hash
  -> task candidate annotation
  -> lifecycle-aware rank and replacement expansion
  -> context projection
  -> identity-checked materialization of the same graph
```

1. Resolve the active workspace using `workspace-resolve-step0`.
2. Scan governed knowledge only; exclude runtime and raw evidence stores.
3. Read each governed source as bytes once, hash those exact bytes, decode it,
   and retain a transient source record for the rest of that build.
4. Prefer explicit `node_id`; derive a deterministic ID for legacy docs.
5. Evaluate lifecycle and freshness independently.
6. Validate typed edges before making them traversable.
7. Build path, ID, and active-replacement lookups once per graph build.
8. Preserve stale/deprecated/superseded nodes in the index.
9. Compile only the task-relevant subgraph into context.
10. Surface state warnings and selection reasons.
11. Materialize only the graph that passed snapshot identity and selected-source
    hash checks; never rescan as an implicit drift check.

## Default Config

```yaml
max_traversal_depth: 1
stale_score_penalty: 4
draft_score_penalty: 6
deprecated_score_penalty: 12
superseded_score_penalty: 16
materialized_path: .contextd/context/synapse.json
```

These are runtime policy constants for artifact version 1. Changing them
requires a policy-version change and evaluation update.

## Failure Strategy

| Scenario | Action |
|---|---|
| Missing frontmatter | Build path-derived legacy node with unknown freshness |
| Invalid metadata | Keep source discoverable, emit diagnostic, use safe default |
| Dangling edge | Reject edge from traversal, emit diagnostic |
| Cross-workspace target | Reject edge, emit error diagnostic |
| Supersede cycle | Reject cycle edges, keep nodes, emit error diagnostic |

## Implementation Rules

- The graph index is derived and atomically replaceable.
- Source hashes are computed from exact source bytes before decoding or
  redaction; exposed content still follows the existing redaction boundary.
- Source records and graph lookup indexes live only for the current build.
- Projection and materialization reuse that build state rather than rebuilding
  indexes or rereading governed workspace files.
- Workspace node discovery never reads another workspace.
- Runtime memory is not auto-promoted.
- Context budgets remain enforced after graph expansion.
- Selection remains deterministic for the same source tree, task, and
  evaluation date.

## Anti-patterns

- Using a graph database as the canonical knowledge store.
- Deleting stale nodes instead of changing freshness/lifecycle.
- Treating `stale`, `deprecated`, and `superseded` as synonyms.
- Following arbitrary Markdown links as trusted graph edges.
- Inferring cross-workspace relationships.
- Persisting agent speculation as long-term knowledge.

## Used By

- `scripts/lib/synapse_engine.py`
- `scripts/lib/task_context_engine.py`
- `scripts/cmd_synapse.py`

## Related

- Contract: `../contracts/synapse-node-edge-schema.md`
- Pattern: `workspace-resolve-step0.md`
- Management guide: `docs/synapse-context-management.md`
- Plan: `docs/synapse-implementation-plan.md`
