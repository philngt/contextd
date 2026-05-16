# 08 — Knowledge Gaps (vs workspace `wiki`)

> Source evidence: `2026-05-08-engine-bootstrap-wiki-template` (variant=agentic-engine)
> Inputs: a01-engine-stack.md + a02-command-map.md + a03-pattern-proposals.md + a04-contract-proposals.md + workspace `wiki` (empty)

Authoritative source for `blocks_apply` và `gap_severity`. `qa-batching.md` derive từ file này.

Workspace baseline: `{ws}/{patterns-index.md, platform/patterns/, platform/contracts/, projects/, decisions/}` rỗng → bootstrap workflow → mọi gap structural là `[BLOCKING]` đối với apply, không phải đối với task user (engine vẫn chạy được).

---

## Blocking gaps (must resolve before apply)

### G-001 — Patterns chưa có file trong `{ws}/platform/patterns/`  [BLOCKING]
- **Type**: missing-pattern
- **Affected**: `{ws}/platform/patterns/{workspace-resolve-step0,askuser-confirm-preview,secrets-blocklist-gate,redaction-post-pass,evidence-state-machine,citation-rule,multi-stage-subagent-pipeline,variant-discriminated-dispatcher}.md` (8 files will be created)
- **Needed info**: User confirm pattern name + scope (workspace-wide hay project-specific) cho từng P-001..P-008.
- **Source in code**: `(workspaces/wiki/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md)` P-001..P-008
- **Resolution**: `/evidence-qa` P0 batch confirm từng pattern → `/evidence-apply` create files.

### G-002 — Contracts chưa có file trong `{ws}/platform/contracts/`  [BLOCKING]
- **Type**: missing-contract
- **Affected**: `{ws}/platform/contracts/{evid-id-format,evidence-file-layout,raw-md-section-structure,source-yaml-schema,evidence-state-machine,citation-format,slash-command-naming,sub-agent-frontmatter-schema}.md` (8 files will be created)
- **Needed info**: User confirm rule statement chính xác cho từng C-001..C-008. C-007 có sub-decision (verb-subject vs subject-verb consistent?).
- **Source in code**: `(workspaces/wiki/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a04-contract-proposals.md)` C-001..C-008
- **Resolution**: `/evidence-qa` P0 batch confirm → `/evidence-apply` create files. C-005/C-006 cần coordinate với G-001 (pattern–contract pair).

### G-003 — Command/agent docs chưa có  [BLOCKING for full coverage]
- **Type**: missing-service-doc
- **Affected**: `{ws}/projects/{project}/services/` empty hoặc `{ws}/engine/` (chưa có thư mục) — quyết định doc location chưa được resolve.
- **Needed info** (P1 question):
  - 1 doc per command (19 + 5 = 24 docs)?
  - Group by category (5–6 group docs)?
  - 1 mega-doc tổng quan (1 doc)?
  - Doc location: `{ws}/projects/engine/services/` hay `{ws}/engine/` (workspace-level reserved namespace)?
- **Source in code**: `(workspaces/wiki/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a02-command-map.md)` E-001..E-019, A-001..A-005
- **Resolution**: User decision in `/evidence-qa` P1 batch → run `--prompt a05` (command/agent doc drafts) → `/evidence-apply`.

### G-004 — ADR cho variant `agentic-engine` introduction  [BLOCKING for traceability]
- **Type**: missing-adr
- **Affected**: `{ws}/decisions/{NNN}-introduce-agentic-engine-variant.md`
- **Needed info**:
  - Decision context: tại sao introduce variant mới thay vì force-fit wiki-template vào variant=code?
  - Alternatives considered: (a) skip /code-analyze cho engine repos, (b) extend variant=code section schema, (c) introduce agentic-engine variant — option (c) chosen this session.
  - Trade-offs: code-analysis-prompts.md grow (CORE-CODE + CORE-AGENTIC trong 1 file ~900 lines).
- **Source in code**: introduced trong session 2026-05-08, files affected:
  - `(agents/pipeline/code-snapshot-conventions.md:L324-L399)` Section 12
  - `(agents/pipeline/code-analysis-prompts.md:L8-L18)` variant dispatch
  - `(agents/pipeline/code-analysis-prompts.md:L533-L920)` CORE-AGENTIC A1–A4 + A5–A7
  - `(.claude/commands/code-analyze.md:L43-L70, L194-L297, L412-L420)` Bước 1.4 + 4 + 7 dispatch
  - `(.claude/commands/evidence-analyze.md)` Bước 2 dispatch (just patched in Phase 1 of this run)
  - `(templates/agentic-engine-snapshot.md:L1)` new template
  - `(templates/evidence-source.yaml:L17-L19)` new code_variant field
- **Resolution**: `/evidence-analyze --id 2026-05-08-engine-bootstrap-wiki-template --prompt a06` để draft ADR → `/evidence-qa` confirm → `/evidence-apply`.

### G-005 — ADR cho `code-analysis-prompts.md` chứa cả CORE-CODE + CORE-AGENTIC  [BLOCKING for maintenance]
- **Type**: missing-adr
- **Affected**: `{ws}/decisions/{NNN}-{keep|split}-code-analysis-prompts.md`
- **Needed info**:
  - File hiện ~920 lines (`agents/pipeline/code-analysis-prompts.md` line counts post-extension).
  - Decision: (a) keep monolithic (current), (b) split thành `code-analysis-prompts.md` + `agentic-analysis-prompts.md`.
  - Trade-offs: monolithic = single dispatch reference, easier to find shared prompts (CORE 4/8). Split = better readability, mỗi file ~450 lines.
