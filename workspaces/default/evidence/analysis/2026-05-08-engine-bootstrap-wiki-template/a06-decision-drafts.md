# a06 — Implicit Decision Drafts

> Source evidence: `2026-05-08-engine-bootstrap-wiki-template` (variant=agentic-engine)
> Inputs: raw.md Section 9 (git — unmanaged), Section 4–7 (commands/agents/templates), session 2026-05-08 changes, `08-knowledge-gaps.md` G-004/G-005
> Note: Repo unmanaged-by-git → KHÔNG có commit history. Decisions detect dựa vào structural analysis của session changes + cross-reference observations.

---

## D-001 — Introduce variant=agentic-engine cho /code-analyze

### Scope
workspace-wide (engine-level decision affecting mọi workspace consume engine)

### Context
Trước session 2026-05-08, `/code-analyze` chỉ hỗ trợ runtime codebase (Java/Spring, Node/Express, Python/FastAPI, Go) — Section 4–8 của raw.md design cho REST endpoints / Kafka consumers / JPA entities / DB migrations.

User cố gắng chạy `/code-analyze` trên `wiki-template` repo (markdown-heavy: 19 slash commands, 5 sub-agents, 16 pipeline spec docs, 22 templates) gặp 2 vấn đề:
1. **Validation gate fail**: repo không có `.git/` cũng không có `pom.xml`/`package.json`/etc → STOP `not a recognized code repo`.
2. **Sections misfire**: nếu force-fit, Section 4 (REST endpoints) / Section 5 (Kafka consumers) / Section 7 (DB schema) sẽ trống — output cho CORE-CODE prompts (c01–c04) sẽ tạo proposals vô nghĩa (Kafka topic naming pattern cho 1 markdown engine).

### Decision
Introduce **`code_variant: code | agentic-engine`** field cho `source.yaml`. Default omitted = `code` (backward-compat). `agentic-engine` variant:
- Soften validation gate: không yêu cầu `.git/`/build file; đủ ≥ 2 markers trong {`agents/**/*.md`, `.claude/commands/**/*.md`, `.claude/agents/**/*.md`, `templates/`, `mcp.json`}.
- Section 4–8 redefined: Slash commands / Sub-agents / Pipeline stages / Templates / Hooks (thay vì REST/Kafka/Services/DB/Public APIs).
- evid-id prefix `engine` (thay `code`).
- Origin format `engine:{slug}@{sha}`.
- New CORE-AGENTIC prompts A1–A4 dispatched via `code_variant` (parallel với CORE-CODE C1–C4).
- New ON-DEMAND A5–A7 (parallel với C5–C7).

### Alternatives considered

| Option | Rejected because |
|--------|------------------|
| (a) Skip /code-analyze cho engine repos | Engine maintainers không có path để bootstrap wiki cho engine. Onboarding gap. |
| (b) Force-fit variant=code, accept empty Section 4–8 | CORE-CODE prompts hallucinate (đề xuất Kafka pattern cho markdown repo). Misfire output >> empty output value. |
| (c) New `source_type=engine` (parallel với code/paste/api/mcp) | Source_type space explode khi thêm variant tương lai (infra, data-pipeline, ...). Variant approach scales better. |
| (d) Variant approach (chosen) | Section 4–8 redefine clean; same source_type=code dispatch tree; CORE prompts reused (CORE 4 và CORE 8 shared via filename); new variants future không cần đổi source_type. |

### Trade-offs (observed)
- **Pro**: variant approach extensible; share state machine + file layout contracts; backward-compat (default omitted).
- **Pro**: CORE 4 (questions) và CORE 8 (gaps) reused via filename across variants → less duplication.
- **Con**: `code-analysis-prompts.md` tăng size từ ~520 lines lên ~920 lines (CORE-CODE + CORE-AGENTIC trong cùng file). → Dẫn đến D-002.
- **Con**: 2 templates `code-snapshot.md` + `agentic-engine-snapshot.md` cần maintain song song. Drift risk khi future change Section structure.
- **Con**: Implementation requires patch trên 5 surfaces: `code-snapshot-conventions.md` Section 12, `code-analysis-prompts.md` CORE-AGENTIC + ON-DEMAND, `code-analyze.md` Bước 1.4/4/5/7, `evidence-analyze.md` Bước 2/4/6, `templates/agentic-engine-snapshot.md` (new).

