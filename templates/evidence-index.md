# Evidence Index — Workspace `{ws}`

> Bảng này là single source of truth về state của mọi evidence set trong workspace.
> Updated bởi `/evidence-{ingest,analyze,qa,apply,archive}`.
> KHÔNG sửa tay (sẽ bị overwrite). Nếu cần đổi state thủ công, edit và mark dòng có dấu `(manual)`.

## Active

| evid-id | source | label | state | created | last_updated | blocked_on | applied_to |
|---------|--------|-------|-------|---------|--------------|------------|------------|
| 2026-05-04-paste-PROJ-1234 | paste | PROJ-1234 timeout config change | qa_awaiting_external | 2026-05-04 | 2026-05-04 | be-lead@example.com (q-002, due 2026-05-06) | — |
| 2026-05-03-api-changelog-v2 | api  | Kafka client v2.4 changelog | analyzed | 2026-05-03 | 2026-05-03 | — | — |
| 2026-05-02-paste-incident-kafka-lag | paste | Kafka lag 2026-04 incident | applied | 2026-05-02 | 2026-05-02 | — | runbooks/kafka-lag.md, projects/surgery-service/services/kafka-consumer.md |

## Archived

| evid-id | source | label | applied_to | archived |
|---------|--------|-------|------------|----------|
| 2026-04-15-paste-PROJ-1100 | paste | Old retry config rollback | projects/surgery-service/services/kafka-consumer.md | 2026-04-30 |

---

## State legend

- **ingested** — raw data đã ghi, chưa analyze
- **analyzed** — 4 CORE prompts đã chạy
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
