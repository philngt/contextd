# a02 — Command & Agent Map

> Source evidence: `2026-05-08-engine-bootstrap-wiki-template` (variant=agentic-engine)
> Inputs: `raw.md` Section 4, 5, 6, 7 + workspace `wiki` (empty — no existing service docs)

Workspace baseline: `{ws}/projects/` rỗng → mọi entry-point status = `[NEW]`.

## Entry-points (20 slash commands)

### E-001 — `/contextd-setup`  [NEW]
- **type**: slash-command
- **purpose**: Tạo `.claude/wiki.json` cho codebase hiện tại; detect project name + components và pre-fill config `(raw.md#section-4)`
- **inputs**: none (interactive — AskUserQuestion driven) `(.claude/commands/contextd-setup.md:L1)`
- **outputs**: creates `<cwd>/.claude/wiki.json` + workspace skeleton trong `{wiki_root}/workspaces/{name}/`
- **calls**: template `templates/wiki-local.json`, `templates/workspace.md`
- **called_by**: (top-level user entry — onboard codebase mới)

### E-002 — `/contextd-detect`  [NEW]
- **type**: slash-command
- **purpose**: Validate `.claude/wiki.json` của codebase + check workspace tồn tại + scan dependency để propose update `(raw.md#section-4)`
- **inputs**: none
- **outputs**: report only (no file changes)
- **calls**: reads `.claude/wiki.json`, `{wiki_root}/workspaces/{ws}/workspace.md`
- **called_by**: user khi `/contextd-use` lỗi resolve

### E-003 — `/switch-workspace {name}`  [NEW]
- **type**: slash-command
- **purpose**: Đổi `workspace` field trong `<cwd>/.claude/wiki.json` sang workspace khác `(raw.md#section-4)`
- **inputs**: `{name}` (positional)
- **outputs**: edits `.claude/wiki.json#workspace`
- **calls**: validate `{wiki_root}/workspaces/{name}/workspace.md` tồn tại trước khi đổi
- **called_by**: user khi cùng codebase phục vụ nhiều domain

### E-004 — `/new-workspace {name}`  [NEW]
- **type**: slash-command
- **purpose**: Scaffold workspace mới trong `{wiki_root}/workspaces/{name}/` từ template `(raw.md#section-4)`
- **inputs**: `{name}` (positional)
- **outputs**: creates `workspaces/{name}/{workspace.md, patterns-index.md, platform/, projects/, domains/, runbooks/, decisions/}`; updates `patterns-index.md`
- **calls**: templates `workspace.md`, derived `patterns-index.md` `(.claude/commands/new-workspace.md:L63)`
- **called_by**: user khi join công ty/dự án mới

### E-005 — `/list-workspaces`  [NEW]
- **type**: slash-command
- **purpose**: In bảng mọi workspace + đánh dấu workspace của codebase hiện tại `(raw.md#section-4)`
- **inputs**: none
- **outputs**: report only
- **calls**: scan `{wiki_root}/workspaces/*/workspace.md`

### E-006 — `/contextd-use`  [NEW]
- **type**: slash-command
- **purpose**: Chạy 5-stage pipeline (planner → context-selector → plan-reviewer → main agent code → reviewer) trước khi viết code wiki-aware `(raw.md#section-4)`
- **inputs**: task description (free-text)
- **outputs**: invokes 5 sub-agents pipeline; writes `.claude/context/current-task.md`; emits trace `.claude/runs/{run_id}/`
- **calls**:
  - sub-agent `wiki-planner` (E-A1) → Stage 1
  - sub-agent `wiki-context-selector` (E-A2) → Stage 2
  - sub-agent `wiki-plan-reviewer` (E-A3) → Stage 2.5
  - main agent (Builder) → Stage 3
  - sub-agent `wiki-reviewer` (E-A5) → Stage 4 (optional)
  - templates: `prompt-template.md` (Stage 3 output template)
- **called_by**: user trước MỌI task implement_feature/fix_bug/design/incident/review

