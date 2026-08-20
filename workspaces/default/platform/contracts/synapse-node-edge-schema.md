---
type: Contract
title: "Contract: synapse-node-edge-schema"
description: "Deterministic workspace-scoped node, edge, lifecycle, freshness, and context-projection invariants for contextd synapse artifacts."
status: stable
node_id: contract.synapse-node-edge-schema.v1
freshness: fresh
---

# Contract: synapse-node-edge-schema

> PAIR contract of pattern `../patterns/synapse-context-projection.md`. The
> pattern describes the build and retrieval flow; this contract defines the
> invariant artifact semantics.

## Rule

`contextd_synapse.v1` MUST be a deterministic, rebuildable index over the
active workspace. It MUST NOT become a second source of truth or traverse into
another workspace.

## Node Invariants

Every node MUST contain:

- `id`: explicit `node_id` or deterministic workspace-relative fallback.
- `workspace`: the active workspace.
- `kind`: normalized document category.
- `path`: knowledge-root-relative source path.
- `source_hash`: SHA-256 of the exact source bytes, before UTF-8 decoding or
  content redaction.
- `memory_class`: `long_term` for canonical workspace knowledge.
- `lifecycle`: `draft | active | deprecated | superseded`.
- `freshness`: `fresh | stale | unknown`.
- `id_source`: `frontmatter | path`.

The source document remains canonical. Generated nodes MUST NOT overwrite it.

## Edge Invariants

Every edge MUST contain `type`, `source`, and `target`. Allowed types:

```text
supersedes
supports
contradicts
implements
depends_on
derived_from
related_to
```

An edge target MUST resolve to a node in the same effective workspace graph.
Cross-workspace targets, self-edges, duplicate edges, dangling targets, and
supersede cycles MUST NOT enter the traversable edge set. They MUST produce a
diagnostic.

Targets are local node IDs. A qualified target such as
`workspace://other/node.id` is explicitly cross-workspace and MUST be rejected;
`workspace://{active}/node.id` may be normalized to the local node ID.

## Lifecycle And Freshness Invariants

- Missing OKF `status` behaves as `active` for backward compatibility.
- `status: stable` maps to `active`.
- `draft` remains retrievable but is lower priority.
- `deprecated` and `superseded` nodes remain in the graph for history.
- Explicit `freshness: stale` always remains stale.
- A valid `review_by` earlier than the evaluation date marks the node stale.
- Missing freshness evidence produces `unknown`, not an invented fresh claim.
- Lifecycle and freshness are independent dimensions.

## Context Projection Invariants

Task context is a projection, not a memory record. A projection MUST include:

- source `synapse_hash`
- selected node IDs
- state summary for selected nodes
- traversed/relevant edges between selected nodes
- lifecycle/freshness policy version

The compiler MUST warn when selected knowledge is draft, stale, deprecated, or
superseded. It MUST NOT silently delete such nodes.

A context build MUST derive the graph, candidate content, source hashes, and
lookup indexes from one coherent source snapshot. Governed workspace sources
MUST NOT be read or hashed again while projecting or materializing that build.
Decoded source records and lookup indexes are transient runtime data; they MUST
NOT be serialized as a second knowledge store.

When a caller supplies a synapse snapshot for materialization, the materializer
MUST verify its artifact type, workspace, resolved knowledge root, evaluation
date, policy version, graph hash integrity, exact derived context projection,
and the source hashes of selected/static documents. A mismatch MUST refuse
synapse materialization and surface a drift warning; it MUST NOT silently
rebuild from newer files.

## Runtime Memory Boundary

Session history, observations, and workflow checkpoints are runtime state.
They MUST NOT become `long_term` nodes without an explicit reviewed write into
the active workspace. Synapse indexing MUST ignore `.observations`, raw
evidence payloads, generated reports, and materialized runtime artifacts.

## Validator Behavior

- Invalid node or edge field: retain the source file, omit the invalid graph
  element, emit a non-blocking diagnostic.
- Duplicate explicit node ID: omit ambiguous edges to that ID and emit an error
  diagnostic.
- Cross-workspace edge: reject edge and emit an error diagnostic.
- Supersede cycle: reject cycle edges from traversal and emit an error
  diagnostic.
- Unknown frontmatter fields: tolerate them.

## Related

- Pattern: `../patterns/synapse-context-projection.md`
- Schema: `templates/synapse.schema.json`
- Task-context schema: `templates/task-context.schema.json`
- Management guide: `docs/synapse-context-management.md`
- Plan: `docs/synapse-implementation-plan.md`
