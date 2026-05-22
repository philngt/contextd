# pack-dba — Prompt Overrides

Section bổ sung vào `agents/pipeline/prompt-template.md` self-check khi pack active.

## Self-Check Constraints (append vào `Constraints to check` của prompt-template)

```
### Schema Change (pack-dba)
- Migration có rollback/forward-fix strategy rõ ràng
- DDL có khả năng lock lớn nêu maintenance window + impact scope
- Migration immutable + versioned (tool: Flyway/Alembic/Prisma)
- Foreign key có index trên child column

### Query & Index (pack-dba)
- Query tuning có EXPLAIN plan / slow log / p95 metric evidence
- Index proposal nêu trade-off read vs write vs storage
- Không SELECT * trong application query
- Transaction ngắn, KHÔNG bao external HTTP/IO

### Backup & DR (pack-dba)
- Backup policy có RPO + RTO + restore verification cadence
- Cross-region/offsite copy enabled cho production
- Restore drill log gần nhất < 30 ngày
```

## Layer-2 LLM self-check (append vào validator-rules Layer 2)

```md
### Database Administration
- Schema change có rollback hoặc forward-fix
- Lock impact estimate có cho migration > 1M rows
- Query recommendation có EXPLAIN before/after
- SELECT * chỉ trong migration/admin script
- Backup doc có RPO/RTO/restore drill
- Slow query log enabled + alerting active
- FK column có index
```

## Inclusion logic

Pack loader (`scripts/pack_loader.py`) merge nội dung file này vào prompt context khi build `current-task.md` cho `/use-contextd`.

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS (pack-dba-*)
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
