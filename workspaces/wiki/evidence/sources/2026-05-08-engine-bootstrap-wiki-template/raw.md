# Agentic-Engine Snapshot — 2026-05-08-engine-bootstrap-wiki-template

> Source: agentic-coding engine tại `d:/tool/wiki-template/` @ git SHA `unmanaged-2064d55e2bd25900333b26deedc3a26205708fd9f0ba8d38a5b3827b59f160d0` (branch: `unmanaged`)
> Snapshotted at: 2026-05-08T00:00:00+07:00
> Scope: `agents/**/*.md`, `.claude/commands/**/*.md`, `.claude/agents/**/*.md`, `templates/**`, `README.md`, `CLAUDE.md`
> Variant: agentic-engine
>
> Đây là snapshot METADATA cho engine repo (markdown-heavy: slash commands, sub-agents, prompt templates), KHÔNG phải bản sao file. Mọi citation `(file:line)` trỏ về file thật trong repo (immutable tại tree-manifest sha trên).

---

## Section 1 — Engine metadata

- **Engine name**: Knowledge Wiki (`wiki-template`)
- **Purpose**: Single source of truth for system knowledge — consumed by both developers and AI agents, được tổ chức theo workspace vì user làm việc ở nhiều công ty/dự án độc lập. AI agents read this wiki as runtime context, not documentation. `(README.md:L1-L8)`
- **Mental model**: Wiki = engine (dùng chung) + N workspaces (mỗi nơi 1 sandbox). Active workspace là per-codebase, sống trong `<project>/.claude/wiki.json.workspace`. `(README.md:L10-L23)`
- **Top-level dirs**:
  - `agents/` — System prompt, coding rules, constraints, pipeline (intent → retrieval → filter → validate). Engine defaults áp dụng mọi workspace. `(README.md:L29)`
  - `templates/` — Skeleton cho workspace mới và doc mới. `(README.md:L30)`
  - `.claude/commands/` — Slash commands cho workflow wiki-aware. `(.claude/commands/README.md:L1-L8)`
  - `.claude/agents/` — Sub-agents (5 file: wiki-planner, wiki-context-selector, wiki-plan-reviewer, wiki-curator, wiki-reviewer).
  - `workspaces/` — N workspaces, mỗi cái có platform/domains/projects/decisions/runbooks. `(README.md:L18-L19)`
  - `scripts/` — Python scripts (lint-wiki, render_trace, validate, install-to-claude, build-report-with-dialog). _(out of default scope)_
- **Claude Code version target**: _(not stated)_
- **Stated purpose excerpt**: "Single source of truth for system knowledge — consumed by both developers and AI agents... Wiki = engine + N workspaces." `(README.md:L5-L23)`

---

## Section 2 — Dependencies

### MCP servers (`mcp.json` / `.mcp.json`)

_(none — no mcp.json or .mcp.json in repo root)_

### Runtime / script-tool deps

_(none — no package.json, pyproject.toml, requirements.txt at repo root in scope)_

> Note: `scripts/` dir contains Python scripts (`.py`) but không khai báo deps file ở root. Out of default scope.

### External integrations (inferred from commands/agents)

| Integration | Inferred from | Citation |
|-------------|---------------|----------|
| Obsidian (Second Brain vault) | `/obsidian-ingest` slash command — batch wrapper for Obsidian vault scan | `(.claude/commands/obsidian-ingest.md:L1)`, `(.claude/commands/README.md:L73)` |
| Confluence (mentioned, not implemented) | listed in evidence pipeline source examples | `(.claude/commands/README.md:L72)` |
| Linear (mentioned) | listed in evidence pipeline source examples | `(.claude/commands/README.md:L72)` |
| Slack (mentioned) | listed in evidence pipeline source examples | `(.claude/commands/README.md:L72)` |
| MCP (generic) | `source_type=mcp` first-class in evidence pipeline | `(agents/pipeline/critical-analysis-prompts.md:L1)`, `(templates/evidence-source.yaml:L6)` |
| HTTP API (generic) | `source_type=api` first-class | `(templates/evidence-source.yaml:L6-L7)` |
| Git CLI | `/code-analyze` uses `git rev-parse`, `git log`, `git status` | `(.claude/commands/code-analyze.md:L43-L46)` |

---

## Section 3 — Configs

