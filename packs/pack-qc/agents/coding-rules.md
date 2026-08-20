# pack-qc — Coding Rules

Idioms cho QC writing — test case, bug report, regression plan, release gate. Less strict than constraints — đây là convention.

## Test Case Format

- Cấu trúc: **ID → Preconditions → Steps → Expected → Actual → Status** — 6 element bắt buộc.
- Ưu tiên format checklist ngắn, testable; tránh mô tả mơ hồ ("works correctly").
- 1 test case = 1 verification path; chia khi gặp `and`/`or` composite.
- Test ID stable (`TC-{epic}-{nn}`); link tới requirement ID `R-...`.
- Test name mô tả intent: `test_login_fails_when_password_expired`, KHÔNG `test_1`/`test_user`.

## Acceptance & Test Item Wording

- Mỗi acceptance/test item có **điều kiện vào + kết quả mong đợi** rõ ràng.
- Negative case có riêng (input invalid, permission denied, timeout) — không gộp vào happy path.
- Derive boundary cases từ input/state/risk model (ví dụ empty, range edge, unicode, concurrency); không copy checklist không liên quan.
- Assertion specific: `expect(x).toBe(42)` thay vì `expect(x).toBeTruthy()`.

## Bug Report Format

- Cấu trúc: **Summary → Environment → Repro steps → Expected → Actual → Severity → Priority → Attachments**.
- Severity (impact) tách khỏi Priority (urgency) — không gộp.
- Repro steps: numbered, deterministic, từ clean state.
- Attachment: log, screenshot, HAR, video — redact PII trước upload.
- Defect language nhất quán: `severity`, `priority`, `reproducible`, `blocked`, `ready for retest`, `closed/won't fix`.

## Regression Plan

- Regression suite = test critical path + tests for fixed bugs (regression-of) + smoke.
- Tag test theo scope: `smoke|regression|critical-path|edge`.
- Cadence lấy từ release risk, change frequency và CI budget; ghi rõ trigger cho smoke/regression/full suite.
- Coverage matrix: feature × test type — gap section liệt kê chưa cover.

## Release Quality Gate

- Gate có entry criteria + exit criteria rõ; checklist signed-off mới release.
- Release recommendation luôn nêu **residual risk** còn lại + mitigation tạm thời.
- Go/No-go decision có owner; reason + evidence ghi log permanent.
- Hot-fix process tách khỏi standard release — fast lane định nghĩa trước.

## Test Data Management

- Test data từ factory/builder/fixture; KHÔNG hardcode env-specific (vd `userId=12345` của staging).
- Sensitive test data masked/synthetic; tuyệt đối không production PII trong test env.
- Cleanup sau test (teardown); fixture scope tối thiểu để tránh leak state.

## Automation Idioms

- Test order-independent: `--shuffle` chạy không gãy.
- Flaky test tracker: log occurrence, owner, quarantine deadline; không silent `@retry`.
- Snapshot test có manual review + approval; auto-update là smell.
- CI phase tách: unit (fast) → integration → e2e; fail fast.

## Communication

- Defect triage meeting: dùng severity + priority matrix; SLA per tier.
- Status report cho stakeholder: pass/fail count + trend + blocker — không chỉ raw number.
- Khi report kết quả flaky/inconclusive, ghi rõ thay vì làm tròn pass.

---

# Performance Optimization

## Measurement Loop

- Trình bày theo vòng: **before → change → after** với cùng workload + same instrument.
- Ghi rõ tradeoff: **latency / throughput / cost / memory / dev complexity** — không chỉ 1 chiều.
- Mỗi metric: name, unit, percentile (nếu latency), sample size, time window, env.

## Profile-First

- Profile trước khi guess: pprof / async-profiler / py-spy / clinic.js — share artifact link.
- Optimize hotspot theo measured contribution và target; micro-optimization chỉ hợp lệ khi evidence cho thấy nó ảnh hưởng SLO/cost/hot path.
- Document hypothesis trước khi đo: "expect 30% giảm CPU on path X vì Y".

## Benchmark Design

- Bench harness reproducible: seed, dataset version, warm-up iterations, statistical method (median + stddev).
- Run nhiều iterations, drop outlier theo Tukey fence; report distribution không chỉ mean.
- Avoid micro-bench artifact: dead-code elimination, JIT warm-up, cache hit ảo.

## Cache Pattern

- Cache key format: `{tenant}:{entity}:{version}:{params_hash}` — version để invalidate bulk.
- TTL/freshness window lấy từ data contract; dùng jitter hoặc refresh coalescing khi synchronized expiry là risk, không hardcode một tỷ lệ chung.
- Negative-cache policy phải phân biệt not-found ổn định với transient/auth failure; recovery window dựa trên upstream semantics.
- Stale-while-revalidate chỉ dùng khi contract cho phép stale data và có upper bound/observability rõ.

## Hot Path Idioms

- Allocate ngoài loop (pre-size collection, reuse buffer); avoid boxing/unboxing.
- Batch I/O — N+1 query là worst offender; SIMD/vectorize khi data-parallel.
- Async/await: tránh `await trong for-loop` khi không có dependency — `Promise.all`/`asyncio.gather`.
- String concat trong loop → builder; map lookup hot → array index nếu key bounded.

## Reporting (perf)

- Format: **Problem → Hypothesis → Measurement → Change → Result → Tradeoff**.
- Result: before/after table với delta + confidence interval; chart nếu time-series.
- Tradeoff section bắt buộc — nêu cost (storage, complexity, ops burden).
- Link tới ticket/incident gốc và follow-up monitoring dashboard.

## Sequencing

- Quick win trước (config tuning, index, query rewrite) → architectural change sau.
- 1 change per measurement window — multi-variable confound impossible to attribute.
- Document order of operations + dependencies in rollout plan.
