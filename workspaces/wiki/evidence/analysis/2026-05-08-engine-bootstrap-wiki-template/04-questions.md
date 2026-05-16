# 04 — Question Pool (vs workspace `wiki`)

> Source evidence: `2026-05-08-engine-bootstrap-wiki-template` (variant=agentic-engine)
> Inputs: a01–a04 + 08-knowledge-gaps.md + raw.md
> Schema: theo CORE 4 (agentic-engine override) `(agents/pipeline/code-analysis-prompts.md "CORE 4 — Question Generator (agentic-engine override)")`

Question priorities:
- **P0** — blocks_apply, must answer before `/evidence-apply`.
- **P1** — high-value, unblocks structural decisions.
- **P2** — nice-to-have, refines but doesn't block.
- **P3** — counter-arguments / sanity checks.

---

## P0 — Pattern confirmations (block apply)

### q-001  [P0]  Pattern P-001 workspace-resolve-step0
- **Question**: Pattern P-001 `workspace-resolve-step0` (cite raw.md → 15 commands follow Bước 0 boilerplate) có nên thêm vào `{ws}/platform/patterns/workspace-resolve-step0.md` không?
- **Reason**: G-001 blocking — 15/15 commands follow → strong evidence (●●●). Coverage near-universal.
- **Source**: `(workspaces/wiki/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md)` P-001
- **Default suggestion**: NÊN THÊM (CAO) — pattern là invariant ở engine level.

### q-002  [P0]  Pattern P-002 askuser-confirm-preview
- **Question**: Pattern P-002 `askuser-confirm-preview` (4+ commands có preview→Continue/Edit/Cancel flow) có nên thêm vào `{ws}/platform/patterns/askuser-confirm-preview.md`?
- **Reason**: G-001 blocking. Coverage moderate (4 commands xác định, có thể thêm).
- **Source**: `a03-pattern-proposals.md` P-002
- **Default suggestion**: NÊN THÊM (●●○) — apply cho commands có side effects.

### q-003  [P0]  Pattern P-003 secrets-blocklist-gate
- **Question**: Pattern P-003 `hard-blocklist-plus-askuser-gate` (2-tier config guard) có nên thêm vào `{ws}/platform/patterns/secrets-blocklist-gate.md`?
- **Reason**: G-001 blocking. Critical security pattern — should formalize.
- **Source**: `a03-pattern-proposals.md` P-003
- **Default suggestion**: NÊN THÊM (●●●) — security-critical, even though only 1 explicit implementation hiện tại.

### q-004  [P0]  Pattern P-004 redaction-post-pass
- **Question**: Pattern P-004 `redaction-post-pass` (scan-and-stop-on-secret) có nên thêm vào `{ws}/platform/patterns/redaction-post-pass.md`?
- **Reason**: G-001 blocking. Companion với P-003.
- **Source**: `a03-pattern-proposals.md` P-004
- **Default suggestion**: NÊN THÊM (●●●).

### q-005  [P0]  Pattern P-005 evidence-state-machine
- **Question**: Pattern P-005 `evidence-state-machine` (DAG transitions) — pattern doc tại `{ws}/platform/patterns/`, hay promote thẳng thành CONTRACT C-005 only (skip pattern), hay làm cả PAIR (pattern + contract)?
- **Reason**: G-001 + G-002 cross-reference. P-005 và C-005 cùng concept — quyết định layering.
- **Source**: `a03-pattern-proposals.md` P-005, `a04-contract-proposals.md` C-005
- **Default suggestion**: PAIR (pattern describes implementation skeleton; contract describes invariant rule) — recommended convention cho engine.

### q-006  [P0]  Pattern P-006 citation-rule + Contract C-006 citation-format
- **Question**: P-006/C-006 cùng concept — confirm PAIR approach (giống P-005/C-005)?
- **Reason**: G-001 + G-002 cross-reference.
- **Source**: `a03-pattern-proposals.md` P-006, `a04-contract-proposals.md` C-006
- **Default suggestion**: PAIR.

### q-007  [P0]  Pattern P-007 multi-stage-subagent-pipeline (FLAGSHIP)
- **Question**: P-007 là **flagship pattern** đại diện engine identity (5-stage `/use-wiki` flow). Có nên đặt làm pattern ĐẦU TIÊN trong `{ws}/patterns-index.md` (top of list)?
- **Reason**: G-001 blocking + identity statement.
- **Source**: `a03-pattern-proposals.md` P-007
- **Default suggestion**: YES — top of patterns-index, cross-reference từ workspace.md.

### q-008  [P0]  Pattern P-008 variant-discriminated-dispatcher
- **Question**: P-008 (variant dispatcher) chỉ có 1 instance hoàn chỉnh (variant agentic-engine vừa được add). Sample size = 1 — confidence thấp. Promote thành pattern NGAY, hay đợi variant thứ 3 để verify shape?
- **Reason**: G-001 blocking + sample size concern.
- **Source**: `a03-pattern-proposals.md` P-008
- **Default suggestion**: ADD pattern doc với confidence note "single instance — pattern shape may evolve". Tốt hơn là document sớm để variant tiếp theo follow consistent skeleton.

