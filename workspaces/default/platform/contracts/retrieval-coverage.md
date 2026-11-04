---
type: Contract
title: "Contract: retrieval-coverage"
description: "Task-specific eligibility, scoped retrieval gaps and agent-visible diagnostics."
status: draft
node_id: contract.retrieval-coverage.v1
freshness: unknown
---

# Contract: retrieval-coverage

## Rule

Candidate discovery MUST NOT imply task-specific support. Category priority,
lifecycle adjustments and the existence of workspace files MUST NOT make an
unrelated candidate eligible. A build MAY select zero referenced documents.

## Eligibility

A candidate MUST have at least one of these signals before ranking and budgets:

- A specific query term in its name or delivered sections. Generic actions and
  software-role nouns are excluded from effective query terms. Explicitly
  detected pack component identities are retained. Literal matching is not
  semantic entailment.
- An explicitly configured component retrieval route.
- A task-matched OES assertion with checked source evidence.
- An active one-hop replacement of an independently relevant historical node.

General static guidance MUST remain available without being counted as support
for the particular task. Explicitly selected component sections in a pack MAY
count as a declared route. Eligibility MUST NOT expand replacement chains.

## Report and gaps

The artifact SHOULD expose `coverage` with selected support paths, query terms,
literal matches, unmatched terms and the supplied graph's route status.
`coverage.complete` MUST be false: matching signals do not establish that the
task is answerable or that all requirements are covered.

When no task-specific support is selected, the build MUST emit an actionable
`knowledge-coverage` gap. It MUST distinguish missing retrieval matches from
matching candidates excluded by budgets or section filters. A supplied graph
that contributes no selected evidence MUST produce a scoped `oes-coverage` gap.
Neither report proves absence across the entire workspace. Unmatched literal
terms alone MUST NOT be reported as missing knowledge; aliases may exist.

## Agent output

The same coverage and gap report MUST enter both task Markdown and the compiled
agent pack. Its content MUST be bound to pack identity and included in the rough
token estimate as `estimated_tokens_diagnostics`. Changing these diagnostics
after a build MUST invalidate materialization. Empty gap lists MUST NOT be
presented as proof of complete knowledge.

## Related

- [OES input contract](oes-context.md)
- [Task artifact schema](../../../../templates/task-context.schema.json)
- [Context filter](../../../../agents/pipeline/context-filter.md)
- [Effectiveness and limitations](../../../../docs/effectiveness.md)