_(Configs skipped — rerun with --allow-configs to include)_

**Config guard log**:
- Configs not read (--allow-configs not set): `settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, `.claude/wiki.json`, candidate `templates/wiki-global.json`, `templates/wiki-local.json` (templates — không phải config thực tế)

---

## Section 4 — Slash commands

19 commands trong `.claude/commands/`. Categorized theo `(.claude/commands/README.md)`:

### 4.1 Workspace setup & navigation `(.claude/commands/README.md:L12-L21)`

| Name | Purpose (1 line) | Inputs (args) | Outputs (state/file changes) | Mode | Citation |
|------|------------------|---------------|------------------------------|------|----------|
| `/wiki-setup` | Tạo `.claude/wiki.json` cho codebase hiện tại; detect project name + components và pre-fill config | none (interactive) | creates `<cwd>/.claude/wiki.json` + workspace skeleton | interactive | `(.claude/commands/wiki-setup.md:L1)`, `(.claude/commands/README.md:L16)` |
| `/wiki-detect` | Validate `.claude/wiki.json` của codebase + check workspace tồn tại + scan dependency để propose update | none | report only | auto | `(.claude/commands/wiki-detect.md:L1)`, `(.claude/commands/README.md:L17)` |
| `/switch-workspace` | Đổi `workspace` field trong `<cwd>/.claude/wiki.json` sang workspace khác | `{name}` (positional) | edits `.claude/wiki.json#workspace` | interactive | `(.claude/commands/switch-workspace.md:L1)`, `(.claude/commands/README.md:L18)` |
| `/new-workspace` | Scaffold workspace mới trong `{wiki_root}/workspaces/{name}/` từ template | `{name}` (positional) | creates `workspaces/{name}/` skeleton; updates patterns-index | interactive | `(.claude/commands/new-workspace.md:L1)`, `(.claude/commands/README.md:L19)` |
| `/list-workspaces` | In bảng mọi workspace + đánh dấu workspace của codebase hiện tại | none | report only | auto | `(.claude/commands/list-workspaces.md:L1)`, `(.claude/commands/README.md:L20)` |

### 4.2 Wiki usage (per-task pipeline) `(.claude/commands/README.md:L24-L31)`

| Name | Purpose | Inputs | Outputs | Mode | Citation |
|------|---------|--------|---------|------|----------|
| `/use-wiki` | Chạy 5-stage pipeline (planner → context-selector → plan-reviewer → main agent code → reviewer) trước khi viết bất kỳ code wiki-aware nào | task description | invokes 5 sub-agents; writes `.claude/context/current-task.md`; emits trace `.claude/runs/{run_id}/` | interactive | `(.claude/commands/use-wiki.md:L1)`, `(.claude/commands/README.md:L28)` |
| `/update-wiki` | Sync wiki với code đã thay đổi (git diff → curator áp dụng) | optional `--scope` | edits files trong `{ws}/...` qua wiki-curator subagent | interactive | `(.claude/commands/update-wiki.md:L1)`, `(.claude/commands/README.md:L29)` |
| `/rebase-wiki` | Quét wiki vs codebase thực tế để vá mọi chỗ wiki nói khác code chạy | none | edits files trong `{ws}/...` qua wiki-curator | interactive | `(.claude/commands/rebase-wiki.md:L1)`, `(.claude/commands/README.md:L30)` |

### 4.3 Codebase analysis `(.claude/commands/README.md:L34-L40)`

| Name | Purpose | Inputs | Outputs | Mode | Citation |
|------|---------|--------|---------|------|----------|
| `/code-analyze` | Snapshot metadata codebase → ingest vào evidence pipeline với `source_type=code` → sinh proposals patterns/contracts/services/ADRs | `--ref`, `--scope`, `--bundle`, `--label`, `--skip-analyze`, `--allow-configs`, `--with-drafts`, `--variant` (NEW) | creates `{ws}/evidence/sources/{evid-id}/` + analysis files | interactive | `(.claude/commands/code-analyze.md:L1)`, `(.claude/commands/README.md:L38)` |

### 4.4 Reporting `(.claude/commands/README.md:L44-L50)`

