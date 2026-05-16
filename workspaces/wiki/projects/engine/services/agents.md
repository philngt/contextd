# Service: agents (sub-agents catalog)

## Purpose

Catalog 5 sub-agents định nghĩa trong `.claude/agents/` của engine. Mỗi sub-agent có frontmatter conform contract `sub-agent-frontmatter-schema.md` (required: name, description, tools, model).

## Sub-agent inventory

| Name | Role | Tools | Model | Invoked by | Source |
|------|------|-------|-------|------------|--------|
| `wiki-planner` | Phân tích task, xác định patterns/contracts/domain/components cần áp dụng | Read, Glob, Grep | sonnet | `/use-wiki` Stage 1 | `.claude/agents/wiki-planner.md` |
| `wiki-context-selector` | Map intent JSON → file wiki cụ thể, slice section, ghi `current-task.md` | Read, Glob, Grep, Write | sonnet | `/use-wiki` Stage 2 | `.claude/agents/wiki-context-selector.md` |
| `wiki-plan-reviewer` | Review intent + context retrieved, APPROVED/BLOCK gate | Read, Grep, Glob | sonnet | `/use-wiki` Stage 2.5 | `.claude/agents/wiki-plan-reviewer.md` |
| `wiki-curator` | Edit wiki khi code/evidence change — pattern/contract/service/ADR | Read, Edit, Write, Glob, Grep | sonnet | `/update-wiki`, `/rebase-wiki`, `/evidence-apply` | `.claude/agents/wiki-curator.md` |
| `wiki-reviewer` | Đối chiếu code output vs context theo `validator-rules.md` (read-only) | Read, Grep, Glob | sonnet | `/use-wiki` Stage 4 (optional) | `.claude/agents/wiki-reviewer.md` |

## Tools allowlist principle (observed, not yet contract — see G-009)

| Role | Tools pattern |
|------|---------------|
| Read-only roles (planner, plan-reviewer, reviewer) | `Read, Glob, Grep` |
| Read + write context-task (context-selector) | `Read, Glob, Grep, Write` (write privilege scoped to `.claude/context/`) |
| Write roles (curator) | `Read, Edit, Write, Glob, Grep` (write privilege scoped to `{ws}/...`) |

> Sample size = 5. Defer formalize thành contract C-008a until sample ≥ 8.

## Invocation patterns

```
/use-wiki:
  Stage 1: planner
  Stage 2: context-selector
  Stage 2.5: plan-reviewer (BLOCKING gate)
  Stage 3: main agent (NOT subagent)
  Stage 4: reviewer (optional, read-only)

/update-wiki, /rebase-wiki, /evidence-apply:
  delegate to: wiki-curator
  fallback: --inline (main agent direct edit, mất 1 safety layer)
```

## Frontmatter convention (per contract `sub-agent-frontmatter-schema.md`)

```yaml
---
name: {kebab-case}                  # MUST match filename
description: |
  {Role 1 line}
  DÙNG KHI {positive trigger}
  KHÔNG DÙNG để {negative trigger / scope constraint}
tools: {comma-separated list}
model: sonnet                       # default
---
```

5/5 sub-agents follow `DÙNG KHI/KHÔNG DÙNG` convention (recommended, non-binding).

## Config

```yaml
default_model: sonnet                       # all 5 sub-agents
description_convention: "DÙNG KHI ... KHÔNG DÙNG ..."
required_frontmatter_fields: [name, description, tools, model]
```

## Config Overrides

| Parameter | Platform Default | This Service | Reason |
|-----------|-----------------|--------------|--------|
| _(none — engine-level)_ | | | |

## Failure Handling

| Scenario | Action |
|----------|--------|
| Sub-agent file missing required frontmatter | Linter reject; runtime invocation fail |
| Tool used not in `tools` allowlist | Runtime error |
| Sub-agent unavailable trong runtime | Calling command STOP với `CURATOR UNAVAILABLE` (or relevant) |
| `wiki-context-selector` write outside `.claude/context/` | Tools scope violation |
| `wiki-curator` write outside `{ws}/` | Workspace isolation violation |

## Notes

- 5 sub-agents read-mostly, 2 có write privileges (context-selector, curator).
- Stage 3 Builder = main agent (NOT subagent) — cần full Edit/Write capability cho code generation.
- Stage 4 reviewer là OPTIONAL; recommended cho task wiki-aware để catch context drift.
- Sub-agents define theo Claude Code Agent SDK frontmatter spec.

## Related

- Contract: [../../platform/contracts/sub-agent-frontmatter-schema.md](../../platform/contracts/sub-agent-frontmatter-schema.md)
- Pattern: [../../platform/patterns/multi-stage-subagent-pipeline.md](../../platform/patterns/multi-stage-subagent-pipeline.md) (5-stage flow uses 4 of 5 sub-agents)
- Service: [wiki-usage.md](wiki-usage.md) (`/use-wiki`, `/update-wiki`, `/rebase-wiki` invoke sub-agents)
- Service: [evidence-pipeline.md](evidence-pipeline.md) (`/evidence-apply` invokes wiki-curator)
- Engine source: `.claude/agents/wiki-{planner,context-selector,plan-reviewer,curator,reviewer}.md`
- Engine spec: `agents/pipeline/multi-agent-pipeline.md` (full I/O schema)
- Source: F-017g, evidence `2026-05-08-engine-bootstrap-wiki-template`
