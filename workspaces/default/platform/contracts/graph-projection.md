---
type: Contract
title: "Contract: bounded graph projection"
description: "Read-only seed traversal, semantic annotations, boundaries and provenance for advisory graph projections."
status: draft
node_id: contract.graph-projection.v1
knowledge_role: constraint
regions: [knowledge]
relations:
  - type: depends_on
    target: contract.synapse-node-edge-schema.v1
---

# Contract: bounded graph projection

This experimental contract extends the existing
[synapse context projection pattern](../patterns/synapse-context-projection.md).
The [Synapse v1 contract](synapse-node-edge-schema.md) remains unchanged.

## Scope

`contextd_graph_projection.v1` is advisory **metadata only**, not a
`contextd_task_context.v1` artifact. It does not authorize execution, load
source bodies, apply context policy, or replace normal context compilation.

## Invariants

1. Canonical workspace files remain the only knowledge source of truth.
   Build once with the existing safe scanner; use the retained source records
   to read frontmatter without another filesystem read.
2. Projection must verify the snapshot hash and retained source hashes. Graph
   error diagnostics refuse projection. Workspace isolation and exclusions for
   runtime observations, raw evidence, and unsafe paths remain unchanged.
3. Seeds are explicit local node IDs. Missing seeds, duplicate graph identities,
   seeds outside requested regions, and a node cap smaller than the seed set
   must fail; no implicit workspace or model-based seed inference is allowed.
4. Traversal is deterministic breadth-first. Process all seeds first, then
   prioritize constraints within each depth, followed by the versioned edge
   order and stable IDs. Keep one deterministic shortest parent path per node.
5. Use only Synapse v1 edge types. Direction controls traversal, not the stored
   meaning of an edge. Preserve every relation between selected nodes, including
   relations excluded from traversal by the edge filter.
6. Omitted outgoing `depends_on` neighbors and `implements` targets whose
   kind is `contract` or semantic role is `constraint` must be reported as gaps, including exclusions
   due to edge filters, direction, regions, depth, or node budget. Incoming
   contradictions and replacements must remain visible as warnings.
7. Depth, node count, and boundary report limits are explicit request parameters.
   Truncated reports must retain accurate total/truncated counts. These limits
   do not constitute a hard token budget or guarantee semantic completeness.
8. `knowledge_role` is independent of OKF `type`. Supported roles and fallback
   behavior are versioned by the schema. Invalid roles fall back to `knowledge`
   with a warning count. No role or relation establishes truth or confidence.
9. `regions` is a list of human-authored lowercase tags. No regions are inferred
   from paths. A region filter excludes untagged nodes; region membership is
   a retrieval scope, **not** an authorization or tenant-isolation boundary.
10. Noncurrent selected nodes must warn, never be silently promoted. Unknown
    freshness remains unknown. Preserve upstream diagnostic counts without
    exposing arbitrary diagnostic messages or source content.
11. Source hashes, evaluation date, normalized request, selected nodes/edges,
    gaps, and diagnostics determine the projection hash. Wall-clock build
    timestamps and absolute machine paths must not affect it.
12. Default warnings and dependency gaps do not fail the advisory CLI. `--strict`
    returns a failure for warnings, gaps, or metadata issues. Invalid request
    syntax/ranges return 2; resolution or snapshot errors return 1.

## Compatibility

Existing `contextd context`, Synapse v1 schemas, pack routing, lifecycle ranking,
and golden tasks are not replaced. The experimental `contextd-project` console
entry point is source-install only; it is not a new standalone release binary.

## Related

- [Projection guide and phased roadmap](../../../../docs/graph-projection.md)
- [Machine-readable schema](../../../../templates/graph-projection.schema.json)
