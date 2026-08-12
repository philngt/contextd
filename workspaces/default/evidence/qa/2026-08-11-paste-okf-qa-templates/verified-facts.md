# Verified Facts — Evidence `2026-08-11-paste-okf-qa-templates`

## Block: Templates (QA pipeline)

### F-001 — Evidence QA files không bị OKF lint flag

- **Confidence**: high
- **Source**: q-001 (self) — answered 2026-08-11
- **Affects**: `../../../scripts/lint-wiki.py`, `../../../scripts/test_lint_wiki.py`

`check_workspace_okf` exclude `evidence/` subtree — runtime artifacts (batch-N-answers.md, pending-external.md, recommendations.md) không phải concept files, không bị flag thiếu/unknown type. Có test riêng cover.

### F-002 — Placeholder trong frontmatter render ra YAML hợp lệ

- **Confidence**: high
- **Source**: q-002 (self) — answered 2026-08-11
- **Affects**: `../../../templates/evidence-qa-answers.md`, `../../../templates/evidence-qa-recommendations.md`, `../../../templates/evidence-pending-external.md`

`generated: { by: process:evidence-qa, at: {ISO timestamp} }` khi thay placeholder bằng ISO timestamp chuẩn (`2026-08-11T10:32:00+07:00`) vẫn là flow-mapping YAML hợp lệ — chứng minh bằng batch-1-answers.md/batch-2-answers.md render từ template (frontmatter parse thành công).

### F-003 — Append-only I-6 không bị frontmatter phá

- **Confidence**: high
- **Source**: q-003 (self) — answered 2026-08-11
- **Affects**: `../../../templates/evidence-qa-answers.md`

I-6 áp dụng cho `## q-XXX` entries (update = entry mới + `supersedes:`); frontmatter là metadata block cố định trước `---`, append diễn ra sau marker comment. Không overlap.

## Open / deferred (informational, không block apply)

- **08-knowledge-gaps gap #1 (blocking, đã resolve)**: "Chưa chạy QA end-to-end trên evidence set thật" — fixture này đã chạy trọn pipeline, gap đóng.
- Nice-to-have gap #1: C8 recommendations chưa chạy với `source_type=code` (fixture dùng paste) — không block, chạy độc lập khi có code evidence.
