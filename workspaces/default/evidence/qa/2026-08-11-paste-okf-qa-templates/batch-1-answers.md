---
type: Evidence
title: "Q&A Answers — Batch 1"
description: "Append-only answers cho batch 1 của evidence 2026-08-11-paste-okf-qa-templates"
generated: { by: process:evidence-qa, at: 2026-08-11T10:32:00+07:00 }
---

# Q&A Answers — Batch 1

> Append-only. KHÔNG sửa câu trả lời cũ. Nếu sai → tạo entry mới với `supersedes: <q-id>@<timestamp>`.

**Evidence ID**: `2026-08-11-paste-okf-qa-templates`
**Batch**: 1
**Priority bucket**: P0
**Asked at**: 2026-08-11T10:30:00+07:00

---

## q-001 — Evidence QA files do pipeline sinh ra có bị OKF lint flag không?

- **Status**: answered
- **Answered at**: 2026-08-11T10:32:00+07:00
- **Answered by**: self
- **Confidence**: high

**Answer**:
Không bị flag. `check_workspace_okf` trong lint-wiki.py skip `evidence/` subtree — evidence QA files là runtime artifacts, không phải concept files. Đã có test `test_okf_skips_evidence_runtime_artifacts` cover trường hợp này.

**Evidence cited**:
- `scripts/lint-wiki.py` (check_workspace_okf — evidence exclusion)
- `scripts/test_lint_wiki.py` (test_okf_skips_evidence_runtime_artifacts)

---

## q-002 — Placeholder trong frontmatter render ra YAML hợp lệ không?

- **Status**: answered
- **Answered at**: 2026-08-11T10:32:00+07:00
- **Answered by**: self
- **Confidence**: high

**Answer**:
Hợp lệ. Flow-mapping `{ by: process:evidence-qa, at: <ISO> }` với ISO timestamp chuẩn (vd `2026-08-11T10:32:00+07:00`) không chứa space/quote đặc biệt → YAML parse thành công. Chính file này (render từ template `evidence-qa-answers.md`) là bằng chứng: frontmatter parse được, placeholders đã được thay bằng giá trị thật.

**Evidence cited**:
- `templates/evidence-qa-answers.md` (frontmatter template — rendered tại file này)
- `workspaces/default/evidence/qa/2026-08-11-paste-okf-qa-templates/batch-1-answers.md` (kết quả render)

<!-- Append future entries dưới dòng này. KHÔNG xóa entry cũ. -->
