# pack-optimize — Validator Rules

Layer-1 rule. Prefix `pack-optimize-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-optimize-no-baseline-metric` | error | Tài liệu optimize thiếu baseline hoặc target metric |
| `pack-optimize-no-measure-loop` | warn | Thiếu đo trước/sau tối ưu |
| `pack-optimize-premature-tuning` | warn | Có tuning đề xuất nhưng thiếu profiling/bottleneck evidence |
| `pack-optimize-no-regression-check` | warn | Thiếu kế hoạch regression check |

## Layer-2 self-check

```md
### Performance Optimization (pack-optimize)
- Có baseline metric và target metric trước khi tối ưu
- Có đo trước/sau cho thay đổi optimize
- Tuning có profiling/bottleneck evidence
- Có regression check hoặc rollback/guardrail plan
```

## Related

- Implementation: [`scripts/rules.py`](../../scripts/rules.py)
- Engine validator pipeline: [`agents/pipeline/validator-rules.md`](../../../../agents/pipeline/validator-rules.md)