| Name | Purpose | Inputs | Outputs | Mode | Citation |
|------|---------|--------|---------|------|----------|
| `/wiki-report` | Sinh 1 file HTML self-contained tổng hợp toàn workspace (Overview / Architecture / Contracts / Patterns / Domains / ADRs / Runbooks) | optional filters | creates HTML output file | auto | `(.claude/commands/wiki-report.md:L1)`, `(.claude/commands/README.md:L48)` |

### 4.5 Pipeline observability `(.claude/commands/README.md:L54-L61)`

| Name | Purpose | Inputs | Outputs | Mode | Citation |
|------|---------|--------|---------|------|----------|
| `/wiki-trace` | Render Markdown timeline 1 run pipeline (5 stage) từ trace JSON dưới `.claude/runs/{run_id}/` | `{run_id}` | report only | auto | `(.claude/commands/wiki-trace.md:L1)`, `(.claude/commands/README.md:L58)` |
| `/wiki-eval` | Aggregate trace nhiều run → báo cáo Markdown: hallucination rate, top knowledge gaps, plan-block rate, violation hotspots | optional date range | creates eval report | auto | `(.claude/commands/wiki-eval.md:L1)`, `(.claude/commands/README.md:L59)` |
| `/wiki-viz` | (HTML viewer + live watch của pipeline trace) — observability companion | optional `{run_id}` | creates HTML viewer | auto | `(.claude/commands/wiki-viz.md:L1)` |

### 4.6 Evidence pipeline (raw → wiki) `(.claude/commands/README.md:L65-L77)`

| Name | Purpose | Inputs | Outputs | Mode | Citation |
|------|---------|--------|---------|------|----------|
| `/evidence-ingest` | Pull raw data từ MCP / API / paste / code vào `{ws}/evidence/sources/{evid-id}/` (immutable sau ingest) | `--source`, `--label`, `--ref` etc | creates `{ws}/evidence/sources/{evid-id}/{raw.*, source.yaml}` | interactive | `(.claude/commands/evidence-ingest.md:L1)`, `(.claude/commands/README.md:L72)` |
| `/obsidian-ingest` | Batch wrapper quanh `/evidence-ingest --source paste` cho Obsidian vault: scan folder, parse frontmatter, dedup, redaction pre-check | `--vault`, `--folder`, etc | batch ingest từ Obsidian vault | interactive | `(.claude/commands/obsidian-ingest.md:L1)`, `(.claude/commands/README.md:L73)` |
| `/evidence-analyze` | Chạy CORE prompts sinh `analysis/{id}/`. Text: `[01,02,04,08]`. Code: `[c01,c02,c03,c04,04,08]` | `--id`, `--prompt` | creates `{ws}/evidence/analysis/{id}/*.md` | auto | `(.claude/commands/evidence-analyze.md:L1)`, `(.claude/commands/README.md:L74)` |
| `/evidence-qa` | Q&A loop với user theo batches P0/P1/P2/P3, defer-to-expert option, sinh `verified-facts.md` khi xong | `--id` | creates `{ws}/evidence/qa/{id}/{recommendations.md, batches/, verified-facts.md}` | interactive | `(.claude/commands/evidence-qa.md:L1)`, `(.claude/commands/README.md:L75)` |
| `/evidence-apply` | Apply verified facts vào wiki docs với checkpoint/resume per-file. Router edit-vs-create theo `Affects:` path | `--id`, `--mode update`, `--dry-run` | edits files trong `{ws}/{platform,domains,projects,decisions,runbooks}/...` | interactive | `(.claude/commands/evidence-apply.md:L1)`, `(.claude/commands/README.md:L76)` |

### 4.7 Index command (meta)

| Name | Purpose | Citation |
|------|---------|----------|
| `/README` (in commands index) | Slash Commands index — tóm tắt 19 commands trên | `(.claude/commands/README.md:L1)` |

---

## Section 5 — Sub-agents & system prompts

### 5.1 Sub-agents trong `.claude/agents/` (5 sub-agents có frontmatter)