### E-007 — `/contextd-update`  [NEW]
- **type**: slash-command
- **purpose**: Sync wiki với code đã thay đổi (git diff → curator áp dụng) `(raw.md#section-4)`
- **inputs**: optional `--scope`
- **outputs**: edits files trong `{ws}/...` qua wiki-curator subagent
- **calls**: sub-agent `wiki-curator` (E-A4)
- **called_by**: user sau khi code merge

### E-008 — `/contextd-rebase`  [NEW]
- **type**: slash-command
- **purpose**: Quét wiki vs codebase thực tế để vá mọi chỗ wiki nói khác code chạy `(raw.md#section-4)`
- **inputs**: none
- **outputs**: edits files trong `{ws}/...` qua wiki-curator
- **calls**: sub-agent `wiki-curator` (E-A4)
- **called_by**: user định kỳ (hằng tuần/tháng) hoặc khi nghi wiki lỗi thời

### E-009 — `/code-analyze`  [NEW]
- **type**: slash-command
- **purpose**: Snapshot metadata codebase → ingest vào evidence pipeline với `source_type=code` (variant=code|agentic-engine) → sinh proposals patterns/contracts/services/ADRs `(raw.md#section-4)`
- **inputs**: `--ref`, `--scope`, `--bundle`, `--label`, `--skip-analyze`, `--allow-configs`, `--with-drafts`, `--variant` (NEW)
- **outputs**: creates `{ws}/evidence/sources/{evid-id}/{raw.md, source.yaml, raw.normalized.md?}`; auto-trigger `/evidence-analyze` (unless `--skip-analyze`)
- **calls**:
  - templates `code-snapshot.md` (variant=code) hoặc `agentic-engine-snapshot.md` (variant=agentic-engine), `evidence-source.yaml`
  - command `/evidence-analyze` (Bước 7)
- **called_by**: user khi onboard codebase legacy / refresh / bootstrap

### E-010 — `/contextd-report`  [NEW]
- **type**: slash-command
- **purpose**: Sinh 1 file HTML self-contained tổng hợp toàn workspace (Overview / Architecture / Contracts / Patterns / Domains / ADRs / Runbooks) `(raw.md#section-4)`
- **inputs**: optional filters
- **outputs**: HTML report file
- **calls**: templates `report-html-skeleton.html`, `report-fragments.html`, `report-prompts.md`

### E-011 — `/contextd-trace {run_id}`  [NEW]
- **type**: slash-command
- **purpose**: Render Markdown timeline 1 run pipeline (5 stage) từ trace JSON dưới `.claude/runs/{run_id}/` `(raw.md#section-4)`
- **inputs**: `{run_id}` (positional)
- **outputs**: report only (markdown)
- **calls**: schema `templates/run-trace.schema.json`, script `scripts/render_trace.py`

### E-012 — `/contextd-eval`  [NEW]
- **type**: slash-command
- **purpose**: Aggregate trace nhiều run → báo cáo Markdown: hallucination rate, top knowledge gaps, plan-block rate, violation hotspots `(raw.md#section-4)`
- **inputs**: optional date range
- **outputs**: eval report markdown; per-workspace `{ws}/eval/golden-tasks/`
- **calls**: schema `templates/run-trace.schema.json`, template `templates/task-scorecard.md`

### E-013 — `/contextd-viz`  [NEW]
- **type**: slash-command
- **purpose**: HTML viewer + live watch của pipeline trace — observability companion `(raw.md#section-4.5)`
- **inputs**: optional `{run_id}`
- **outputs**: HTML viewer file
- **calls**: scripts/templates observability-related
- **note**: ⚠ vắng mặt trong `.claude/commands/README.md` index Section "Pipeline observability" mặc dù file tồn tại — README stale `(.claude/commands/README.md:L57-L59)`

### E-014 — `/evidence-ingest`  [NEW]
- **type**: slash-command
- **purpose**: Pull raw data từ MCP / API / paste / code vào `{ws}/evidence/sources/{evid-id}/` (immutable sau ingest) `(raw.md#section-4)`
- **inputs**: `--source {mcp|api|paste|code}`, `--label`, `--ref`, source-specific args
- **outputs**: creates `{ws}/evidence/sources/{evid-id}/{raw.*, source.yaml}`; updates `{ws}/evidence/_index.md`
- **calls**: templates `evidence-source.yaml`, `evidence-index.md`; conventions `raw-storage-conventions.md`, `code-snapshot-conventions.md`
- **called_by**: user when external sources ready; `/code-analyze` dưới capô (variant=code)

