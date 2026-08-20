---
type: Decision
title: "ADR-005: Adopt a Rebuildable Synapse Lifecycle Graph"
description: "Keep workspace files canonical while adding lifecycle-aware nodes, typed edges, and task-specific context projections."
status: stable
node_id: decision.adopt-synapse-lifecycle-graph.v1
freshness: fresh
relations:
  - type: implements
    target: contract.synapse-node-edge-schema.v1
---

# ADR-005: Adopt a Rebuildable Synapse Lifecycle Graph

## Scope

contextd core runtime and the active workspace knowledge model.

## Status

ACCEPTED for implementation on `feat/synapse-lifecycle-graph`.

## Context

The task-context engine currently ranks a flat list of files. OKF lifecycle,
evidence review dates, `STALE` analysis labels, and supersession references are
present in separate conventions but do not affect core retrieval. Old knowledge
can therefore remain selected without a machine-readable stale warning.

The project must retain deterministic, local-first, file-backed behavior and
must not become a memory database or code graph indexer.

## Decision

Add a rebuildable synapse index over canonical workspace knowledge:

- Workspace documents are long-term governed knowledge nodes.
- Typed metadata relations become validated edges.
- Lifecycle and freshness remain independent.
- Stale and superseded nodes remain inspectable.
- Task context becomes a selected graph projection.
- Runtime observations/checkpoints remain runtime state until explicitly
  promoted through a reviewed workspace write.

## Alternatives Considered

| Option | Decision |
|---|---|
| Continue flat ranking | Rejected: cannot represent stale/superseded semantics |
| Delete/archive old files outside retrieval | Rejected: loses history and weakens auditability |
| Use a graph database as source of truth | Rejected: introduces drift and violates local build-system positioning |
| Infer all Markdown links as edges | Rejected: relation type and trust are ambiguous |
| Auto-promote runtime observations | Deferred: risks turning unreviewed inference into canonical knowledge |

## Consequences

Benefits:

- Stale knowledge is visible without silently acting as current guidance.
- Context selection becomes relationship-aware and more explainable.
- Supersession, contradiction, implementation, and evidence lineage become
  mechanically inspectable.
- The index remains reproducible and disposable.

Costs:

- Metadata and edge maintenance add authoring overhead.
- Invalid/dangling edges require diagnostics and tests.
- Date-based freshness introduces an explicit evaluation-date input.
- Context artifact consumers must tolerate new additive fields.

## Revisit Trigger

Revisit when one of these becomes true:

- Graph build time materially affects context command latency.
- More than one host needs a shared runtime-memory protocol.
- Teams require claim-level rather than document-level nodes.
- A rebuildable JSON index can no longer meet corpus scale.

## Related

- Contract: `../platform/contracts/synapse-node-edge-schema.md`
- Pattern: `../platform/patterns/synapse-context-projection.md`
- Plan: `docs/synapse-implementation-plan.md`