| Name | Role (1 line) | Tools allowed | When to use | Citation |
|------|---------------|---------------|-------------|----------|
| `wiki-planner` | Phân tích task của user và xác định patterns, contracts, domain, components cần áp dụng theo wiki | Read, Glob, Grep | DÙNG KHI bắt đầu một task mới (implement_feature, fix_bug, design, incident, review) trước bất kỳ retrieval hoặc code nào. KHÔNG DÙNG để sinh code hay đọc nhiều file. | `(.claude/agents/wiki-planner.md:L2-L5)` |
| `wiki-context-selector` | Map intent JSON từ wiki-planner sang danh sách file wiki cụ thể, slice section liên quan, và ghi `.claude/context/current-task.md` | Read, Glob, Grep, Write | DÙNG NGAY SAU wiki-planner. KHÔNG DÙNG để phân tích task hay sinh code. | `(.claude/agents/wiki-context-selector.md:L2-L5)` |
| `wiki-plan-reviewer` | Review intent JSON + context đã retrieve trước khi main agent code. Phát hiện sớm conflict/gap/pattern không tồn tại để chặn code sai | Read, Grep, Glob | DÙNG NGAY SAU wiki-context-selector và TRƯỚC khi main agent bắt đầu Implementation. KHÔNG DÙNG để review code đã sinh (đó là việc của wiki-reviewer). | `(.claude/agents/wiki-plan-reviewer.md:L2-L5)` |
| `wiki-curator` | Cập nhật wiki sau khi code thay đổi — pattern mới, contract mới, service mới, ADR mới | Read, Edit, Write, Glob, Grep | DÙNG KHI user gọi /update-wiki hoặc khi cần đồng bộ wiki sau merge. KHÔNG DÙNG để chỉnh code project. | `(.claude/agents/wiki-curator.md:L2-L5)` |
| `wiki-reviewer` | Đối chiếu output của builder/main agent với contracts, patterns, domain rules trong `.claude/context/current-task.md` và validator-rules.md | Read, Grep, Glob | DÙNG SAU KHI code đã được sinh, trước khi merge/commit. KHÔNG DÙNG để sửa code — chỉ báo cáo violation. | `(.claude/agents/wiki-reviewer.md:L2-L5)` |

> Tất cả 5 sub-agents declared `model: sonnet`.

### 5.2 System prompts trong `agents/` (system-prompt-style docs, no frontmatter)

| Name | Role (1 line) | Citation |
|------|---------------|----------|
| `system-prompt.md` | Engine system prompt — workspace resolution, knowledge priority order, hard constraints | `(agents/system-prompt.md:L1)` |
| `coding-rules.md` | Engine universal coding rules (Java, Kafka, MQTT examples) — workspace có thể override | `(agents/coding-rules.md:L1)` |
| `constraints.md` | Engine-level hard constraints — workspace có thể bổ sung tại `{ws}/agents/constraints.md` | `(agents/constraints.md:L1)` |

### 5.3 Pipeline definition docs trong `agents/pipeline/` (16 docs — see Section 6)

Các file pipeline KHÔNG phải sub-agent invokable; chúng là **specs** cho stages. Liệt kê đầy đủ ở Section 6.

---

## Section 6 — Pipeline stages / Modules

### 6.1 Pipeline 5 stages `(agents/pipeline/README.md:L27-L46)`

| Order | Stage | Role | Defined in | Citation |
|-------|-------|------|------------|----------|
| 0 | Main agent (Stage 0) | Resolve workspace + wiki_root | `agents/system-prompt.md` | `(agents/pipeline/README.md:L32)` |
| 1 | wiki-planner | Parse intent → intent JSON | `.claude/agents/wiki-planner.md` + `agents/pipeline/intent-parser.md` (schema) | `(agents/pipeline/README.md:L34)`, `(agents/pipeline/intent-parser.md:L1)` |
| 2 | wiki-context-selector | Retrieve + filter + slice; ghi `current-task.md` | `.claude/agents/wiki-context-selector.md` + `context-retrieval-map.md` + `context-filter.md` | `(agents/pipeline/README.md:L36-L37)` |
| 2.5 | wiki-plan-reviewer | APPROVED / BLOCK gate | `.claude/agents/wiki-plan-reviewer.md` | `(agents/pipeline/README.md:L39)` |
| 3 | Main agent (Builder) | Đọc current-task.md, code theo `prompt-template.md` | `agents/pipeline/prompt-template.md` | `(agents/pipeline/README.md:L41)`, `(agents/pipeline/prompt-template.md:L1)` |
| 4 | wiki-reviewer (optional) | Check code vs context theo `validator-rules.md` | `.claude/agents/wiki-reviewer.md` + `validator-rules.md` | `(agents/pipeline/README.md:L43)`, `(agents/pipeline/validator-rules.md:L1)` |