---

## P0 — Contract confirmations (block apply)

### q-009  [P0]  Contract C-001 evid-id-format
- **Question**: Contract C-001 (`{date}-{src}-{slug}` format với src ∈ {paste, api, mcp, code, engine, platform}) có chính xác là rule chính thức? Có cần thêm src nào khác (vd `ticket`, `incident`)?
- **Reason**: G-002 blocking. Coverage 5/5 → high confidence.
- **Source**: `a04-contract-proposals.md` C-001
- **Default suggestion**: NÊN THÊM với src list hiện tại; future src additions update contract version.

### q-010  [P0]  Contract C-002 evidence-file-layout
- **Question**: Contract C-002 file layout invariant — `sources/{id}/{source.yaml, raw.{ext}, raw.normalized.md?}` + `analysis/{id}/`, `qa/{id}/`, `_index.md` — có chính xác? Counter-examples nào?
- **Reason**: G-002 blocking. Universal layout, coverage cao.
- **Source**: `a04-contract-proposals.md` C-002
- **Default suggestion**: NÊN THÊM (●●●).

### q-011  [P0]  Contract C-003 raw-md-section-structure
- **Question**: Contract C-003 (10 sections variant=code, 10 sections variant=agentic-engine, bundle Section 0 + per-repo) — có nên là 1 contract đa-variant hay tách 3 contracts riêng?
- **Reason**: G-002 blocking. Câu hỏi về granularity.
- **Source**: `a04-contract-proposals.md` C-003
- **Default suggestion**: 1 contract đa-variant với variant table — dễ extend khi thêm variant mới.

### q-012  [P0]  Contract C-004 source-yaml-required-fields
- **Question**: Contract C-004 required fields: 11 always-required + conditional (code variant) + conditional (bundle mode) — có nên tách C-004a (code-specific) thành contract riêng không?
- **Reason**: G-002 blocking. Câu hỏi về granularity.
- **Source**: `a04-contract-proposals.md` C-004
- **Default suggestion**: KEEP unified với conditional sections — easier to read. Tách khi conditional grow phức tạp.

### q-013  [P0]  Contract C-007 slash-command-naming consistency
- **Question**: Contract C-007 — convention "verb-subject" vs "subject-verb" mixed trong cùng group (vd workspace ops). Enforce consistency cho commands MỚI hay accept current mixed convention?
- **Reason**: G-002 + G-010. Nice-to-have inconsistency, but contract phải state rule rõ.
- **Source**: `a04-contract-proposals.md` C-007, `08-knowledge-gaps.md` G-010
- **Default suggestion**: Document BOTH convention as valid; suggest "subject-verb" cho commands tương lai (more searchable theo subject).

### q-014  [P0]  Contract C-008 sub-agent-frontmatter-schema
- **Question**: Contract C-008 frontmatter required fields (name, description, tools, model). Có cần required `description` chứa "DÙNG KHI / KHÔNG DÙNG" patterns (positive + negative trigger)?
- **Reason**: G-002 blocking. Sample 5/5 follow nhưng có thể là coincidence.
- **Source**: `a04-contract-proposals.md` C-008
- **Default suggestion**: Mark "DÙNG KHI/KHÔNG DÙNG" as **convention** (recommended) chứ không phải required — để flexible cho agents tương lai có scope đơn giản hơn.

---

## P1 — Service/doc strategy + ADR (high-value, structural)

### q-015  [P1]  Doc grouping strategy cho commands + agents
- **Question**: 19 slash commands + 5 sub-agents → doc strategy?
  - Option A: 1 doc per entry (24 docs trong `{ws}/projects/engine/services/`)
  - Option B: Group by category (5–6 group docs: workspace-ops, wiki-usage, codebase-analysis, reporting, observability, evidence-pipeline)
  - Option C: 1 mega-doc tổng quan + per-command sections
  - Option D: Reuse `{ws}/projects/{p}/services/` schema cho commands (treat command như service)
- **Reason**: G-003 blocking — affects 24+ files.
- **Source**: `08-knowledge-gaps.md` G-003, `a02-command-map.md` E-001..E-019 + A-001..A-005
- **Default suggestion**: Option B (group by category, 6 docs) — balance between detail và navigation. Then individual commands cite vào group doc + raw.md anchor.

### q-016  [P1]  Doc location: `projects/engine/` vs `engine/`
- **Question**: Tạo `{ws}/projects/engine/services/` (treating engine như project) hay tạo namespace mới `{ws}/engine/`?
- **Reason**: G-003 blocking. Workspace structure decision.
- **Source**: `08-knowledge-gaps.md` G-003
- **Default suggestion**: `{ws}/projects/engine/` — KHÔNG introduce new top-level namespace để giữ workspace structure consistent.

