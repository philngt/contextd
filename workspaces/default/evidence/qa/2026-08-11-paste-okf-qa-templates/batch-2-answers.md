---
type: Evidence
title: "Q&A Answers — Batch 2"
description: "Append-only answers cho batch 2 của evidence 2026-08-11-paste-okf-qa-templates"
generated: { by: process:evidence-qa, at: 2026-08-11T10:32:30+07:00 }
---

# Q&A Answers — Batch 2

> Append-only. KHÔNG sửa câu trả lời cũ. Nếu sai → tạo entry mới với `supersedes: <q-id>@<timestamp>`.

**Evidence ID**: `2026-08-11-paste-okf-qa-templates`
**Batch**: 2
**Priority bucket**: P1
**Asked at**: 2026-08-11T10:30:00+07:00

---

## q-003 — Frontmatter có phá append-only invariant I-6 không?

- **Status**: answered
- **Answered at**: 2026-08-11T10:32:30+07:00
- **Answered by**: self
- **Confidence**: high

**Answer**:
Không phá. I-6 áp dụng cho phần nội dung `## q-XXX` entries — update = entry mới với `supersedes:` tag. Frontmatter là metadata block cố định ở đầu file (trước `---`), append entries diễn ra sau marker `<!-- Append future entries dưới dòng này. KHÔNG xóa entry cũ. -->`. Hai vùng không overlap.

**Evidence cited**:
- `agents/pipeline/evidence-lifecycle.md` (I-6 append-only logs)
- `templates/evidence-qa-answers.md` (append marker comment)

<!-- Append future entries dưới dòng này. KHÔNG xóa entry cũ. -->
