# pack-qc — Prompt Overrides

Section bổ sung vào `agents/pipeline/prompt-template.md` self-check khi pack active.
Pack này gộp performance optimization workflow — self-check chia thành Quality Control + Performance blocks.

## System prompt addition

Nếu task thuộc QC, ưu tiên evidence-based reasoning, traceability defect↔test↔requirement, và explicit residual risk khi recommend release. Nếu task thuộc performance, ưu tiên baseline-first measurement, profile-driven decision, regression guarding. Tránh subjective claim không kèm metric.

## Self-Check Constraints (append vào `Constraints to check` của prompt-template)

```
### Quality Gate (pack-qc)
- Release recommendation dựa trên evidence (pass/fail count + defect trend)
- Không gắn `passed` khi defect severity cao chưa có decision
- Gate có entry + exit criteria + signed-off checklist
- Recommendation nêu residual risk + mitigation

### Defect & Test Design (pack-qc)
- Bug report có repro/expected/actual/env tối thiểu
- Severity tách khỏi Priority; matrix per workspace
- Test ID stable (TC-{epic}-{nn}) + link requirement ID
- Test name mô tả intent, không test_1/test_user
- Negative + boundary case bắt buộc; assertion specific

### Regression (pack-qc)
- Scope change → regression scope update
- Test order-independent (--shuffle pass)
- Flaky tracker với owner + quarantine deadline
- Snapshot test có manual review (không auto-update silent)

### Performance Evidence (pack-qc — perf)
- Optimize có baseline metric + target metric (số + percentile)
- Bottleneck claim có data artifact (pprof / flame / APM / slow log)
- Hypothesis stated trước khi đo

### Performance Behavior (pack-qc — perf)
- Optimize có regression check plan (golden scenarios)
- Không thay đổi behavior contract dưới danh nghĩa optimize
- Cache mới có TTL + event invalidation + jitter

### Performance Measurement (pack-qc — perf)
- Track tail latency (p95/p99/p99.9), không chỉ average
- Bench reflect prod workload (size, concurrency, network)
- A/B compare bằng cohort canary, không full rollout
```

## Layer-2 LLM self-check (append vào validator-rules Layer 2)

```md
### Quality Control
- Evidence-based release decision; residual risk nêu rõ
- Test traceability: TC ↔ R{equirement} ↔ Defect
- Negative/edge case coverage; assertion verifies business outcome
- Flaky test tracked với owner; không silent retry
- CI phase tách (unit → integration → e2e); fail fast

### Performance Optimization
- Profile artifact đính kèm cho hotspot claim
- 1 change per measurement window (no confound)
- Top-N hotspot (Pareto), không chase < 5% non-hot
- Threshold/resource limit từ config
- Report format: Problem → Hypothesis → Measurement → Change → Result → Tradeoff
```

## Inclusion logic

Pack loader (`scripts/pack_loader.py`) merge nội dung file này vào prompt context khi build `current-task.md` cho `/use-contextd`.

## Common Pitfalls (Top 10 × 2)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 (QC) hoặc PO01..PO10 (Perf) trong common-pitfalls.md
- Pitfall regex-detectable: confirm Layer-1 validator PASS (pack-qc-* / pack-qc-perf-*)
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
