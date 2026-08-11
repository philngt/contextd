# 01 — Resource Upload Summary

## Core themes (3)

1. **OKF frontmatter added to 3 QA templates** — `evidence-qa-answers.md`, `evidence-qa-recommendations.md`, `evidence-pending-external.md` mỗi file có `type: Evidence` + `title`/`description`/`generated` với placeholders `{N}`, `{evid-id}`, `{ISO timestamp}`.
2. **evidence/ subtree excluded từ OKF lint** — `lint-wiki.py` skip `evidence/` runtime artifacts (không phải concept files), có test `test_okf_skips_evidence_runtime_artifacts`.
3. **Pipeline consumers giữ nguyên cách dùng** — answers template render `batch-{N}-questions.md`/`batch-{N}-answers.md`; recommendations template là C8 output schema; pending-external theo I-7 lifecycle.

## Internal consistency

### Consistent
- Cả 3 template dùng cùng pattern frontmatter (`type: Evidence`, `generated: { by: process:evidence-qa, ... }`) — khớp actor convention `process:<id>`.
- Frontmatter xuất hiện 1 lần ở đầu file, append-only sections (`## q-XXX`) nằm sau `---` — không phá format parse theo heading.

### Contradictory
- Không có contradiction nội bộ.

## Surprising findings
- Placeholders sống **bên trong YAML flow-mapping** (`generated: { by: ..., at: {ISO timestamp} }`) — phải render thành timestamp ISO hợp lệ thì YAML mới parse được; nếu pipeline thay placeholder bằng text bất kỳ có thể phá frontmatter.

## Open issues raised but unanswered
- Chưa có evidence set thật nào chạy QA end-to-end với template mới — chính là mục tiêu verification của fixture này.
