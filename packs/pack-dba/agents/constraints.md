# pack-dba — Constraints

Hard rules cho database administration (schema/query/backup/operational). Additive trên engine constraints. Strict-only direction.

## Schema Change (`pack-dba-schema-change`)

- **Mọi thay đổi schema PHẢI có rollback plan hoặc forward-fix strategy rõ ràng** — không chấp nhận "deploy rồi xử lý sau".
- **Applied migration PHẢI immutable + versioned** theo workspace migration ledger/tool; pre-apply drafts may be revised, executed history is superseded by a new migration/repair process.
- **DDL có khả năng lock/rewrite lớn PHẢI nêu execution strategy** + impact scope dựa trên engine/version, plan, table shape, write rate và rehearsal. Không chọn online-schema tool chỉ từ row count.
- **Foreign-key access path PHẢI được verify** trên cả referencing/referenced side theo engine và column order. MySQL/InnoDB có thể tự tạo index cần thiết; vẫn review index redundancy và query/lock behavior thay vì ghi giả định sai về engine.

## Query & Index (`pack-dba-query-index`)

- **Query tuning recommendation PHẢI dựa trên evidence** — actual/estimated plan, representative latency/distribution, waits/slow capture or equivalent chosen for the engine/workload. KHÔNG tối ưu cảm tính.
- **Index proposal PHẢI nêu trade-off** — read benefit vs write cost vs storage; verify by EXPLAIN before/after.
- **Application query has an explicit projection contract** on stable/hot/public paths; broad projection is allowed only when schema coupling and measured cost are intentionally accepted (for example controlled admin/exploration).
- **Transaction PHẢI ngắn + chỉ bao DB ops** — KHÔNG gọi HTTP / external service / sleep trong open transaction.

## Backup & DR (`pack-dba-backup-restore`)

- **Backup policy PHẢI nêu RPO + RTO** với số cụ thể; KHÔNG "best effort".
- **Backup PHẢI có restore verification theo risk policy** — cadence xuất phát từ RPO/RTO, change rate, data criticality và evidence lần drill gần nhất; backup chưa từng restore-test không được coi là proven.
- **Backup copies span the failure domains in the threat/RPO model** and comply with residency/sovereignty policy. Offsite/cross-region/immutable/offline controls are selected from that model, not mandated identically for every production dataset.

## Operational (`pack-dba-operations`)

- **Query telemetry PHẢI bật với sampling/redaction phù hợp**; alert threshold và review cadence thuộc workload SLO/config, không hardcode trong pack.
- **Connection pool size PHẢI từ config**, không hardcode; saturation alert dựa trên measured queueing/timeout headroom.
- **Incident DB PHẢI nêu blast radius** + recovery checkpoints + data-loss estimate.

## Knowledge (`pack-dba-knowledge`)

- **KHÔNG đoán schema** — đọc actual `\d table` / migration history; rebase wiki nếu drift.
- **KHÔNG copy query pattern từ workspace khác** — local data shape có thể khác.

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
