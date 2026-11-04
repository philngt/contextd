# Context Filter + Rank

## Purpose

Select zero to seven task-relevant documents, rank eligible candidates by
priority, and slice each document to the sections the agent needs. Seven is a
ceiling, not a target to fill with unrelated guidance.

## Eligibility Before Ranking

An eligible candidate has a specific query-term match in its delivered sections
or name, an explicit component retrieval route, checked OES evidence for a
matched assertion, or a one-hop replacement route from a relevant historical
document. Generic actions such as `add` and software-role nouns such as `consumer`
or `service` do not establish relevance alone. Explicit component identities
detected from configured packs remain valid routes. `coverage.query_terms`
records the effective terms after this filter, not every token in the task.
Category and lifecycle scores rank eligible documents; they do not make a
document eligible. Explain traces label rejected filler `no_task_relevance`.

No selected support produces a `knowledge-coverage` gap. A requested graph with
no selected evidence produces a scoped `oes-coverage` gap. Literal matches and
declared routes are retrieval signals; they do not establish complete knowledge.
Coverage and gaps enter the agent pack, its identity and its token estimate.

## Baseline Static Docs

`agents/constraints.md` and `agents/coding-rules.md` are **engine baseline**: they
are always loaded into the compiled context. They do not consume one of the 5–7
retrieved-document slots, but their actual sliced token estimate is included in
`budget_report.estimated_tokens_static` and `estimated_tokens_total`.

Workspace overrides (`{ws}/agents/constraints.md`, `coding-rules.md`, and
`agents/pipeline/validator-rules.md`) inherit the same static status when present.

## Priority Order

```
1. Contracts          ← hardest constraint, always wins
2. Platform Patterns  ← reusable canonical behavior
3. Project Docs       ← local overrides and service specifics
4. Domain Knowledge   ← business rules and workflows
5. Architecture / ADR ← context, not implementation
```

For non-code workstreams, equivalent first-class categories are also valid:
`product`, `requirement`, `design`, `quality`, `evidence`, and `runbook`.
If a retrieved doc doesn't fit one of these categories, drop it.

## Max Context Budget

The slot budget applies to **retrieved knowledge docs only** (contracts +
patterns + project + domain). Static engine/pack/workspace guidance is excluded
from that count, not from total prompt cost.

| Category | Max Docs | Max Sections per Doc |
|----------|----------|---------------------|
| Contracts | 2 | All sections |
| Patterns | 2 | Flow, Config, Failure, Rules |
| Project Docs | 2 | Purpose, Flow, Config Overrides, Failure |
| Domain | 1 | States, Transitions, Business Rules |
| Product / Requirement / Design / Quality / Evidence | 1-3 by workstream | Task-specific canonical sections |
| **Total (retrieved)** | **7** | — |
| Static engine/pack/workspace guidance | outside slot count; included in token total | component-scoped where supported |

## Section Slicing Rules

Never feed a full doc when only a section is needed.

| Task Focus | Sections to Include |
|-----------|-------------------|
| Implementing from scratch | Flow, Config, Failure Strategy, Rules |
| Debugging a failure | Failure Strategy, DLQ, Config |
| Reviewing code | Rules, Constraints, Config Overrides |
| Designing | Flow, Trade-offs, Used By |
| Product/BA work | Problem, Target User, Success Metric, Acceptance Criteria, Actor, Business Outcome |
| UX/design work | Flow, Accessibility, UX Writing, Edge Cases |
| QC/ops/evidence work | Evidence, Scope, Risk, Decision, Verified Facts, Open Questions |

## Slicing Example

Task: implement Kafka consumer

From `kafka-event-processing.md`, extract only:
```md
## Flow
## Default Config
## Failure Strategy
## Implementation Rules
```

Drop: `## Context`, `## DLQ Convention`, `## Used By`

## Ranked Output Schema

```json
{
  "contracts": [
    { "path": "platform/contracts/mqtt-topic-contract.md", "sections": ["all"] }
  ],
  "patterns": [
    { "path": "platform/patterns/kafka-event-processing.md", "sections": ["Flow", "Default Config", "Failure Strategy", "Implementation Rules"] },
    { "path": "platform/patterns/mqtt-routing.md", "sections": ["Flow", "Handler Registration", "Failure Strategy"] }
  ],
  "project": [
    { "path": "projects/surgery-service/services/kafka-consumer.md", "sections": ["all"] }
  ],
  "domain": [
    { "path": "domains/surgery/workflow.md", "sections": ["States", "Transitions", "Business Rules"] }
  ]
}
```

Pass this ranked, sliced context to [Prompt Builder](prompt-template.md).
