# 04 — Question Pool

## Block 1 — Core questions (10)

### q-001 [P0 — Blocking]
**Question**: Evidence QA files được pipeline sinh ra (`batch-{N}-answers.md`, `pending-external.md`, `recommendations.md`) có bị OKF lint flag thiếu/unknown type không?
**Context**: lint-wiki.py thêm OKF checks nhưng evidence/ là runtime artifacts. Raw evidence: related change nói exclude `evidence/` subtree.
**Liên quan**: scripts/lint-wiki.py `check_workspace_okf`; test_okf_skips_evidence_runtime_artifacts.
**Ảnh hưởng**: nếu KHÔNG exclude → mọi evidence set hiện tại + tương lai sẽ warning ồn ào, exit 2.

### q-002 [P0 — Blocking]
**Question**: Frontmatter chứa placeholder (`{by: process:evidence-qa, at: {ISO timestamp} }`) — khi pipeline render thay `{ISO timestamp}` bằng timestamp thật, YAML flow-mapping có còn hợp lệ không?
**Context**: `generated: { by: ..., at: ... }` là flow-mapping. Nếu placeholder thay bằng chuỗi có space/quote → vỡ YAML → conformance fail (OKF yêu cầu frontmatter parseable).
**Liên quan**: templates/evidence-qa-answers.md#L5; OKF SPEC conformance = parseable frontmatter.

### q-003 [P1]
**Question**: Frontmatter ở đầu file có phá append-only invariant I-6 không (entry mới append sau `## q-XXX`, không sửa cũ)?
**Context**: I-6 yêu cầu `batch-{N}-answers.md` append-only, update = entry mới với `supersedes:`. Frontmatter nằm trước phần nội dung, không đụng tới sections.
**Liên quan**: agents/pipeline/evidence-lifecycle.md#I-6; template comment "Append future entries dưới dòng này".

## Block 2 — Unanswered by raw (5)

_(none — raw evidence là diff excerpt đầy đủ của thay đổi under test)_

## Block 3 — Game-changers (3)

_(none)_

## Block 4 — Counter-arguments

_(none)_
