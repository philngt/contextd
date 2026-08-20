# pack-qc — Constraints

Additive constraints cho quality control **và performance optimization** workflow. Strict-only direction.

> Pack này gộp `pack-optimize` (v0.1) — phần performance đặt ở section riêng "Performance Optimization" bên dưới.

## Quality Gate Integrity (`pack-qc-quality-gate`)

- Mọi khuyến nghị release PHẢI dựa trên evidence test execution (pass/fail counts hoặc defect trend), không quyết định theo cảm tính.
- Không được gắn trạng thái `passed` khi còn defect severity cao chưa có decision rõ ràng (fix/defer + risk accepted).

## Defect Traceability (`pack-qc-defect-traceability`)

- Bug report PHẢI có tối thiểu: steps to reproduce, expected result, actual result.
- Severity và priority phải tách biệt; không dùng thay thế cho nhau.

## Regression Discipline (`pack-qc-regression-discipline`)

- Thay đổi scope release PHẢI kéo theo cập nhật regression scope tương ứng.
- Không bỏ regression critical path khi chưa có risk acceptance rõ ràng từ stakeholder chịu trách nhiệm.

---

# Performance Optimization

Constraints áp dụng cho performance/tuning work.

## Evidence (`pack-qc-evidence`)

- **Mọi đề xuất optimize PHẢI có baseline metric + target metric** — số cụ thể với percentile + sample size + workload condition.
- **KHÔNG đề xuất tuning khi chưa có bằng chứng bottleneck** — profile/flame graph/APM/slow log trước, optimize sau.
- **Bottleneck claim PHẢI có data artifact attach** — pprof file, flame graph image, APM trace URL, slow query entry.

## Behavior & Regression (perf) (`pack-qc-performance-behavior`)

- **Tối ưu thay đổi behavior PHẢI có regression check plan** — golden scenarios chạy before/after, diff verified.
- **KHÔNG thay đổi behavior contract** (semantics, ordering, freshness) dưới danh nghĩa optimize. Đổi → migration plan + user comm.
- **Cache thêm mới PHẢI có invalidation strategy** — TTL + event-driven invalidate + jitter + stale-while-revalidate.

## Measurement (`pack-qc-measurement`)

- **Track distribution/tail metric relevant với SLO và traffic volume** — không chỉ average; chọn percentile/window đủ sample và giải thích vì sao.
- **Benchmark PHẢI reflect production** — workload size, concurrency, network condition gần prod.
- **A/B/canary compare PHẢI dùng cohort** — phase size, hold time và promotion threshold đến từ release risk/SLO/config; KHÔNG hardcode một chuỗi phần trăm hoặc rollout toàn bộ rồi mới nhìn global metric.

## Rollout (`pack-qc-rollout`)

- **Optimize có behavior delta PHẢI feature flag** + kill-switch.
- **Rollout PHẢI document rollback trigger** (metric threshold, error rate) + decision owner.

## Config (perf) (`pack-qc-config`)

- **Threshold PHẢI từ config**, KHÔNG hardcode literal trong hot path — tunable per env, alert khi crossing.
- **Resource limit (thread pool, connection, batch size) PHẢI từ config** với default + tuning notes.

---

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../../agents/cross-cutting-principles.md)

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
