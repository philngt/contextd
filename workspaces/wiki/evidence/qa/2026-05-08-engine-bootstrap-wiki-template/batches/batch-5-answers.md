# Q&A Answers — Batch 5

**Evidence ID**: `2026-05-08-engine-bootstrap-wiki-template`
**Batch**: 5 | **Priority**: P1 | **Asked at**: 2026-05-08T00:00:00+07:00 | **Count**: 4

---

## q-015 — Doc grouping strategy
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●●) | **Confidence**: high
- **Answer**: Option B — 6 group docs theo category + 1 agents doc tại `{ws}/projects/engine/services/`. a05 đã draft sẵn 7 files (workspace-ops, wiki-usage, codebase-analysis, reporting, observability, evidence-pipeline, agents). Apply ngay từ a05 drafts.
- **Cited**: `(a05-doc-drafts.md#DRAFT-G1..G6)`, `(08-knowledge-gaps.md#G-003)`

## q-016 — Doc location
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●●) | **Confidence**: high
- **Answer**: `{ws}/projects/engine/services/{group-name}.md`. Treat engine như 1 project. Reuse workspace structure (no special namespace). Decision documented trong D-003 ADR.
- **Cited**: `(CLAUDE.md:L77-L80)`, `(a05-doc-drafts.md)`, `(a06-decision-drafts.md#D-003)`

## q-017 — Apply ADR D-001 variant=agentic-engine
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●●) | **Confidence**: high
- **Answer**: Có, apply D-001 thành ADR `{ws}/decisions/001-introduce-agentic-engine-variant.md` từ a06 draft. Use template `templates/adr.md`. Status field = "ACCEPTED" (vì decision đã thực thi trong session 2026-05-08).
- **Cited**: `(a06-decision-drafts.md#D-001)`, `(08-knowledge-gaps.md#G-004)`

## q-018 — Split or keep code-analysis-prompts.md
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●●) | **Confidence**: high
- **Answer**: KEEP per D-002. Apply ADR `{ws}/decisions/002-keep-code-analysis-prompts-monolithic.md`. Revisit triggers documented inline (>1500 lines / variant #3 / user feedback).
- **Cited**: `(a06-decision-drafts.md#D-002)`, `(agents/pipeline/code-analysis-prompts.md:L1-L920)`

---

## Mini Contradiction Hunter
- q-016 (projects/engine/) align với q-015 (a05 drafts use this location). Compatible.
- q-017 ACCEPTED status implies decision đã happen — match D-004 pattern-contract pairing also already executed in batches 1-4. Compatible.
- No conflicts.