### 6.2 Pipeline support docs `(agents/pipeline/README.md:L13-L23)`

| Doc | Vai trò | Citation |
|-----|---------|----------|
| `multi-agent-pipeline.md` | Reference: vai trò + I/O schema + lý do tách của từng subagent | `(agents/pipeline/multi-agent-pipeline.md:L1)`, `(agents/pipeline/README.md:L16)` |
| `intent-parser.md` | Schema của intent JSON (output Stage 1) | `(agents/pipeline/intent-parser.md:L1)`, `(agents/pipeline/README.md:L17)` |
| `context-retrieval-map.md` | Map intent type/component → file wiki cụ thể (input cho Stage 2) | `(agents/pipeline/context-retrieval-map.md:L1)`, `(agents/pipeline/README.md:L18)` |
| `context-filter.md` | Rank + slice + budget rules (input cho Stage 2) | `(agents/pipeline/context-filter.md:L1)`, `(agents/pipeline/README.md:L19)` |
| `prompt-template.md` | Output template main agent dùng ở Stage 3 | `(agents/pipeline/prompt-template.md:L1)`, `(agents/pipeline/README.md:L20)` |
| `validator-rules.md` | Rules cho Stage 4 (wiki-reviewer) — engine defaults + workspace override | `(agents/pipeline/validator-rules.md:L1)`, `(agents/pipeline/README.md:L21)` |
| `PIPELINE-VISUAL.md` | Mermaid + cheat sheet cho pipeline tổng thể | `(agents/pipeline/PIPELINE-VISUAL.md:L1)` |

### 6.3 Evidence sub-pipeline (4 stages: ingest → analyze → qa → apply)

Pipeline song song với 5-stage chính, dành cho evidence ingestion (paste/api/mcp/code/agentic-engine).

| Stage | Spec doc | Citation |
|-------|----------|----------|
| ingest | (no dedicated spec — implemented in `/evidence-ingest` + `/code-analyze`) | `(.claude/commands/evidence-ingest.md:L1)`, `(.claude/commands/code-analyze.md:L1)` |
| analyze | `critical-analysis-prompts.md` (text) + `code-analysis-prompts.md` (code & agentic-engine) | `(agents/pipeline/critical-analysis-prompts.md:L1)`, `(agents/pipeline/code-analysis-prompts.md:L1)` |
| qa | `qa-batching.md` | `(agents/pipeline/qa-batching.md:L1)` |
| apply | (no dedicated spec) — implemented in `/evidence-apply` | `(.claude/commands/evidence-apply.md:L1)` |
| state machine | `evidence-state-rules.md` | `(agents/pipeline/evidence-state-rules.md:L1)` |
| storage | `raw-storage-conventions.md`, `code-snapshot-conventions.md` | `(agents/pipeline/raw-storage-conventions.md:L1)`, `(agents/pipeline/code-snapshot-conventions.md:L1)` |
| reporting | `report-prompts.md` | `(agents/pipeline/report-prompts.md:L1)` |
| observability | `observability.md` | `(agents/pipeline/observability.md:L1)` |

### 6.4 Functional modules (workspace knowledge structure)

Mỗi workspace có cấu trúc giống nhau, áp dụng inside `{wiki_root}/workspaces/{ws}/`:

| Module | Role | Reference |
|--------|------|-----------|
| `workspace.md` | Metadata workspace (project list, owner, default workspace_at_ingest) | `(templates/workspace.md:L1)` |
| `patterns-index.md` | Per-workspace pattern lookup | `(README.md:L36)` |
| `platform/contracts/` | Topic formats, API schemas — highest priority | `(CLAUDE.md:L72)` |
| `platform/patterns/` | Canonical implementations to reuse | `(CLAUDE.md:L73)` |
| `platform/architecture/` | System topology | `(CLAUDE.md:L74)` |
| `domains/{domain}/` | Business rules, state machines | `(CLAUDE.md:L77)` |
| `projects/{project}/` | Per-service docs, local overrides, ADRs | `(CLAUDE.md:L78)` |
| `runbooks/` | Incident handling | `(CLAUDE.md:L79)` |
| `decisions/` | Workspace ADRs | `(CLAUDE.md:L80)` |
| `evidence/sources/{id}/` | Raw evidence (immutable) | `(agents/pipeline/raw-storage-conventions.md:L1)` |
| `evidence/analysis/{id}/` | CORE/CORE-CODE/CORE-AGENTIC analysis output | `(agents/pipeline/code-analysis-prompts.md:L1)` |

