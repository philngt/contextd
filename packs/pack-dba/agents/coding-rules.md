# pack-dba — Coding Rules

Idioms + preferred patterns cho DBA work. Less strict than constraints — đây là convention, không phải gate.

## Migration Authoring

- Trình bày migration theo thứ tự: **precheck → change → validation → rollback**. Mỗi step là 1 SQL block riêng.
- Precheck: idempotent assertion (`IF NOT EXISTS`, row count check) — re-run an toàn.
- Đặt tên migration: `{timestamp}_{verb}_{object}.sql` (vd `20260518T093000_add_idx_orders_user_id.sql`).
- 1 migration = 1 logical change; KHÔNG bundle nhiều object change vào 1 file.
- Comment trên top file: ticket link, expected duration, lock impact, rollback notes.

## Query Recommendation Format

- Mọi đề xuất index/query nêu **expected trade-off** (read latency / write throughput / storage / cache impact).
- Kèm actual/estimated plan before/after when the engine supports it; nếu chưa chạy được, label hypothesis + required verification rather than presenting a predicted plan as evidence.
- Latency claim PHẢI nêu percentile + sample size + workload condition.
- Recommendation PHẢI link tới slow log entry / dashboard panel cụ thể.

## Index Strategy

- Composite index order follows equality/range predicates, sort/group order, prefix reuse and actual plans; “highest selectivity first” không phải rule chung.
- Partial/filtered index khi engine supports it and predicate/query distribution proves benefit.
- Covering/include index khi actual plan and write/storage trade-off justify an index-only path.
- KHÔNG để index "phòng hờ" — mỗi index có cost trên write path.

## Schema Idioms

- ID type follows scale, distribution, locality, storage/index cost and external-contract needs; document migration headroom instead of prescribing one type globally.
- Timestamp type/precision/timezone and naming follow engine + domain/event contract; distinguish an instant from local civil time and test serialization/round-trip.
- Soft delete, temporal history, or hard delete is a retention/domain decision; if soft-delete is chosen, define uniqueness, filtering, purge and restore semantics.
- Choose enum/check/lookup table from change frequency, referential metadata and engine migration behavior; no blanket ban on native enums.
- JSON column needs schema ownership/validation and query/index strategy; do not use it to bypass a known relational model.

## Backup & Restore Doc

- Doc backup PHẢI nêu: tool, schedule, retention, storage location, encryption, RPO/RTO.
- Restore runbook: step-by-step + estimated time + dependencies + verification query.
- Drill log: lưu policy cadence, date, duration, recovered point, verification result, issues và next due date.

## Incident DB

- Với incident DB, luôn nêu **blast radius** (table/row count affected) và **recovery checkpoints**.
- Nêu recovery paths thực sự được platform support (full, point-in-time, selective/repair) cùng preconditions, data-consistency risk và verification; không invent partial restore nếu chưa proven.
- Postmortem: include slow query / lock graph evidence khi root cause là perf-related.
