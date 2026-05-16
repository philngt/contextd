# Q&A Answers — Batch 1

**Evidence ID**: `2026-05-08-engine-bootstrap-wiki-template`
**Batch**: 1
**Priority bucket**: P0
**Asked at**: 2026-05-08T00:00:00+07:00
**Question count**: 4

---

## q-001 — Pattern P-001 workspace-resolve-step0

- **Status**: answered
- **Answered at**: 2026-05-08T00:00:00+07:00
- **Answered by**: self
- **Via**: code-analyst-recommend (confidence: high — ●●●)
- **Confidence**: high

**Answer**:
> Có, thêm vào `{ws}/platform/patterns/workspace-resolve-step0.md`. Pattern là engine-level invariant — apply cho mọi command future. Workspace override KHÔNG apply (engine invariant). Use canonical 5-step structure trong a03#P-001.

**Evidence cited**:
- `(workspaces/wiki/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md#P-001)` — 15 occurrences
- `(.claude/commands/code-analyze.md:L26-L36)` — canonical example
- `(agents/system-prompt.md)` — wiki_root resolution rule

---

## q-002 — Pattern P-002 askuser-confirm-preview

- **Status**: answered
- **Answered at**: 2026-05-08T00:00:00+07:00
- **Answered by**: self
- **Via**: code-analyst-recommend (confidence: medium — ●●○)
- **Confidence**: medium

**Answer**:
> Có, thêm vào `{ws}/platform/patterns/askuser-confirm-preview.md`. Apply: mọi command có side effects filesystem (tạo evidence, edit wiki, scaffold workspace). Canonical: preview block + AskUserQuestion 3 options (primary action / edit-detail / cancel). Cancel BẮT BUỘC.

**Evidence cited**:
- `(workspaces/wiki/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md#P-002)` — 4 occurrences
- `(.claude/commands/code-analyze.md:L106-L182)` — canonical preview block

---

## q-003 — Pattern P-003 secrets-blocklist-gate

- **Status**: answered
- **Answered at**: 2026-05-08T00:00:00+07:00
- **Answered by**: self
- **Via**: code-analyst-recommend (confidence: high — ●●●)
- **Confidence**: high

**Answer**:
> Có, thêm vào `{ws}/platform/patterns/secrets-blocklist-gate.md`. Security-critical pattern — apply cho mọi command đọc file content nhạy cảm (configs, credentials, ingestion từ external sources có sensitive data). 5 tầng theo a03#P-003.

**Evidence cited**:
- `(workspaces/wiki/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md#P-003)`
- `(agents/pipeline/code-snapshot-conventions.md:L156-L251)` — full spec
- `(.claude/commands/code-analyze.md:L207-L229)` — Bước 4.3 implementation

---

## q-004 — Pattern P-004 redaction-post-pass

- **Status**: answered
- **Answered at**: 2026-05-08T00:00:00+07:00
- **Answered by**: self
- **Via**: code-analyst-recommend (confidence: high — ●●●)
- **Confidence**: high

**Answer**:
> Có, thêm vào `{ws}/platform/patterns/redaction-post-pass.md`. Companion với P-003 (`secrets-blocklist-gate.md`). Apply cho mọi output có khả năng chứa secrets (snapshots, logs, qa exports, reports). STOP-on-secret = irreversible: KHÔNG ghi file output nếu còn match.

**Evidence cited**:
- `(workspaces/wiki/evidence/analysis/2026-05-08-engine-bootstrap-wiki-template/a03-pattern-proposals.md#P-004)`
- `(.claude/commands/code-analyze.md:L274-L282)` — Bước 4.10
- `(agents/pipeline/code-snapshot-conventions.md:L218-L238)` — Section 6.2

---

## Mini Contradiction Hunter (Bước 4d)

- Cross-check với answers cũ (none — first batch).
- Cross-check với 02-contradiction.md (N/A — agentic-engine pipeline không có file này).
- Cross-check với wiki của workspace `wiki` (empty — no conflicts possible).
- **Result**: no contradictions detected.