### q-017  [P1]  ADR cho variant agentic-engine introduction
- **Question**: Draft ADR cho decision "introduce variant=agentic-engine" — title + scope + alternatives đã clear (G-004). Run `--prompt a06` để generate draft? Hay user write ADR thủ công?
- **Reason**: G-004 blocking traceability.
- **Source**: `08-knowledge-gaps.md` G-004
- **Default suggestion**: Run `--prompt a06` để generate draft, then user review & edit.

### q-018  [P1]  Decision: split or keep `code-analysis-prompts.md`
- **Question**: File `code-analysis-prompts.md` hiện ~920 lines (CORE-CODE + CORE-AGENTIC + shared). Split thành 2 files hay keep?
- **Reason**: G-005 blocking maintenance.
- **Source**: `08-knowledge-gaps.md` G-005
- **Default suggestion**: KEEP monolithic — shared sections (CORE 4, CORE 8) easier to maintain trong 1 file. Revisit nếu thêm variant thứ 3.

### q-019  [P1]  Pre-apply: fix `/wiki-viz` orphan trong README index
- **Question**: G-006 — `/wiki-viz` missing from `.claude/commands/README.md` Section "Pipeline observability". Fix qua `/update-wiki` trong cùng phiên này hay tách phiên riêng?
- **Reason**: G-006 — không block evidence-apply nhưng break onboarding clarity.
- **Source**: `08-knowledge-gaps.md` G-006
- **Default suggestion**: Tách phiên — không trộn doc fix với evidence-apply. Mark P1 todo.

---

## P2 — Refinements (nice-to-have, non-blocking)

### q-020  [P2]  Pipeline support docs table outdated
- **Question**: G-007 — `agents/pipeline/README.md` table list 7/16 docs. Extend table trong cùng phiên này hay defer?
- **Reason**: G-007 nice-to-have.
- **Source**: `08-knowledge-gaps.md` G-007
- **Default suggestion**: Defer — file vẫn navigable (file tồn tại trong dir), chỉ table summary outdated.

### q-021  [P2]  Tools allowlist principle (C-008a candidate)
- **Question**: G-009 — sample 5 sub-agents, có nên formalize "read-only roles vs write roles" thành C-008a hay đợi thêm sample?
- **Reason**: G-009 nice-to-have, sample size concern.
- **Source**: `08-knowledge-gaps.md` G-009
- **Default suggestion**: Defer until sample size ≥ 8 sub-agents (workspace với apps thực sẽ có nhiều agents hơn).

### q-022  [P2]  Rerun với --allow-configs?
- **Question**: G-008 — Section 3 (configs) + Section 8 (hooks) chưa analyze. Rerun `/code-analyze --allow-configs` trong phiên này? Sẽ tạo evid-id mới `refresh-wiki-template-2026-05-08`.
- **Reason**: G-008 nice-to-have. Hooks có thể chứa automated behavior cần document.
- **Source**: `08-knowledge-gaps.md` G-008
- **Default suggestion**: Defer cho phiên riêng — keep current evid-id minimal, focus on apply BLOCKING gaps trước.

---

## P3 — Counter-arguments (sanity checks)

### q-023  [P3]  Có lý do gì pattern P-001..P-008 KHÔNG nên canonicalize?
- **Question**: Engine wiki tự document chính nó — có nguy cơ pattern docs lặp lại spec docs (`agents/pipeline/*.md`)? Boundary giữa "engine spec" và "platform pattern" là gì?
- **Reason**: Self-referential workspace dilemma.
- **Source**: raw.md Section 10 item 5 — workspace `wiki` self-referential observation.
- **Default suggestion**: Patterns trong `{ws}/platform/patterns/` describe **what to apply** (action-oriented); spec trong `agents/pipeline/` describe **how engine works** (architecture-oriented). Different audiences (user của engine vs maintainer của engine).

### q-024  [P3]  Có lý do gì introduce variant=agentic-engine là sai design?
- **Question**: Alternative: thay vì variant, có thể design `source_type=engine` (parallel với code/paste/api/mcp). Tại sao chọn variant approach?
- **Reason**: Sanity check decision G-004.
- **Source**: G-004 alternatives section.
- **Default suggestion**: Variant approach giữ source_type finite (4 values) + sub-discriminator inside. `source_type=engine` sẽ explode source_type space khi thêm variant tương lai (infra, data-pipeline, ...). Variant scales better.

---

## Summary

| Priority | Count | List |
|----------|-------|------|
| P0 | 14 | q-001..q-014 (8 patterns + 6 contracts) |
| P1 | 5 | q-015..q-019 (doc strategy + ADRs + orphan fix) |
| P2 | 3 | q-020..q-022 (refinements) |
| P3 | 2 | q-023..q-024 (counter-arguments) |

**Total**: 24 questions.

`/evidence-qa --id 2026-05-08-engine-bootstrap-wiki-template` sẽ run C8 QA Recommender cho P0/P1 (19 questions) trước batch-1, P2/P3 user trả lời trực tiếp.
