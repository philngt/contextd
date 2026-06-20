# Contract: sub-agent-frontmatter-schema

## Rule

Mọi file trong `.claude/agents/` PHẢI có frontmatter YAML với required fields:

```yaml
---
name: {kebab-case}                  # MUST match filename (without .md)
description: {1-3 sentence trigger}
tools: {tool-list-comma-separated}  # vd "Read, Glob, Grep"
model: {haiku|sonnet|opus}          # default sonnet
---
```

### Recommendation (non-binding) — `description` convention

`description` SHOULD chứa 2 phần:
- "DÙNG KHI X" — positive trigger (when to invoke this agent).
- "KHÔNG DÙNG để Y" — negative trigger / scope constraint.

Convention non-binding cho phép agents simple-scope dùng single sentence description.

### Tools allowlist principle (DEFERRED — see G-009)

Observation từ 4 sample agents:
- Read-only roles (planner, reviewer): `Read, Grep, Glob`
- Read-only + write context-task (context-selector): `Read, Glob, Grep, Write`
- Write roles (curator): `Read, Edit, Write, Glob, Grep`

Sample size (4) chưa đủ để formalize tools allowlist principle thành contract C-008a. Defer until ≥ 8 sub-agents (G-009).

## Observed evidence

4/4 sub-agents conform required fields:
- ✅ `contextd-planner`: name, description (DÙNG KHI/KHÔNG DÙNG), tools=`Read, Glob, Grep`, model=sonnet `(.claude/agents/contextd-planner.md:L2-L5)`
- ✅ `contextd-context-selector`: tools=`Read, Glob, Grep, Write` (write privilege cho current-task.json artifact adapter) `(.claude/agents/contextd-context-selector.md:L2-L5)`
- ✅ `contextd-curator`: tools=`Read, Edit, Write, Glob, Grep` (write role) `(.claude/agents/contextd-curator.md:L2-L5)`
- ✅ `contextd-reviewer`: `(.claude/agents/contextd-reviewer.md:L2-L5)`

## Counter-examples

_(none — 4/4 conform)_

## Validator behavior

- Missing required field (name/description/tools/model) → linter reject.
- Filename không match `name` field → reject.
- Tools list claim sai tool name → runtime error khi invoke.

## Future evolution (C-008a candidate)

Khi sample size sub-agents ≥ 8, revisit formalize tools allowlist principle:
- Required: read-only roles MUST NOT have Edit/Write trong tools.
- Required: write roles MUST declare scope (workspace path patterns).

## Related

- Contract: `slash-command-naming.md` (similar kebab-case convention)
- Source: q-014, evidence `2026-05-08-engine-bootstrap-wiki-template`
