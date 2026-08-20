# pack-dba — Prompt Overrides

Section bổ sung vào `agents/pipeline/prompt-template.md` self-check khi pack active.

## Self-Check Constraints (append vào `Constraints to check` của prompt-template)

```
### Schema Change (pack-dba)
- Migration có rollback/forward-fix strategy rõ ràng
- DDL lock/rewrite/replication impact dựa trên exact engine/version + rehearsal/workload evidence
- Applied migration immutable + versioned theo workspace migration tool/contract
- Foreign-key access path/index order được verify từ engine catalog/query plan; không tạo index trùng lặp theo folklore

### Query & Index (pack-dba)
- Query tuning có EXPLAIN plan / slow log / p95 metric evidence
- Index proposal nêu trade-off read vs write vs storage
- Projection explicit trên stable/hot application paths; admin/exploratory exceptions có rationale
- Transaction ngắn, KHÔNG bao external HTTP/IO

### Backup & DR (pack-dba)
- Backup policy có RPO + RTO + restore verification cadence
- Backup failure-domain separation phù hợp threat/RPO/data-residency policy
- Restore drill còn hiệu lực theo risk/RPO/RTO policy và có verification evidence
```

## Layer-2 LLM self-check (append vào validator-rules Layer 2)

```md
### Database Administration
- Schema change có rollback hoặc forward-fix
- Lock/rewrite impact được evidence bằng engine capability, plan/rehearsal và workload shape
- Query recommendation có EXPLAIN before/after
- Query projection phù hợp contract và measured cost; broad projection exceptions reviewable
- Backup doc có RPO/RTO/restore drill
- Query observability/slow-capture mechanism phù hợp engine, workload và privacy policy
- Foreign-key access path/index order được verify theo engine; không tạo index trùng lặp cảm tính
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