### Citation (all changes session 2026-05-08)
- `(agents/pipeline/code-snapshot-conventions.md:L324-L399)` — Section 12 spec
- `(agents/pipeline/code-analysis-prompts.md:L8-L18)` — variant dispatch table
- `(agents/pipeline/code-analysis-prompts.md:L533-L920)` — CORE-AGENTIC A1–A4 + ON-DEMAND A5–A7
- `(.claude/commands/code-analyze.md:L43-L70)` — Bước 1.4 detect
- `(.claude/commands/code-analyze.md:L194-L297)` — Bước 4 dispatch
- `(.claude/commands/code-analyze.md:L412-L420)` — Bước 7 dispatch
- `(.claude/commands/evidence-analyze.md)` — Bước 2 dispatch (patched in this session Phase 1)
- `(templates/agentic-engine-snapshot.md:L1)` — new template
- `(templates/evidence-source.yaml:L17-L19)` — `code_variant` field

### Suggested ADR file path
`{ws}/decisions/001-introduce-agentic-engine-variant.md`

### Status
PROPOSED — pending user confirmation in `/evidence-qa` (q-017).

---

## D-002 — Keep `code-analysis-prompts.md` monolithic (do NOT split)

### Scope
workspace-wide (engine-level)

### Context
After D-001 introduction, `agents/pipeline/code-analysis-prompts.md` chứa:
- CORE-CODE: C1–C4 (~470 lines)
- ON-DEMAND code: C5–C8 (~140 lines)
- CORE-AGENTIC: A1–A4 (~280 lines)
- ON-DEMAND agentic: A5–A7 (~80 lines)
- Shared: CORE 4 + CORE 8 (~100 lines combined)
- Variant dispatch + bundle notes + cite check (~50 lines)

Total ~920 lines. File concern raised trong raw.md Section 10 item 2 — observation rằng có nguy cơ phình to.

### Decision (DRAFT — pending user confirm)
**KEEP monolithic** trong `agents/pipeline/code-analysis-prompts.md`. KHÔNG split thành 2 file.

### Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Split: `code-analysis-prompts.md` (CORE-CODE) + `agentic-analysis-prompts.md` (CORE-AGENTIC) | Shared sections (CORE 4, CORE 8) phải duplicate hoặc cross-reference complex. Variant dispatch table phải maintain ở 2 nơi. |
| Split: per-prompt file (c01.md, c02.md, ..., a01.md, ...) | Over-fragmentation; navigation harder. |
| Keep monolithic + ToC at top + `## CORE-CODE prompts` / `## CORE-AGENTIC prompts` section markers (chosen) | Single file navigable via heading anchors. Shared sections collocated. Variant dispatch single source. |

### Trade-offs
- **Pro**: shared CORE 4 / CORE 8 / variant dispatch table maintained once.
- **Pro**: 920 lines vẫn manageable — comparable với critical-analysis-prompts.md (~500 lines for text variant).
- **Con**: Reading scroll trên devices nhỏ.
- **Con**: Khi thêm variant thứ 3 (vd `infra`), file có thể vượt 1500 lines → revisit decision.

### Trigger to revisit
- File > 1500 lines, HOẶC
- Variant thứ 3 introduced, HOẶC
- User feedback "navigation slow".

### Citation
- `(agents/pipeline/code-analysis-prompts.md:L1-L920)` — entire file
- `(workspaces/default/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md#section-10, item 2)` — observation

### Suggested ADR file path
`{ws}/decisions/002-keep-code-analysis-prompts-monolithic.md`

### Status
PROPOSED — pending user confirmation in `/evidence-qa` (q-018).

---

## D-003 — Workspace `wiki` self-referential (engine documents itself)

### Scope
workspace-wide; affects how user think about workspace boundary

