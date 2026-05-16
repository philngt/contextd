# a07 — Settings/Hook Override Map

> Source evidence: `2026-05-08-engine-bootstrap-wiki-template` (variant=agentic-engine)
> Inputs: raw.md Section 8 (hooks & settings) + a03-pattern-proposals.md + workspace patterns Default Config tables
> Status: **LIMITED ANALYSIS** — Section 3 (configs) + Section 8 (hooks/settings) skipped vì `--allow-configs` không pass khi ingest.

---

## Coverage limitation

raw.md Section 8 ghi `_(not analyzed — pass --allow-configs to include settings.json)_` `(workspaces/wiki/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md#section-8)`.

→ **a07 không thể compute concrete overrides** vì không có settings.json data. File này document **expected override surface** dựa vào structural analysis của commands/agents — actual override values cần `/code-analyze --allow-configs` rerun.

---

## Inferred override surface (no concrete values)

### Hook events expected

Based on engine pattern P-007 (5-stage subagent pipeline), hooks **có thể** được khai báo cho:

| Event | Expected matcher | Inferred purpose | Citation |
|-------|------------------|------------------|----------|
| `PreToolUse` | Bash, Edit, Write | Validator before destructive ops (per Pattern P-007 Stage 4 / wiki-reviewer concept) | `(.claude/agents/wiki-reviewer.md:L2-L5)` |
| `PostToolUse` | Edit, Write | Trigger `/update-wiki` auto-sync? OR emit trace events | `(.claude/commands/update-wiki.md:L1)`, `(agents/pipeline/observability.md:L1)` |
| `UserPromptSubmit` | (any) | Could enforce `/use-wiki` Stage 1 (planner) before main agent codes | `(.claude/commands/use-wiki.md:L1)` |
| `Stop` | (any) | Could emit final trace event for `/wiki-trace` consumption | `(.claude/commands/wiki-trace.md:L1)` |

**Note**: These are **HYPOTHETICAL** surface points — no evidence trong raw.md confirms hooks actually configured. Need `--allow-configs` rerun to validate.

### Permission patterns expected

Engine recommends following permission patterns based on observed tool usage in commands/agents:

| Layer | Tools used | Inferred allowlist |
|-------|-----------|---------------------|
| Sub-agents (read-only) | Read, Glob, Grep | `Read(*)`, `Glob`, `Grep(*)` |
| Sub-agent `wiki-context-selector` | + Write (current-task.md only) | + `Write(.claude/context/*.md)` |
| Sub-agent `wiki-curator` | + Edit, Write | + `Edit(workspaces/**)`, `Write(workspaces/**)` |
| Slash commands (engine) | Bash (git ops in `/code-analyze`) | `Bash(git rev-parse:*)`, `Bash(git log:*)`, `Bash(git status:*)` |
| Scripts | Python execution | `Bash(python:*)` for `scripts/*.py` |

**Citations**:
- `(.claude/agents/wiki-planner.md:L4)` tools=Read, Glob, Grep
- `(.claude/agents/wiki-context-selector.md:L4)` tools=Read, Glob, Grep, Write
- `(.claude/agents/wiki-curator.md:L4)` tools=Read, Edit, Write, Glob, Grep
- `(.claude/commands/code-analyze.md:L43-L46)` git CLI usage

### Env vars expected

| Name | Inferred purpose | Citation |
|------|------------------|----------|
| `CLAUDE_PROJECT_DIR` | Used by Bước 0 workspace resolution to find `.claude/wiki.json` | `(.claude/commands/code-analyze.md:L26-L36)` (via wiki_root rule) |
| (custom env vars cho user codebase) | Unknown — workspace-specific | N/A |

---

## Override comparison (when configs available)

When user reruns `/code-analyze --allow-configs`, expected analysis:

| Service | Pattern ref | Key | Default (pattern) | Actual (settings.json) | Reason | Source |
|---------|-------------|-----|-------------------|------------------------|--------|--------|
| _(populate after rerun)_ | _(P-XXX)_ | _(config-key)_ | _(value-in-pattern-doc)_ | _(value-in-settings.json)_ | _(commit/comment-explanation)_ | _(file:L..)_ |

---

## Workspace `wiki` Default Config tables

Workspace `wiki` `{ws}/platform/patterns/` empty → KHÔNG có default config tables để compare. Override map này sẽ populate sau khi:

1. `/evidence-apply` create `{ws}/platform/patterns/{P-001..P-008}.md` files với "Default Config" sections (per `templates/pattern.md` schema).
2. User reruns `/code-analyze --allow-configs` → new evid-id `refresh-wiki-template-{date}` → CORE-AGENTIC re-runs với Section 3/8 populated.
3. Re-run `/evidence-analyze --id {new-evid} --prompt a07` → concrete override map.

---

## Recommendation

### Block apply of a07-derived doc?
**NO** — a07 hiện chưa có concrete data để generate `{ws}/projects/engine/services/{service}.md` "Config Overrides" tables. Apply phase nên **skip Config Overrides sections** với marker `_(populate after --allow-configs rerun)_`.

### Next steps
1. **Now**: continue với `/evidence-qa` cho 24 questions trong 04-questions.md. Apply patterns + contracts + service docs.
2. **Later**: rerun `/code-analyze --ref . --variant agentic-engine --allow-configs` → tạo evid-id mới `refresh-wiki-template-{date}` → re-run a07 với Section 3/8 populated.
3. **Future**: when sub-agents proliferate (workspace với apps thực), tools allowlist principle (C-008a candidate, currently deferred per G-009) có thể formalize vào a07-style override map cho permission allowlist.

---

## Notes for `/evidence-apply`

- a07 trong phiên này = **placeholder document** — không có concrete override values.
- `{TODO: ask expert}` markers absent vì user explicit chose to skip configs (G-008 NICE-TO-HAVE).
- Service docs from a05 (G2 wiki-usage, G6 evidence-pipeline) reference hook potential — apply phase nên include note "hooks not analyzed in this evidence".
- Não block evidence-apply (G-008 = nice-to-have severity).
