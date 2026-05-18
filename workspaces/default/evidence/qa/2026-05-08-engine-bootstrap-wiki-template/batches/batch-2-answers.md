# Q&A Answers — Batch 2

**Evidence ID**: `2026-05-08-engine-bootstrap-wiki-template`
**Batch**: 2
**Priority bucket**: P0
**Asked at**: 2026-05-08T00:00:00+07:00
**Question count**: 4

---

## q-005 — P-005/C-005 evidence-state-machine pairing

- **Status**: answered
- **Answered at**: 2026-05-08T00:00:00+07:00
- **Answered by**: self
- **Via**: code-analyst-recommend (confidence: high — ●●●)
- **Confidence**: high

**Answer**:
> PAIR. Tạo cả 2 docs với cross-reference:
> - `{ws}/platform/patterns/evidence-state-machine.md` — implementation skeleton (states, transitions, storage location).
> - `{ws}/platform/contracts/evidence-state-machine-transitions.md` — invariant rules (transition ownership, no-skip, _index.md as SoT, I-2 lock).
> Pattern doc cite contract; contract doc cite pattern.

**Evidence cited**:
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md#P-005)`
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a04-contract-proposals.md#C-005)`
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a06-decision-drafts.md#D-004)` — pairing convention

---

## q-006 — P-006/C-006 citation-rule + citation-format pairing

- **Status**: answered
- **Answered at**: 2026-05-08T00:00:00+07:00
- **Answered by**: self
- **Via**: code-analyst-recommend (confidence: high — ●●●)
- **Confidence**: high

**Answer**:
> PAIR. Tạo:
> - `{ws}/platform/patterns/citation-rule.md` — implementation skeleton (path format, bundle prefix variant).
> - `{ws}/platform/contracts/citation-format.md` — invariant + validator behavior (reject paths absolute / cross-workspace / outside scope).
> Cross-reference 2 chiều.

**Evidence cited**:
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md#P-006)`
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a04-contract-proposals.md#C-006)`
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a06-decision-drafts.md#D-004)`

---

## q-007 — P-007 multi-stage-subagent-pipeline (NOT flagship)  [USER OVERRIDE]

- **Status**: answered
- **Answered at**: 2026-05-08T00:00:00+07:00
- **Answered by**: self
- **Via**: user-override (chose "Thêm nhưng KHÔNG làm flagship" — diverged from gợi ý)
- **Confidence**: high

**Answer**:
> Thêm pattern doc tại `{ws}/platform/patterns/multi-stage-subagent-pipeline.md` theo a03#P-007 canonical structure. KHÔNG đặt top of `{ws}/patterns-index.md` (flagship status declined). KHÔNG cross-reference từ `{ws}/workspace.md`. Pattern được liệt kê trong patterns-index theo thứ tự alphabetical hoặc theo grouping bình thường.

**Evidence cited**:
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md#P-007)`
- `(agents/pipeline/README.md:L27-L46)` — 5-stage diagram
- `(.claude/commands/contextd-use.md:L1)` — implementation

**Note**: Apply step phải skip "FLAGSHIP top of patterns-index" + skip workspace.md cross-ref. Pattern doc bình thường.

---

## q-008 — P-008 variant-discriminated-dispatcher (add NOW with note)

- **Status**: answered
- **Answered at**: 2026-05-08T00:00:00+07:00
- **Answered by**: self
- **Via**: code-analyst-recommend (confidence: medium — ●●○)
- **Confidence**: medium

**Answer**:
> Có, thêm với note "single instance — pattern shape may evolve khi variant thứ 3 được introduce". File: `{ws}/platform/patterns/variant-discriminated-dispatcher.md`. Document 6 bước canonical (detect → validation gate → scope default → output template → source.yaml field → downstream dispatch). Version: v1; revisit khi có variant thứ 3.

**Evidence cited**:
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md#P-008)`
- `(.claude/commands/code-analyze.md:L43-L70)` — Bước 1.4 detect
- `(workspaces/default/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a06-decision-drafts.md#D-001)`

---

## Mini Contradiction Hunter (Bước 4d)

- q-007 user override: KHÔNG mâu thuẫn với answers trước (P-001..P-004 không đụng tới flagship status). Nhưng cần align a06 D-003 (self-referential workspace) — D-003 không claim P-007 phải là flagship, chỉ giải thích boundary spec/pattern. Compatible.
- No conflict với 02-contradiction.md (file không tồn tại — agentic-engine pipeline).
- Workspace `wiki` empty → no conflict possible.
- **Result**: no contradictions detected.
