# Evidence Index — Workspace `wiki`

> Bảng này là single source of truth về state của mọi evidence set trong workspace.
> Updated bởi `/evidence-{ingest,analyze,qa,apply,archive}`.
> KHÔNG sửa tay (sẽ bị overwrite). Nếu cần đổi state thủ công, edit và mark dòng có dấu `(manual)`.

## Active

| evid-id | source | label | state | created | last_updated | blocked_on | applied_to |
|---------|--------|-------|-------|---------|--------------|------------|------------|
| 2026-05-08-engine-bootstrap-wiki-template | code | bootstrap-wiki-template | applied | 2026-05-08 | 2026-05-08 | — | patterns-index.md, platform/patterns/ (8), platform/contracts/ (8), projects/engine/ (8), decisions/ (4) |

## Archived

| evid-id | source | label | applied_to | archived |
|---------|--------|-------|------------|----------|

---

## State legend

- **ingested** — raw data đã ghi, chưa analyze
- **analyzed** — CORE prompts đã chạy (text: 4 prompts; code: c01–c04 + 04 + 08; agentic-engine: a01–a04 + 04 + 08)
- **qa_in_progress** — đang trong Q&A loop với user
- **qa_awaiting_external** — chờ expert trả lời (xem `blocked_on`)
- **qa_done** — verified-facts.md đã ghi
- **applied** — wiki đã được update; xem `applied_to` cho list file
- **archived** — moved sang `archive/`, history only

## State transitions

```
ingested → analyzed → qa_in_progress ⇄ qa_awaiting_external → qa_done → applied → archived
```

Xem chi tiết: `agents/pipeline/evidence-lifecycle.md`.