### Context
`wiki-template` repo đang dùng workspace `wiki` để document chính nó (engine documenting engine). Đây là pattern bất thường vì:
- Mọi workspace khác là **application workspace** (vd `example-surgery`) — chứa knowledge về business domain, services, contracts cho 1 app.
- Workspace `wiki` chứa knowledge về **engine internals** — patterns, contracts, decisions của engine code.

### Decision (DRAFT)
Workspace `wiki` là **first-class self-referential workspace**, KHÔNG phải special case. Hợp lệ vì:
- Engine maintainers cần knowledge sandbox riêng để document patterns engine.
- Workspace structure (`platform/`, `projects/`, `decisions/`, ...) áp dụng đầy đủ — engine commands/agents treat như "services" trong project `engine`.
- Không cross-pollution với application workspaces (mỗi workspace là sandbox độc lập theo CLAUDE.md hard constraint).

### Boundary distinction
- **Engine spec docs** trong `agents/pipeline/*.md`, `agents/coding-rules.md` etc. — describe **how engine works internally** (architecture-oriented; audience = engine maintainer).
- **Platform patterns** trong `{ws}/platform/patterns/*.md` (workspace `wiki`) — describe **what to apply** (action-oriented; audience = engine **user** developing on engine).

Khi engine spec change → engine spec doc updated. Khi user-facing pattern reusable → platform pattern doc updated. Drift between 2 layers OK trong short term, but `/contextd-eval` should detect mismatches.

### Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Don't document engine at all (just spec docs) | Engine users cần actionable patterns, not just architecture spec. |
| Special namespace `engine/` outside workspaces | Breaks workspace model invariant. Special case proliferation. |
| Document engine trong template workspace (`templates/workspace.md`) | Templates is skeletons, not knowledge store. |
| Self-referential workspace (chosen) | Reuses workspace model; consistent UX; sandboxed from application workspaces. |

### Trade-offs
- **Pro**: workspace model uniform; user mental model simple ("there are workspaces, one of them happens to be about the engine").
- **Pro**: Engine evolution traceable via workspace ADRs (`{ws}/decisions/`).
- **Con**: Risk of drift between engine spec docs (`agents/pipeline/*`) và workspace platform patterns (`{ws}/platform/patterns/*`). Mitigation: `/contextd-eval` cross-check.
- **Con**: User onboarding confusion ("which is source of truth?"). Mitigation: rule "spec docs describe HOW; patterns describe WHAT to apply".

### Citation
- `(workspaces/default/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md#section-10, item 5)` — self-referential observation
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/04-questions.md)` q-023 — counter-argument question
- `(CLAUDE.md:L18-L25)` — workspace sandboxing rule

### Suggested ADR file path
`{ws}/decisions/003-self-referential-engine-workspace.md`

### Status
PROPOSED — pending user confirmation in `/evidence-qa` (q-023 refinement).

---

## D-004 — Pattern–Contract pairing convention

### Scope
workspace-wide (engine-level)

### Context
Trong a03 + a04, 3 cặp pattern–contract cùng concept lộ ra:
- P-005 evidence-state-machine ↔ C-005 evidence-state-machine-transitions
- P-006 citation-rule-relative-path ↔ C-006 citation-format
- P-007/P-008 (patterns chưa có pair contract — chờ data thêm)

Câu hỏi: Khi nào 1 concept nên là pattern, khi nào contract, khi nào CẢ HAI?

### Decision (DRAFT)
Convention:

| Layer | Định nghĩa | Audience | File location |
|-------|-----------|----------|---------------|
| **Pattern** | Implementation **skeleton** + canonical structure + diff vs alternatives | Người đang IMPLEMENT 1 feature follow pattern | `{ws}/platform/patterns/{name}.md` |
| **Contract** | Invariant **rule** + observed evidence + counter-examples + validator behavior | Người đang VALIDATE / REVIEW code | `{ws}/platform/contracts/{name}.md` |

**Pairing rule**: Concept có cả implementation skeleton VÀ invariant rule → tạo cả 2 docs với cross-reference. Pattern doc cite contract; contract doc cite pattern.

**Single-document rule**: Concept chỉ là pure rule (vd evid-id format) → contract only. Concept chỉ là implementation pattern không có hard invariant (vd "preview-block layout style") → pattern only.

### Alternatives considered

| Option | Rejected because |
|--------|------------------|
| All patterns (no contracts) | Validator reject conditions cần ngôn ngữ "rule" không phải "skeleton". Confusion. |
| All contracts (no patterns) | Implementer cần "how to apply", không phải "what to validate". Half-information. |
| Merge pattern + contract trong 1 doc | Audience mixing. Implementer lost trong validator details. Validator lost trong implementation detail. |
| Pattern–contract pairing với clear convention (chosen) | Layered information. Cross-reference makes navigation explicit. |

### Trade-offs
- **Pro**: Clear separation of concerns (HOW vs WHAT-IS-CORRECT).
- **Pro**: Cross-reference enforces consistency (impl skeleton phải satisfy invariant rule).
- **Con**: 2 docs cho cùng concept = double maintenance.
- **Con**: User decision required mỗi pattern proposal: pair-or-single. → Q&A friction.

### Citation
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md)` P-005, P-006 recommendation sections
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a04-contract-proposals.md)` C-005, C-006 recommendation sections
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/04-questions.md)` q-005, q-006

