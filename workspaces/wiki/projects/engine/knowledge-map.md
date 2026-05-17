# Knowledge Map — engine

> Per-project knowledge map cho project `engine` trong workspace `wiki`. Project `engine` là self-referential — document chính engine repo (wiki-template).

## Project context

Project `engine` document chính wiki-template engine: 19 slash commands + 5 sub-agents + 16 pipeline spec docs + 22 templates. Self-referential workspace per ADR `../../decisions/003-self-referential-engine-workspace.md`.

Boundary rule:
- **Engine spec docs** (`agents/pipeline/*.md`, `agents/coding-rules.md`, etc.) — describe HOW engine works internally (architecture; audience = engine maintainer).
- **Platform patterns** (`{ws}/platform/patterns/*.md`) — describe WHAT to apply (action-oriented; audience = engine USER).
- **Service docs trong project này** — describe specific commands/agents (entry-points + flow + failure handling).

## Services

### Command groups (entry-points)

| Service doc | Covers | Pattern refs |
|-------------|--------|--------------|
| [services/workspace-ops.md](services/workspace-ops.md) | `/wiki-setup`, `/wiki-detect`, `/switch-workspace`, `/new-workspace`, `/list-workspaces` | P-001 workspace-resolve, P-002 askuser-confirm |
| [services/wiki-usage.md](services/wiki-usage.md) | `/use-wiki`, `/update-wiki`, `/rebase-wiki` | P-007 multi-stage-pipeline |
| [services/codebase-analysis.md](services/codebase-analysis.md) | `/code-analyze` | P-001/P-002/P-003/P-004/P-008 |
| [services/reporting.md](services/reporting.md) | `/wiki-report` | P-001 |
| [services/observability.md](services/observability.md) | `/wiki-trace`, `/wiki-eval`, `/wiki-viz` | P-001 |
| [services/evidence-pipeline.md](services/evidence-pipeline.md) | `/evidence-ingest`, `/obsidian-ingest`, `/evidence-analyze`, `/evidence-qa`, `/evidence-apply` | P-005, P-006, P-008 + contracts C-001..C-014 |

### Sub-agents

| Doc | Covers |
|-----|--------|
| [services/agents.md](services/agents.md) | wiki-planner, wiki-context-selector, wiki-plan-reviewer, wiki-curator, wiki-reviewer |

## Patterns applied (workspace-level)

Mọi service trong project `engine` apply ≥ 1 pattern từ:

- [`workspace-resolve-step0`](../../platform/patterns/workspace-resolve-step0.md) — universal Step 0 cho mọi command.
- [`askuser-confirm-preview`](../../platform/patterns/askuser-confirm-preview.md) — pattern preview/confirm UX.
- [`secrets-blocklist-gate`](../../platform/patterns/secrets-blocklist-gate.md) — config guard pre-read.
- [`redaction-post-pass`](../../platform/patterns/redaction-post-pass.md) — secret scan post-build.
- [`evidence-state-machine`](../../platform/patterns/evidence-state-machine.md) — DAG transition tracking.
- [`citation-rule`](../../platform/patterns/citation-rule.md) — citation format invariant.
- [`multi-stage-subagent-pipeline`](../../platform/patterns/multi-stage-subagent-pipeline.md) — 5-stage `/use-wiki` flow.
- [`variant-discriminated-dispatcher`](../../platform/patterns/variant-discriminated-dispatcher.md) — variant routing.

## Contracts applied

- [`evid-id-format`](../../platform/contracts/evid-id-format.md)
- [`evidence-state-machine-transitions`](../../platform/contracts/evidence-state-machine-transitions.md)
- [`citation-format`](../../platform/contracts/citation-format.md)
- [`evidence-file-layout`](../../platform/contracts/evidence-file-layout.md)
- [`raw-md-section-structure`](../../platform/contracts/raw-md-section-structure.md)
- [`source-yaml-schema`](../../platform/contracts/source-yaml-schema.md)
- [`slash-command-naming`](../../platform/contracts/slash-command-naming.md)
- [`sub-agent-frontmatter-schema`](../../platform/contracts/sub-agent-frontmatter-schema.md)

## Project-level decisions

_(none yet — workspace-level decisions trong `{ws}/decisions/` cover engine-wide concerns.)_

## Thesis

- [THESIS](THESIS.md) — canonical project thesis and non-negotiables for engine governance.

## Related

- Workspace ADRs: [`../../decisions/`](../../decisions/)
- Engine source: `agents/`, `.claude/commands/`, `.claude/agents/`, `templates/` (engine repo, not in `{ws}/`)
- Source: F-017, evidence `2026-05-08-engine-bootstrap-wiki-template`
