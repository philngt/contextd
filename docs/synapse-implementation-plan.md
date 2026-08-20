# Synapse Lifecycle Graph — Implementation Plan

## Delivery Status

Implemented on branch `feat/synapse-lifecycle-graph`. The contract, pattern,
ADR, schemas, file-backed builder, CLI, task-context integration, workspace
isolation guards, and acceptance tests are complete. The graph remains a
derived artifact; no runtime observation is promoted automatically.

## Goal

Add a deterministic, workspace-scoped knowledge graph to the contextd core so
stale or superseded knowledge remains inspectable without silently guiding new
tasks as if it were current.

The graph is a rebuildable index over canonical files. It is not a second
memory database and does not write inferred knowledge back into a workspace.

## Product Model

The implementation separates four concerns:

| Concern | Ownership | Durability | Representation |
|---|---|---|---|
| Long-term governed knowledge | Workspace authors | Durable, Git-backed | Files under `workspaces/{ws}/` |
| Synapse | contextd core | Rebuildable | Nodes, typed edges, lifecycle, freshness |
| Context | contextd compiler | Task-scoped, replaceable | A selected synapse projection in `contextd_task_context.v1` |
| Runtime memory | Agent host/workflow | Session/checkpoint scoped | Existing host history, observations, and workflow checkpoints |

Runtime memory is not automatically promoted. Durable promotion remains an
explicit reviewed write into the active workspace.

## Scope

### Included

1. `contextd_synapse.v1` JSON schema and file-backed builder.
2. Stable node IDs from explicit `node_id`, with deterministic path-derived
   fallback for legacy documents.
3. Lifecycle states: `draft`, `active`, `deprecated`, `superseded`.
4. Freshness states: `fresh`, `stale`, `unknown`.
5. Typed edges: `supersedes`, `supports`, `contradicts`, `implements`,
   `depends_on`, `derived_from`, and `related_to`.
6. Freshness evaluation from explicit metadata and `review_by`.
7. Diagnostics for invalid metadata, duplicate IDs, dangling targets,
   cross-workspace targets, and invalid supersede topology.
8. CLI preview/materialization through `contextd synapse`.
9. Lifecycle-aware task-context ranking and warnings.
10. Context projection metadata identifying selected nodes and traversed edges.
11. Single-scan build snapshots reused by context projection and materialization.
12. Raw-byte source hashes and transient decoded source records shared by graph
    construction, candidate collection, and static workspace context.
13. Precomputed path, node-ID, and active-replacement lookups shared across the
    context build.
14. Strict materialization identity checks covering the resolved knowledge root
    and every selected/static workspace source hash.

### Excluded

- Graph database or vector database dependencies.
- Code symbol/call graph indexing.
- Conversation capture.
- Automatic promotion of observations into canonical knowledge.
- Cross-workspace graph traversal.
- Automatic deletion of stale or superseded nodes.

## Metadata Contract

Legacy files require no changes. A concept may opt into stable identity and
relationships with top-level OKF-compatible frontmatter fields:

```yaml
---
type: Contract
status: stable
node_id: contract.payment-timeout.v2
freshness: fresh
review_by: 2026-12-31
relations:
  - type: supersedes
    target: contract.payment-timeout.v1
  - type: implements
    target: pattern.timeout-handling
---
```

Compatibility mappings:

- absent `status` -> lifecycle `active`
- `status: stable` -> lifecycle `active`
- `status: draft|deprecated` -> same lifecycle
- explicit `lifecycle: superseded` is accepted for graph semantics while OKF
  `status` may remain `deprecated`
- absent freshness metadata -> `unknown`
- expired `review_by` -> `stale`
- explicit `freshness: stale` remains stale regardless of `review_by`

## Runtime Flow

```text
resolve active workspace
  -> scan safe workspace knowledge files
  -> read exact bytes once and compute raw source hashes
  -> retain transient decoded source records
  -> parse metadata
  -> create deterministic nodes
  -> validate and normalize typed edges
  -> evaluate lifecycle/freshness
  -> compute synapse hash
  -> build reusable path/ID/replacement lookups
  -> rank task candidates with lifecycle policy
  -> emit selected context projection + diagnostics
  -> validate identity and materialize the same graph
```

## Retrieval Policy

Ranking remains deterministic. Lifecycle adjusts, but does not erase, the
existing keyword/category score:

| State | Default task behavior |
|---|---|
| active + fresh/unknown | Normal priority |
| draft | Lower priority and warning if selected |
| stale | Lower priority and warning if selected |
| deprecated | Strongly lower priority; retain for history/conflict tasks |
| superseded | Strongly lower priority; prefer an active node that declares a `supersedes` edge to it |

When a deprecated or superseded node is a candidate, the compiler may expand a
valid replacement edge into the candidate set. Category budgets and maximum
document limits still apply.

## Materialized Artifacts

`contextd synapse` writes, unless previewed:

```text
.contextd/context/synapse.json
```

The file is generated and safe to delete/regenerate. Canonical workspace files
remain the source of truth.

`contextd context` adds a `context_projection` object containing:

- synapse hash
- selected node IDs
- lifecycle/freshness state for each selected node
- relevant edges between selected nodes
- lifecycle/freshness policy version

The context builder returns the public artifact and its in-memory synapse
snapshot together to materializing callers. `materialize_context` validates the
snapshot identity and writes it directly; it does not scan or hash workspace
sources a second time. Validation covers artifact type, workspace, resolved
knowledge root, evaluation date, policy version, graph hash integrity,
the exact derived projection, and selected/static source-hash-map consistency.
A mismatch marks the reference `drifted` and refuses `synapse.json` rather than
rebuilding from a different point in time.

The decoded source records and graph lookups used during compilation are
transient and are not written into either artifact. This keeps canonical files
as the only long-term store and avoids introducing cache invalidation policy in
v1.

## Delivery Steps

1. Record ADR, pattern, contract, and schemas.
2. Implement frontmatter parsing and synapse construction as a standard-library
   module.
3. Add CLI build/preview/materialization.
4. Integrate node metadata and lifecycle penalties into context selection.
5. Add warnings and selection-trace reasons without breaking existing fields.
6. Add tests for deterministic output, legacy fallback, stale retention,
   supersession, invalid edges, workspace isolation, and CLI behavior.
7. Run runtime tests, wiki lint, doctor, and CLI smoke checks.

## Acceptance Criteria

- A stale document remains present in `contextd_synapse.v1.nodes`.
- An expired `review_by` deterministically produces `freshness: stale` for a
  supplied evaluation date.
- A superseded node and its replacement are connected by a typed edge.
- Invalid cross-workspace edges are rejected and reported; they are never
  traversed.
- A task artifact reports selected node states and warns when stale,
  deprecated, draft, or superseded knowledge is selected.
- Existing workspaces without synapse metadata continue to build context.
- Rebuilding unchanged inputs for the same evaluation date produces the same
  `synapse_hash`.
- CRLF and other byte-level source differences are represented by the exact
  raw-byte `source_hash`.
- One context build reads each governed workspace source at most once and does
  not reread it during materialization.
- A matching graph from another knowledge root is rejected even when its
  workspace name and graph hash are identical.
- No generated graph becomes a second source of truth.

## Rollback

The task-context integration is additive. Rollback consists of removing the
synapse projection and lifecycle score adjustment; existing artifact fields and
workspace content remain valid. Materialized `synapse.json` can be deleted and
rebuilt at any time.