### E-015 — `/obsidian-ingest`  [NEW]
- **type**: slash-command
- **purpose**: Batch wrapper quanh `/evidence-ingest --source paste` cho Obsidian vault: scan folder, parse frontmatter, dedup, redaction pre-check `(raw.md#section-4)`
- **inputs**: `--vault`, `--folder`, etc.
- **outputs**: batch ingest từ Obsidian vault → multiple `{ws}/evidence/sources/{id}/`
- **calls**: command `/evidence-ingest`
- **called_by**: user maintain Second Brain trong Obsidian

### E-016 — `/evidence-analyze`  [NEW]
- **type**: slash-command
- **purpose**: Chạy CORE prompts sinh `analysis/{id}/`. Text: `[01,02,04,08]`. Code (variant=code): `[c01,c02,c03,c04,04,08]`. Code (variant=agentic-engine): `[a01,a02,a03,a04,04,08]` `(raw.md#section-4)`
- **inputs**: `--id`, `--prompt {03|05|06|07|09|10|c05|c06|c07|a05|a06|a07}`
- **outputs**: creates `{ws}/evidence/analysis/{id}/*.md`; transitions state `ingested → analyzed`
- **calls**: prompt specs `critical-analysis-prompts.md` (text), `code-analysis-prompts.md` (code + agentic-engine)
- **called_by**: `/code-analyze` Bước 7 (auto), user manually

### E-017 — `/evidence-qa`  [NEW]
- **type**: slash-command
- **purpose**: Q&A loop với user theo batches P0/P1/P2/P3, defer-to-expert option, sinh `verified-facts.md` khi xong `(raw.md#section-4)`
- **inputs**: `--id`
- **outputs**: creates `{ws}/evidence/qa/{id}/{recommendations.md, batches/, verified-facts.md, pending-external.md?}`; transitions state `analyzed → qa_in_progress → qa_done`
- **calls**: spec `qa-batching.md`; template `evidence-qa-recommendations.md`, `evidence-qa-answers.md`, `evidence-qa-todo.json`, `evidence-pending-external.md`; CORE C8/A8 (QA Recommender)
- **called_by**: user sau analyze

### E-018 — `/evidence-apply`  [NEW]
- **type**: slash-command
- **purpose**: Apply verified facts vào wiki docs với checkpoint/resume per-file. Router edit-vs-create theo `Affects:` path `(raw.md#section-4)`
- **inputs**: `--id`, `--mode {update|rebase}`, `--dry-run`
- **outputs**: edits files trong `{ws}/{platform,domains,projects,decisions,runbooks}/...`; transitions state `qa_done → applied`
- **calls**: sub-agent `wiki-curator` (E-A4); templates `service.md`, `pattern.md`, `adr.md`, `runbook.md`, `evidence-apply-checkpoint.json`, `evidence-manifest.yaml`
- **called_by**: user sau qa_done

### E-019 — `/README` (commands index)  [NEW]
- **type**: doc index (not invokable as slash-command — meta)
- **purpose**: Slash Commands index — tóm tắt 19 commands `(.claude/commands/README.md:L1)`
- **inputs**: n/a
- **outputs**: n/a (read-only doc)
- **note**: Stale — không có row cho `/contextd-viz` `(.claude/commands/README.md:L57-L59)`

## Sub-agents (5 agents)

### A-001 — `wiki-planner`  [NEW]
- **type**: subagent
- **role**: Phân tích task của user và xác định patterns, contracts, domain, components cần áp dụng theo wiki
- **tools allowed**: Read, Glob, Grep `(.claude/agents/wiki-planner.md:L4)`
- **model**: sonnet `(.claude/agents/wiki-planner.md:L5)`
- **invoked_by**: command `/contextd-use` Stage 1 (`E-006`) `(raw.md#section-5.1)`
- **output schema**: intent JSON `(agents/pipeline/intent-parser.md:L1)`

