# Context Filter + Rank

## Purpose

Trim the retrieved doc list to the 5–7 most relevant, rank them by priority, and slice each doc to only the sections the agent needs. This is the most critical stage — it prevents context overload and enforces the priority order.

## Baseline (out-of-budget) Docs

`agents/constraints.md` and `agents/coding-rules.md` are **engine baseline**: they are always loaded into the main agent's context (effectively part of the system prompt — see `agents/system-prompt.md` Related section) for every intent. Any retrieval-map row that lists them (e.g. `intent_type=review`) is **tracking-only** — these entries are NOT counted toward the 5–7 doc budget defined below.

Workspace overrides (`{ws}/agents/constraints.md`, `{ws}/agents/pipeline/validator-rules.md`) inherit the same baseline status when present.

## Priority Order

```
1. Contracts          ← hardest constraint, always wins
2. Platform Patterns  ← reusable canonical behavior
3. Project Docs       ← local overrides and service specifics
4. Domain Knowledge   ← business rules and workflows
5. Architecture / ADR ← context, not implementation
```

If a retrieved doc doesn't fit one of these 5 categories, drop it.

## Max Context Budget

Budget applies to **retrieved knowledge docs only** (contracts + patterns + project + domain). Engine baseline docs (see "Baseline (out-of-budget) Docs" above) are excluded from this count.

| Category | Max Docs | Max Sections per Doc |
|----------|----------|---------------------|
| Contracts | 2 | All sections |
| Patterns | 2 | Flow, Config, Failure, Rules |
| Project Docs | 2 | Purpose, Flow, Config Overrides, Failure |
| Domain | 1 | States, Transitions, Business Rules |
| **Total (retrieved)** | **7** | — |
| Engine baseline (`agents/constraints.md`, `agents/coding-rules.md`) | out-of-budget | — |

## Section Slicing Rules

Never feed a full doc when only a section is needed.

| Task Focus | Sections to Include |
|-----------|-------------------|
| Implementing from scratch | Flow, Config, Failure Strategy, Rules |
| Debugging a failure | Failure Strategy, DLQ, Config |
| Reviewing code | Rules, Constraints, Config Overrides |
| Designing | Flow, Trade-offs, Used By |

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