---

## Section 7 — Templates

22 files trong `templates/`. Categorized theo artifact type:

### 7.1 Workspace + service skeletons

| Name | Output artifact type | Used by | Citation |
|------|----------------------|---------|----------|
| `workspace.md` | Markdown — workspace metadata skeleton | `/new-workspace`, `/wiki-setup` | `(templates/workspace.md:L1)` |
| `service.md` | Markdown — service doc skeleton | `/evidence-apply` (S5 service drafts), manual create | `(templates/service.md:L1)` |
| `pattern.md` | Markdown — platform/agent pattern doc skeleton | `/evidence-apply`, `/update-wiki` | `(templates/pattern.md:L1)` |
| `adr.md` | Markdown — architecture decision record skeleton | `/evidence-apply` (C6/A6 decision drafts), manual | `(templates/adr.md:L1)` |
| `runbook.md` | Markdown — incident runbook skeleton | manual create after incident | `(templates/runbook.md:L1)` |

### 7.2 Evidence pipeline templates

| Name | Output artifact type | Used by | Citation |
|------|----------------------|---------|----------|
| `evidence-source.yaml` | YAML — `source.yaml` per evidence | `/evidence-ingest`, `/code-analyze` Bước 5 | `(templates/evidence-source.yaml:L1)` |
| `evidence-manifest.yaml` | YAML — apply manifest | `/evidence-apply` | `(templates/evidence-manifest.yaml:L1)` |
| `evidence-index.md` | Markdown — `_index.md` skeleton (Active/Archived tables) | `/evidence-ingest` Bước 6 (init), `/code-analyze` Bước 6 | `(templates/evidence-index.md:L1)` |
| `evidence-pending-external.md` | Markdown — list of P0 questions deferred to external expert | `/evidence-qa` | `(templates/evidence-pending-external.md:L1)` |
| `evidence-qa-answers.md` | Markdown — Q&A batch answer tracking | `/evidence-qa` per-batch | `(templates/evidence-qa-answers.md:L1)` |
| `evidence-qa-recommendations.md` | Markdown — C8 QA Recommender output | `/evidence-qa` (auto pre-batch-1) | `(templates/evidence-qa-recommendations.md:L1)` |
| `evidence-qa-todo.json` | JSON — Q&A todo state | `/evidence-qa` | `(templates/evidence-qa-todo.json:L1)` |
| `evidence-apply-checkpoint.json` | JSON — per-file apply checkpoint (resume support) | `/evidence-apply` | `(templates/evidence-apply-checkpoint.json:L1)` |

### 7.3 Code-analysis templates

| Name | Output artifact type | Used by | Citation |
|------|----------------------|---------|----------|
| `code-snapshot.md` | Markdown — raw.md skeleton cho variant=code | `/code-analyze` Bước 4 (variant=code) | `(templates/code-snapshot.md:L1)` |
| `agentic-engine-snapshot.md` | Markdown — raw.md skeleton cho variant=agentic-engine (NEW) | `/code-analyze` Bước 4 (variant=agentic-engine) | `(templates/agentic-engine-snapshot.md:L1)` |
| `bundle.yaml` | YAML — bundle manifest cho `--bundle` mode | `/code-analyze --bundle` | `(templates/bundle.yaml:L1)` |

### 7.4 Workspace config templates

| Name | Output artifact type | Used by | Citation |
|------|----------------------|---------|----------|
| `wiki-global.json` | JSON — `~/.claude/wiki-global.json` skeleton | `/wiki-setup` (global init), `/install-to-claude.{py,sh}` | `(templates/wiki-global.json:L1)` |
| `wiki-local.json` | JSON — `<cwd>/.claude/wiki.json` skeleton | `/wiki-setup` per-codebase | `(templates/wiki-local.json:L1)` |

### 7.5 Reporting templates