### Suggested ADR file path
`{ws}/decisions/004-pattern-contract-pairing-convention.md`

### Status
PROPOSED — pending user confirmation in `/evidence-qa` (q-005, q-006 batch).

---

## D-005 — `/contextd-viz` keep-or-deprecate

### Scope
engine-level

### Context
G-006: `/contextd-viz` exists as `.claude/commands/contextd-viz.md` but missing from `.claude/commands/README.md` Section "Pipeline observability" index. 2 hypotheses:
- (a) Production command, README simply stale.
- (b) Experimental/deprecated command, README intentionally exclude.

Code analysis from raw.md Section 4.5: `/contextd-viz` listed as observability companion (HTML viewer + live watch). Frontmatter/heading present. KHÔNG có deprecation notice trong file.

### Decision (DRAFT)
**Option (a) — production command, README stale**. Reasons:
- File has `# Wiki Viz` heading (`.claude/commands/contextd-viz.md:L1`) without "deprecated" or "experimental" note.
- Bước 0 workspace check present (per pattern P-001) — same maturity level as `/contextd-trace` and `/contextd-eval`.
- README index missing entry is most likely human oversight (3 commands trong category, 2 in index).

### Action
- Update `.claude/commands/README.md` Section "Pipeline observability" → add row cho `/contextd-viz`.
- Tách phiên riêng (per q-019 default — không trộn doc fix với evidence-apply).

### Alternatives considered
- (b) Deprecate → archive `.claude/commands/contextd-viz.md` to `.claude/commands/_archive/`. Rejected: no evidence of intentional exclusion.

### Citation
- `(.claude/commands/contextd-viz.md:L1)` — file present
- `(.claude/commands/README.md:L57-L59)` — README missing row
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/08-knowledge-gaps.md)` G-006

### Suggested ADR file path
N/A — bug fix, KHÔNG cần ADR. Track via PR description or commit message.

### Status
RESOLVED-PENDING-FIX — fix qua `/contextd-update` trong phiên riêng.

---

## Notes for `/evidence-apply`

- **5 decision drafts**: D-001, D-002, D-003, D-004 → ADR files cho `{ws}/decisions/`. D-005 → bug fix only.
- D-001 → ADR `001-introduce-agentic-engine-variant.md` resolves G-004.
- D-002 → ADR `002-keep-code-analysis-prompts-monolithic.md` resolves G-005.
- D-003 → ADR `003-self-referential-engine-workspace.md` (new gap không có trong 08, but emerges from a03 P-007 và q-023 — should add to 08 as `[NICE]`).
- D-004 → ADR `004-pattern-contract-pairing-convention.md` (new gap, emerges from q-005/q-006 cross-reference).
- D-005 → action item, no ADR.

Apply order: ADRs LAST (after patterns + contracts + service docs) vì ADRs reference những decisions about những artifacts đó.
