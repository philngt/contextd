# pack-operator-steering

Agent-operator steering pack for practical context audits, drift checks, remediation plans, decision ledgers, handoff quality, and workflow mental models.

## When to enable

Workspace opts in by adding `- pack-operator-steering` under `## Packs` in `workspaces/{ws}/workspace.md`.

Enable when the workspace needs:
- Operators to inspect whether an agent has enough context before work continues.
- Drift checks against decisions, assumptions, risks, and accepted defaults.
- Remediation plans that name root cause, owner, acceptance criteria, and verification method.
- Durable handoff briefs for long-running agent work.

## What it adds

- **Constraints** (`agents/constraints.md`) - hard gates for evidence, root cause, decisions, handoffs, and stop/continue calls.
- **Working rules** (`agents/coding-rules.md`) - practical output conventions for operator-facing reports.
- **Common pitfalls** (`agents/common-pitfalls.md`) - repeated failure modes for agent steering.
- **Templates** (`templates/`) - context audit, drift report, remediation plan, decision note, handoff brief, and workflow mental model.
- **Retrieval map** (`agents/pipeline/retrieval-map.md`) - component to workspace/pack docs mapping.
- **Prompt overrides** (`agents/pipeline/prompt-overrides.md`) - self-check additions for active tasks.

## Components declared

- `context-audit`
- `drift-check`
- `remediation-planning`
- `decision-ledger`
- `handoff-quality`
- `workflow-mental-model`

## Conflicts with

(none)

## Notes

This pack borrows the practical audit shape from operator-facing steering workflows, but it has no runtime dependency on WOAFC or any `.woafc/project/` store. `contextd` remains the build substrate; the pack only adds deterministic docs, templates, and validation hints.

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)
