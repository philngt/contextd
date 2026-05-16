# Q&A Answers — Batch 6

**Evidence ID**: `2026-05-08-engine-bootstrap-wiki-template`
**Batch**: 6 | **Priority**: P1+P2 | **Asked at**: 2026-05-08T00:00:00+07:00 | **Count**: 4

---

## q-019 — /wiki-viz orphan README fix
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●●) | **Confidence**: high
- **Answer**: Tách phiên. Apply evidence này trước. Sau đó chạy `/update-wiki --scope .claude/commands/README.md` để add row cho `/wiki-viz` Section "Pipeline observability". KHÔNG tạo ADR (bug fix only).
- **Cited**: `(a06-decision-drafts.md#D-005)`, `(08-knowledge-gaps.md#G-006)`

## q-020 — Pipeline support docs README table extend
- **Status**: deferred (P2 nice-to-have, no expert) | **By**: self | **Confidence**: medium
- **Answer**: Defer cho phiên riêng. File `agents/pipeline/README.md` table list 7/16 docs nhưng files thực tế đều tồn tại trong dir → navigable. Low urgency.
- **Cited**: `(08-knowledge-gaps.md#G-007)`

## q-021 — Tools allowlist principle (C-008a)
- **Status**: deferred (sample concern) | **By**: self | **Confidence**: medium
- **Answer**: Defer until sample size ≥ 8 sub-agents. Hiện 5/5 follow read-only/write-allowed split nhưng có thể là coincidence — workspace với apps thực sẽ có nhiều agents hơn để verify principle.
- **Cited**: `(a04-contract-proposals.md#C-008)` Recommendation note, `(08-knowledge-gaps.md#G-009)`

## q-022 — Rerun /code-analyze --allow-configs phiên này
- **Status**: deferred (P2) | **By**: self | **Confidence**: high
- **Answer**: Defer cho phiên riêng. Keep current evid-id minimal, focus apply BLOCKING gaps trước. Rerun sau với label `refresh-wiki-template-{later-date}` → tạo evid-id mới → re-run a07 với Section 3/8 populated.
- **Cited**: `(08-knowledge-gaps.md#G-008)`, `(a07-settings-overrides.md)` Next steps section

---

## Mini Contradiction Hunter
- All 4 answers compatible — q-019..q-022 đều choose defer/separate session, consistent với apply order plan.
- No conflicts.

---

## P0+P1 batch summary

After Batch 6: **all 14 P0 + 5 P1 = 19 P0/P1 questions resolved**:
- P0: 14 answered (13 accept gợi ý + 1 user-override q-007)
- P1: 5 answered (4 accept gợi ý + 1 deferred q-019 → tách phiên fix)
- 0 awaiting_external
- Wait, q-019 is technically "answered" with action plan = tách phiên. Not deferred.

Recount:
- P0: 14 answered (0 deferred, 0 awaiting_external, 0 skipped)
- P1: 5 answered (0 deferred, 0 awaiting_external, 0 skipped)
- P2: 3 deferred (q-020, q-021, q-022)
- P3: 2 pending (q-023, q-024)

State ready for Bước 5 stop check.