- **Source in code**: `(agents/pipeline/code-analysis-prompts.md:L1-L920)` toàn file; observation in raw.md `(workspaces/wiki/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md#section-10, item 2)`.
- **Resolution**: P1 question + ADR draft via `--prompt a06`.

### G-006 — `/wiki-viz` orphaned trong commands/README.md  [BLOCKING for documentation accuracy]
- **Type**: stale-doc
- **Affected**: `(.claude/commands/README.md:L57-L59)` — Section "Pipeline observability" thiếu row cho `/wiki-viz`. File `wiki-viz.md` tồn tại và khai báo Bước 0 (commands count match khi grep).
- **Needed info**: User confirm `/wiki-viz` là production command (cần index) hay deprecated/experimental (không index).
- **Source in code**:
  - `(.claude/commands/wiki-viz.md:L1)` — file exists, has heading "# Wiki Viz"
  - `(.claude/commands/README.md:L54-L61)` — Pipeline observability section list 2 commands (wiki-trace, wiki-eval), missing wiki-viz
- **Resolution**: `/update-wiki` add row vào README.md. KHÔNG cần ADR (sửa stale doc, không phải decision).

---

## Nice-to-have gaps

### G-007 — `agents/pipeline/README.md` table outdated  [NICE-TO-HAVE]
- **Type**: stale-doc
- **Affected**: `(agents/pipeline/README.md:L13-L23)` — table list 7/16 pipeline support docs.
- **Missing rows**: `code-analysis-prompts.md`, `code-snapshot-conventions.md`, `evidence-state-rules.md`, `qa-batching.md`, `raw-storage-conventions.md`, `report-prompts.md`, `observability.md`, `critical-analysis-prompts.md`, `PIPELINE-VISUAL.md` (already mentioned but in different anchor).
- **Source in code**: `(agents/pipeline/README.md:L13-L23)` vs actual files in `agents/pipeline/` (16 .md files).
- **Resolution**: `/update-wiki` extend table. Low urgency — không break engine, chỉ harder to navigate.

### G-008 — Section 3 (configs) + Section 8 (hooks) chưa analyze  [NICE-TO-HAVE]
- **Type**: missing-data
- **Affected**: `a01-engine-stack.md` Configurable surface = `_(not analyzed)_`; raw.md Section 8 = `_(not analyzed — pass --allow-configs)_`.
- **Needed info**: User decide có rerun `/code-analyze --allow-configs` không. Settings file có thể chứa hooks define automated behavior — nếu không analyze, CORE-AGENTIC misses hook-driven patterns.
- **Source in code**:
  - `(workspaces/wiki/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md#section-3)` — guard log shows configs skipped
  - `(workspaces/wiki/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md#section-8)` — settings unanalyzed
- **Resolution**: User opt-in `--allow-configs` → rerun `/code-analyze` (will create new evid-id refresh-wiki-template-2026-05-08).

### G-009 — Tools allowlist principle (C-008a candidate) thiếu evidence  [NICE-TO-HAVE]
- **Type**: insufficient-evidence
- **Affected**: future contract C-008a (tools allowlist principle: read-only vs write-allowed roles).
- **Needed info**: Sample size hiện = 5 sub-agents, không đủ để claim universal principle. Cần thêm sub-agents (vd application-domain agents) để verify.
- **Source in code**: `(workspaces/wiki/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a04-contract-proposals.md)` C-008 Recommendation note.
- **Resolution**: Defer cho future evidence ingest (vd application workspace có sub-agents thực tế). KHÔNG block apply C-008 (frontmatter schema).

### G-010 — Mixed naming convention "verb-subject" vs "subject-verb"  [NICE-TO-HAVE]
- **Type**: inconsistency
- **Affected**: contract C-007 sub-decision.
- **Source in code**: `(workspaces/wiki/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a04-contract-proposals.md)` C-007 note.
- **Resolution**: P2 question trong 04-questions.md. Có thể leave as-is (cả 2 convention OK trong communities) hoặc enforce consistency cho commands mới.

---

## Missing source types

_(none — agentic-engine variant vừa được introduce, đã cover toàn bộ engine surface)_

---

## Severity summary

| Severity | Count | List |
|----------|-------|------|
| BLOCKING | 6 | G-001, G-002, G-003, G-004, G-005, G-006 |
| NICE | 4 | G-007, G-008, G-009, G-010 |

Total = 10 gaps.

## Apply readiness

- **Cannot apply** until BLOCKING gaps resolved via `/evidence-qa` P0/P1 batches.
- **G-001 + G-002 + G-005 (pattern–contract pairs)** nên resolve cùng batch (cross-reference dependency).
- **G-003** depend trên P1 decision về doc grouping strategy → block `/evidence-apply --prompt a05`.
- **G-004** standalone — có thể resolve sớm (introduce agentic-engine variant ADR).
- **G-006** không block evidence-apply (khác workspace path) — có thể fix riêng qua `/update-wiki`.
- **NICE gaps** không block apply; có thể defer.