| Name | Output artifact type | Used by | Citation |
|------|----------------------|---------|----------|
| `report-html-skeleton.html` | HTML — wiki report skeleton | `/wiki-report` | `(templates/report-html-skeleton.html:L1)` |
| `report-fragments.html` | HTML — section fragments | `/wiki-report` | `(templates/report-fragments.html:L1)` |

### 7.6 Observability templates

| Name | Output artifact type | Used by | Citation |
|------|----------------------|---------|----------|
| `run-trace.schema.json` | JSON Schema — pipeline run trace validation | `/wiki-trace`, `/wiki-eval`, `scripts/emit_trace.py` | `(templates/run-trace.schema.json:L1)` |
| `task-scorecard.md` | Markdown — manual A/B eval scorecard | `/wiki-eval`, golden-tasks workflow | `(templates/task-scorecard.md:L1)` |

---

## Section 8 — Hooks & settings

_(not analyzed — pass --allow-configs to include settings.json)_

> Note: repo có `.claude/commands/` và `.claude/agents/` nhưng KHÔNG thấy `.claude/settings.json` ở scope (chưa pass `--allow-configs`). Hooks/permissions/env vars chưa biết.

---

## Section 9 — Git summary

_(unmanaged — no git history. git_sha = unmanaged-2064d55e2bd25900333b26deedc3a26205708fd9f0ba8d38a5b3827b59f160d0 — sha256 of sorted file path+content manifest cho scope hiện tại)_

> Repo không nằm dưới git control. Tree manifest sha computed bằng `find {scope-paths} -type f | sort | xargs sha256sum | sha256sum`.

---

## Section 10 — Notes

Observations surprising phát hiện được:

1. **`templates/code-snapshot.md` và `templates/agentic-engine-snapshot.md` là 2 variants** của cùng raw.md skeleton — variant agentic-engine vừa được introduce trong phiên này (xem citation `(templates/agentic-engine-snapshot.md:L1)`). Đây là implicit decision (split snapshot template by variant) cần ADR formalize ở `a06-decision-drafts.md` nếu chạy ON-DEMAND.
2. **3 lớp code analysis prompts cùng tồn tại trong 1 file**: `code-analysis-prompts.md` chứa CORE-CODE (C1–C8), CORE-AGENTIC (A1–A4), và shared CORE 4/CORE 8 — tách khỏi `critical-analysis-prompts.md` (text variant). Có nguy cơ file phình to (file hiện đã > 800 lines). Cân nhắc tách `code-analysis-prompts.md` thành 2 file: `code-analysis-prompts.md` (CORE-CODE only) + `agentic-analysis-prompts.md` (CORE-AGENTIC only). `(agents/pipeline/code-analysis-prompts.md:L533)`
3. **Repo không git** — wiki-template được symlink/install vào nhiều codebase khác nhau qua `scripts/install-to-claude.{py,sh}`. Snapshot này chỉ là 1 source-of-truth tại 1 thời điểm; thay đổi của user sẽ không track được qua commit history. `(scripts/install-to-claude.py)` _(out of scope)_
4. **`/wiki-viz` vắng mặt khỏi `.claude/commands/README.md` Section "Pipeline observability"** mặc dù file `wiki-viz.md` tồn tại — index README có thể stale. `(.claude/commands/README.md:L57-L59)` vs `(.claude/commands/wiki-viz.md:L1)`.
5. **Workspace `wiki` đang active** chứa knowledge META-LEVEL về chính wiki engine (self-referential — wiki nói về chính nó). Đây là pattern hợp lệ (engine maintainers tự document) nhưng cần phân biệt với workspaces application thực tế (`example-surgery`, etc).
6. **`templates/agentic-engine-snapshot.md` được introduce nhưng chưa có ADR** — quyết định technical này nên được formalize. _(see ON-DEMAND a06)_
7. **Pipeline support docs (Section 6.2) một số không có trong `agents/pipeline/README.md` table** — `PIPELINE-VISUAL.md`, `multi-agent-pipeline.md` được list nhưng `code-analysis-prompts.md`, `code-snapshot-conventions.md`, `evidence-state-rules.md`, `qa-batching.md`, `raw-storage-conventions.md`, `report-prompts.md`, `observability.md`, `critical-analysis-prompts.md` thiếu mention trong table chính. Nguy cơ outdated map. `(agents/pipeline/README.md:L13-L23)` vs danh sách 16 file thực tế.
