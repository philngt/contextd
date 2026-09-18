---
type: Contract
title: "Contract: decision-first context"
description: "Author-classified support projection preserves required constraints, local facts, provenance and outcome verification."
status: draft
node_id: contract.decision-context.v1
knowledge_role: constraint
regions: [knowledge]
relations:
  - type: depends_on
    target: contract.synapse-node-edge-schema.v1
---

# Contract: decision-first context

## Scope

Optional support selection for an explicitly profiled domain pack. It is a
context contract, not a model-competence assertion or an authorization to act.

## Invariants

1. Task facts, controlling workspace definitions, constraints, permissions,
   accepted decisions and required procedures remain authoritative. An author
   cannot relax them by labeling them “foundation” or “skill.”
2. Strategy/judgment, their conditions/exceptions and evidence/stop criteria
   remain together. A strategy does not require an optional skill document.
3. Only explicitly designated supplementary foundations and procedures can be
   deferred. Local unknowns and conflicting evidence are reported, not guessed.
4. Requests identify source sections within the active pack/task scope. They
   are not filesystem paths, remote URLs, executable commands or permission
   grants. Invalid or unresolved requests fail before materialization.
5. Raw source hashes retain their meaning. Different projected content or
   support requests bind a distinct output identity; unchanged unprofiled
   callers retain backward-compatible identity semantics.
6. Workspace isolation, source redaction, snapshot coherence and governance
   remain in force. No deferred body leaks through a duplicate reference.
7. A host decides whether additional support is needed. The context builder
   neither infers knowledge from model confidence nor learns by rewriting
   shared sources automatically. All real actions still need tools and authority.
8. Required content is never silently omitted for a smaller context. Source
   token estimates are not hard tokenizer caps or proof of improved quality.

## Verification

Compare core-only, exact-support and full builds; check constraints, source and
projection hashes, scoped references, errors before writes and actual rendered
artifacts. Human review validates whether an author correctly classified content.

## Related

- [Synapse invariants](synapse-node-edge-schema.md)
- [Authoring and API contract](../../../../docs/decision-context.md)
