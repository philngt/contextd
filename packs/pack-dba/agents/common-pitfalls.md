# pack-dba — Top 10 Common Pitfalls

Anti-pattern lặp lại với schema / query / backup. Additive trên [constraints.md](constraints.md).

## P01 — Schema change thiếu rollback plan
- **NG**: PR `ALTER TABLE ... DROP COLUMN` không nêu rollback.
- **OK**: doc rollback (down-migration) hoặc forward-fix strategy.
- **Why**: prod fail → không revert được.
- **Detect**: Layer-1 `pack-dba-migration-no-rollback`.
- **Severity**: error

## P02 — ALTER blocking lock không announce
- **NG**: `ALTER TABLE big_table ADD COLUMN ... NOT NULL DEFAULT ...` chạy prod giờ peak.
- **OK**: online schema change (gh-ost / pt-osc); maintenance window; review impact scope.
- **Why**: full-table lock → outage.
- **Detect**: Layer-2 — migration doc có `maintenance_window|online_change`.
- **Severity**: error

## P03 — Index không evidence-based
- **NG**: "thêm index cho fast" mà không EXPLAIN / metric.
- **OK**: kèm EXPLAIN before/after, p95 query metric.
- **Why**: index thừa = write slow, storage tốn.
- **Detect**: Layer-1 `pack-dba-query-no-evidence`.
- **Severity**: warn

## P04 — SELECT * trong production query
- **NG**: `SELECT * FROM orders WHERE ...` từ application.
- **OK**: liệt kê column cần.
- **Why**: payload bloat, break khi schema đổi, index không cover được.
- **Detect**: Layer-1 `pack-dba-select-star` (regex heuristic ngoài migration/admin context).
- **Severity**: warn

## P05 — Backup thiếu restore verification
- **NG**: backup chạy mỗi đêm nhưng chưa từng restore thử.
- **OK**: automated restore-test theo RPO/RTO + risk policy; log recovered point, duration và verification queries.
- **Why**: ngày cần restore mới biết backup hỏng.
- **Detect**: Layer-1 `pack-dba-no-restore-verification`.
- **Severity**: error

## P06 — Schema change không version
- **NG**: edit migration cũ; không sequence number/timestamp.
- **OK**: migration tool (Flyway/Alembic/Prisma); immutable history.
- **Why**: out-of-sync giữa env, replay break.
- **Detect**: Layer-2 — repo có migration folder + tool config.
- **Severity**: error

## P07 — Không verify foreign-key access path
- **NG**: giả định mọi engine xử lý FK/index giống nhau, hoặc tạo index trùng mà không xem column order/query plan.
- **OK**: inspect engine-generated/declared indexes trên referencing và referenced columns; verify delete/update/query plan và redundancy.
- **Why**: missing/wrong-order index gây scan/lock; redundant index tăng write/storage cost. MySQL/InnoDB có thể tự tạo index cần cho FK.
- **Detect**: Layer-2 — compare actual catalog/index order với FK và workload.
- **Severity**: warn

## P08 — Transaction quá dài
- **NG**: open transaction → call HTTP/external → commit.
- **OK**: transaction chỉ bao DB ops; external IO ngoài tx.
- **Why**: lock contention, connection pool starve.
- **Detect**: Layer-2 — review tx scope.
- **Severity**: error

## P09 — Backup policy thiếu RPO/RTO
- **NG**: doc "backup mỗi ngày" nhưng không nêu RPO/RTO.
- **OK**: RPO (max data loss), RTO (max recovery time) explicit + monitored.
- **Why**: SLA không đo được; expectation không khớp business.
- **Detect**: Layer-1 `pack-dba-backup-no-rpo-rto`.
- **Severity**: error

## P10 — Không monitor slow query
- **NG**: prod chạy, không slow query log / pg_stat_statements.
- **OK**: enable slow log + alert threshold; weekly review top-N.
- **Why**: degradation gradual không detect, đến khi user complain.
- **Detect**: Layer-2 — observability config.
- **Severity**: warn

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 rollback | `pack-dba-migration-no-rollback` | ✓ |
| P02 blocking-lock | — | ✓ |
| P03 evidence | `pack-dba-query-no-evidence` | ✓ |
| P04 select-* | `pack-dba-select-star` | ✓ |
| P05 restore-verify | `pack-dba-no-restore-verification` | ✓ |
| P06 ver-mig | — | ✓ |
| P07 fk-idx | — | ✓ |
| P08 long-tx | — | ✓ |
| P09 rpo-rto | `pack-dba-backup-no-rpo-rto` | ✓ |
| P10 slow-log | — | ✓ |