### A-002 — `wiki-context-selector`  [NEW]
- **type**: subagent
- **role**: Map intent JSON từ wiki-planner sang danh sách file wiki cụ thể, slice section liên quan, và ghi `.claude/context/current-task.md`
- **tools allowed**: Read, Glob, Grep, Write `(.claude/agents/wiki-context-selector.md:L4)`
- **model**: sonnet
- **invoked_by**: `/contextd-use` Stage 2 (sau `wiki-planner`)
- **calls**: spec `context-retrieval-map.md`, `context-filter.md`

### A-003 — `wiki-plan-reviewer`  [NEW]
- **type**: subagent
- **role**: Review intent JSON + context đã retrieve trước khi main agent code. Phát hiện sớm conflict/gap/pattern không tồn tại để chặn code sai
- **tools allowed**: Read, Grep, Glob `(.claude/agents/wiki-plan-reviewer.md:L4)`
- **model**: sonnet
- **invoked_by**: `/contextd-use` Stage 2.5 (gate trước Builder)
- **output**: APPROVED / BLOCK + reasons

### A-004 — `wiki-curator`  [NEW]
- **type**: subagent
- **role**: Cập nhật wiki sau khi code thay đổi — pattern mới, contract mới, service mới, ADR mới
- **tools allowed**: Read, Edit, Write, Glob, Grep `(.claude/agents/wiki-curator.md:L4)`
- **model**: sonnet
- **invoked_by**: commands `/contextd-update` (E-007), `/contextd-rebase` (E-008), `/evidence-apply` (E-018)

### A-005 — `wiki-reviewer`  [NEW]
- **type**: subagent
- **role**: Đối chiếu output của builder/main agent với contracts, patterns, domain rules trong `.claude/context/current-task.md` và `validator-rules.md`
- **tools allowed**: Read, Grep, Glob `(.claude/agents/wiki-reviewer.md:L4)`
- **model**: sonnet
- **invoked_by**: `/contextd-use` Stage 4 (optional, validator)
- **output**: violation report (no edits — read-only)

## System prompt docs (3 docs — not invokable subagents)

| Doc | Role | Citation |
|-----|------|----------|
| `agents/system-prompt.md` | Engine system prompt — workspace resolution, knowledge priority, hard constraints | `(agents/system-prompt.md:L1)` |
| `agents/coding-rules.md` | Engine universal coding rules — workspace có thể override | `(agents/coding-rules.md:L1)` |
| `agents/constraints.md` | Engine-level hard constraints — workspace có thể bổ sung | `(agents/constraints.md:L1)` |

## Cross-reference summary

- **5-stage `/contextd-use` pipeline**: E-006 invokes A-001 → A-002 → A-003 → main agent (no subagent) → A-005 (optional). `(raw.md#section-6.1)`
- **Wiki edit pipeline**: E-007/E-008/E-018 all delegate to A-004 (wiki-curator) — central edit authority. `(raw.md#section-4.2, section-4.6)`
- **Evidence ingest pipeline**: E-014 (generic) ← wrapped by E-015 (Obsidian batch) and E-009 (code/agentic-engine wrapper). All write to `{ws}/evidence/sources/{id}/`. `(raw.md#section-6.3)`
- **Evidence analyze→qa→apply chain**: E-016 → E-017 → E-018 sequential, dispatched by `source_type` + `code_variant`. `(raw.md#section-4.6)`
- **Observability sub-system**: E-011 / E-012 / E-013 độc lập với core flow, đọc `.claude/runs/{run_id}/` traces. E-013 missing from index README. `(raw.md#section-10, item 4)`

## Notes for downstream prompts

1. Workspace `wiki` empty → mọi entry-point `[NEW]` (a05 sẽ generate doc cho tất cả nếu user chọn 1-doc-per-command).
2. 19 commands là **engine-level** (không phải application services) — service doc grouping cần quyết định: 1 doc per command (verbose) hay group by category (5 groups: setup, usage, codebase-analysis, reporting, observability, evidence) hay 1 mega-doc tổng quan. → query trong `04-questions.md` P1.
3. 5 sub-agents có frontmatter `name/description/tools/model` chuẩn — đây là contract C-008 trong a04.
4. `/contextd-viz` orphaned trong README index — gap G-006 trong 08.
