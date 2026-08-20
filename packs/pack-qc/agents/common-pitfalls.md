# pack-qc — Top 10 Common Pitfalls

Anti-pattern lặp lại với QA/testing. Additive trên [constraints.md](constraints.md).

## P01 — Mock thay vì integration cho path critical
- **NG**: payment flow chỉ unit test với mock DB.
- **OK**: integration test với real DB/test container.
- **Why**: mock không phản ánh migration / lock / transaction thực.
- **Detect**: Layer-2 — critical path có integration suite.
- **Severity**: error

## P02 — Flaky test ignore / retry không track
- **NG**: thêm `@retry(3)` cho flaky test, quên.
- **OK**: log flake, owner, root cause; quarantine có deadline.
- **Why**: flake che bug thật; CI noise.
- **Detect**: Layer-2 — CI có flake tracker.
- **Severity**: error

## P03 — Coverage số nhưng không assert behavior
- **NG**: test chạy hết function nhưng chỉ check `not None`.
- **OK**: assert business outcome cụ thể (value, side-effect).
- **Why**: coverage 90% mà bug vẫn ship.
- **Detect**: Layer-2 — assertion must prove the business outcome; coverage alone is insufficient.
- **Severity**: warn

## P04 — Test data hardcode env-specific
- **NG**: `userId = 12345` (id của user staging).
- **OK**: factory/fixture/builder; isolated test data.
- **Why**: test pass staging, fail CI.
- **Detect**: Layer-2 — test có fixture factory.
- **Severity**: warn

## P05 — Missing negative / edge case
- **NG**: chỉ test happy path.
- **OK**: null, empty, max size, unicode, concurrent, timeout.
- **Why**: bug ở boundary là phổ biến nhất.
- **Detect**: Layer-2 — test suite có nhóm "edge cases".
- **Severity**: error

## P06 — Test order-dependent
- **NG**: test B phụ thuộc test A run trước (shared DB state).
- **OK**: isolation per test; setUp/tearDown reset state.
- **Why**: random order = flake.
- **Detect**: Layer-2 — run `--shuffle` không gãy.
- **Severity**: error

## P07 — Fixture leak state cross-test
- **NG**: module-scope fixture mutate, không reset.
- **OK**: function-scope hoặc reset trong teardown.
- **Why**: heisenbug.
- **Detect**: Layer-2 — fixture scope review.
- **Severity**: warn

## P08 — Không separate unit / integration trong CI
- **NG**: mọi test chạy 1 phase, 30 phút mới fail.
- **OK**: phase unit (fast) → integration → e2e; fail fast.
- **Why**: feedback chậm, dev không chạy local.
- **Detect**: Layer-2 — CI config có phase split.
- **Severity**: warn

## P09 — Không snapshot review / approval
- **NG**: snapshot test auto-update silently.
- **OK**: review diff; CI fail nếu snapshot đổi mà chưa approve.
- **Why**: regression slip in.
- **Detect**: Layer-2 — snapshot workflow.
- **Severity**: warn

## P10 — Test không có name mô tả intent
- **NG**: `test_1`, `test_user`.
- **OK**: `test_login_fails_when_password_expired`.
- **Why**: fail report không hiểu, debug chậm.
- **Detect**: Layer-2/linter convention — name communicates behavior and condition.
- **Severity**: info

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 mock | — | ✓ |
| P02 flaky | — | ✓ |
| P03 empty-assert | — | ✓ |
| P04 hardcode-data | — | ✓ |
| P05 edge | — | ✓ |
| P06 order | — | ✓ |
| P07 fixture | — | ✓ |
| P08 CI phase | — | ✓ |
| P09 snapshot | — | ✓ |
| P10 test-name | — | ✓ |

---

# Performance Optimization — Top 10 Pitfalls

## PO01 — Tuning không có baseline metric
- **NG**: "tăng thread pool lên 200" mà không đo trước.
- **OK**: baseline (p50/p95/p99, throughput, error rate) → change → re-measure.
- **Why**: không biết improve hay regress.
- **Detect**: Layer-1 `pack-qc-perf-no-baseline-metric`.
- **Severity**: error

## PO02 — Thiếu regression check plan
- **NG**: optimize handler nhưng không test các path khác.
- **OK**: load test golden scenarios trước/sau; canary deploy.
- **Why**: side-effect ở case không nghĩ tới.
- **Severity**: error

## PO03 — Premature optimization
- **NG**: optimize hot loop trước khi profile.
- **OK**: profile (flame graph, slow query, APM) → optimize top hotspot.
- **Severity**: warn

## PO04 — Micro-bench không reflect prod
- **NG**: JMH local 1 thread → claim 10x faster.
- **OK**: bench với prod-like data, concurrency, network.
- **Severity**: warn

## PO05 — Không A/B compare
- **NG**: rollout 100% rồi nhìn metric global.
- **OK**: compare control/canary cohort; promote theo configured error/latency/business guardrail và rollback trigger.
- **Severity**: warn

## PO06 — Ignore tail latency (p99/p99.9)
- **NG**: optimize average, p95 ổn nhưng p99 tăng 5x.
- **OK**: SLO ràng buộc tail; monitor riêng.
- **Severity**: error

## PO07 — Không profile trước khi guess
- **NG**: "chắc do GC" → tune heap → không cải thiện.
- **OK**: pprof / flame graph / async-profiler trước.
- **Severity**: error

## PO08 — Optimize đổi behavior
- **NG**: cache result lâu hơn → user thấy data cũ.
- **OK**: behavior contract bất biến; nếu đổi → migration plan + user comm.
- **Severity**: error

## PO09 — Cache thiếu invalidation strategy
- **NG**: thêm Redis cache, không nêu TTL / invalidate event.
- **OK**: TTL + event-driven invalidate + jitter + stale-while-revalidate.
- **Severity**: error

## PO10 — Hardcode threshold trong code
- **NG**: `if size > 1000: batch_process()` literal.
- **OK**: config-driven; tunable per env; alert khi crossing.
- **Severity**: info

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| PO01 baseline | `pack-qc-perf-no-baseline-metric` | ✓ |
| PO02 regression | `pack-qc-perf-no-regression-check` | ✓ |
| PO03 premature | `pack-qc-perf-premature-tuning` | ✓ |
| PO04 micro-bench | — | ✓ |
| PO05 A/B | — | ✓ |
| PO06 tail | — | ✓ |
| PO07 profile | `pack-qc-perf-premature-tuning` | ✓ |
| PO08 behavior | — | ✓ |
| PO09 cache-inv | — | ✓ |
| PO10 threshold | — | ✓ |
