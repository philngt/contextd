# Pattern: multi-stage-subagent-pipeline

> Pattern doc — apply per `/use-wiki` flow. **Note**: NOT marked as flagship in patterns-index (per ADR 003 — workspace user override during Q&A q-007).

## Context

Khi user task implement_feature / fix_bug / design / incident / review wiki-aware code, naïvely throw all wiki vào prompt → noise, hallucination, ignored knowledge. Pattern multi-stage subagent pipeline filters, ranks, and validates context trước khi Builder agent thấy.

5-stage flow (+ optional Stage 4) reused trong `/use-wiki` command.

## Flow

```
User Task
   ↓
[Stage 0] Main agent              → resolve workspace + wiki_root
   ↓                                (apply pattern workspace-resolve-step0)
[Stage 1] wiki-planner            → parse intent → intent JSON
   ↓                                (sub-agent A-001)
[Stage 2] wiki-context-selector   → retrieve + filter + slice
   ↓                                → ghi {project_dir}/.claude/context/current-task.md
   ↓                                (sub-agent A-002)
[Stage 2.5] wiki-plan-reviewer    → APPROVED / BLOCK gate
   ↓                                (sub-agent A-003 — blocking gate)
[Stage 3] Main agent (Builder)    → đọc current-task.md, code theo prompt-template.md
   ↓                                (no subagent — main agent)
[Stage 4] wiki-reviewer (optional)→ check code vs context theo validator-rules.md
   ↓                                (sub-agent A-005 — read-only review)
Output
```

1. **Stage 0**: main agent applies pattern `workspace-resolve-step0.md` — establish workspace context.
2. **Stage 1**: invoke `wiki-planner` subagent với task description. Output: intent JSON theo `agents/pipeline/task-to-docs-map.md` schema.
3. **Stage 2**: invoke `wiki-context-selector` với intent JSON + `agents/pipeline/task-to-docs-map.md` rules. Output: `{project_dir}/.claude/context/current-task.md` (sliced wiki context).
4. **Stage 2.5**: invoke `wiki-plan-reviewer` với intent + current-task.md. Output: APPROVED / BLOCK + reasons.
5. **Stage 3**: main agent (Builder) — đọc current-task.md, code theo `agents/pipeline/prompt-template.md`. KHÔNG subagent (main agent có full file edit capability).
6. **Stage 4** (optional): invoke `wiki-reviewer` — check code vs context theo `validator-rules.md`. Output: violation report (read-only, KHÔNG sửa code).

On Stage 2.5 BLOCK: STOP, KHÔNG tiếp tục Stage 3. User phải fix gap (vd add evidence, update wiki) rồi retry.

## Default Config

```yaml
# Stage definitions
stages:
  - n: 0
    name: workspace_resolve
    actor: main_agent
    blocking: true
  - n: 1
    name: planner
    actor: subagent_wiki_planner
    blocking: true
  - n: 2
    name: context_selector
    actor: subagent_wiki_context_selector
    blocking: true
  - n: 2.5
    name: plan_reviewer
    actor: subagent_wiki_plan_reviewer
    blocking: true                       # BLOCK gate
    on_block: stop_pipeline
  - n: 3
    name: builder
    actor: main_agent
    blocking: true
  - n: 4
    name: reviewer
    actor: subagent_wiki_reviewer
    blocking: false                      # optional
    output_only: violation_report

# Trace emission
emit_trace: true
trace_dir: ".claude/runs/{run_id}/"
trace_schema: "templates/run-trace.schema.json"
```

## Failure Strategy

| Scenario | Action |
|----------|--------|
| Stage 0 workspace resolve fail | STOP (per pattern `workspace-resolve-step0.md`) |
| Stage 1 planner fails to parse intent | Re-prompt with reminder; vẫn fail → user clarify task |
| Stage 2 context-selector returns empty | Warn user "wiki has no relevant knowledge for this task"; allow opt-in proceed |
| Stage 2.5 BLOCK | STOP, output reasons; user fix gap → retry pipeline |
| Stage 3 Builder code violates context | Stage 4 (nếu enabled) catches; else manual review |
| Stage 4 violations | Output report; user decide accept/fix |

## Implementation Rules

- Stage 2.5 gate là blocking — BLOCK → STOP, không tiếp tục Stage 3.
- Stage 4 optional nhưng recommended cho task wiki-aware (validator catches drift).
- Sub-agents tools allowlist (per contract `sub-agent-frontmatter-schema.md`):
  - planner / context-selector / plan-reviewer / reviewer = read-only (Read, Glob, Grep)
  - context-selector = + Write (cho current-task.md only)
- Trace emitted to `.claude/runs/{run_id}/` cho `/wiki-trace` consume.
- Stage 3 Builder = main agent — NOT subagent (cần full Edit/Write capability).

## Override Points

- Stage 4 `enabled` flag — workspace có thể disable nếu validator overhead không justify.
- `trace_dir` location — default `.claude/runs/`, có thể relocate.
- KHÔNG override: stage order, Stage 2.5 blocking semantic.

## Anti-patterns

- ❌ Skip Stage 1 (planner) — Builder thấy raw task, hallucinate scope.
- ❌ Skip Stage 2.5 (plan-reviewer) — Sai sót lọt xuống Builder, fix tốn token gấp 5–10×.
- ❌ Dump full wiki vào Stage 3 prompt thay vì Stage 2 sliced context.
- ❌ Stage 4 reviewer auto-fix code — review must be read-only.
- ❌ Cache `.claude/context/current-task.md` across runs — stale context.

## Used By

- `/use-wiki` command (`.claude/commands/use-wiki.md`) — primary implementation.
- Engine specs:
  - `agents/pipeline/README.md` (Section "Pipeline (5 stage)")
  - `agents/pipeline/multi-agent-pipeline.md` (full I/O schema)
  - `agents/pipeline/PIPELINE-VISUAL.md` (Mermaid diagram)
  - `agents/pipeline/task-to-docs-map.md` (Stage 1 output schema)
  - `agents/pipeline/task-to-docs-map.md` (Stage 2 input rules)
  - `agents/pipeline/context-filter.md` (Stage 2 ranking rules)
  - `agents/pipeline/prompt-template.md` (Stage 3 output template)
  - `agents/pipeline/validator-rules.md` (Stage 4 rules)

## Related

- Pattern: `workspace-resolve-step0.md` (Stage 0 invariant)
- Contract: `../contracts/sub-agent-frontmatter-schema.md` (sub-agent definitions)
- ADR: `../../decisions/003-self-referential-engine-workspace.md` (boundary giữa engine spec docs và platform pattern docs)
- Source: q-007, evidence `2026-05-08-engine-bootstrap-wiki-template`

> **Note**: Per user override during Q&A (q-007), pattern này NOT marked as flagship trong `{ws}/patterns-index.md`. Position: alphabetical normal (between `evidence-state-machine` và `redaction-post-pass`). KHÔNG cross-reference từ `{ws}/workspace.md`.
