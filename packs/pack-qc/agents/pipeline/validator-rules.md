# pack-qc — Validator Rules

Layer-1 rule. Prefix `pack-qc-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-qc-bug-missing-repro` | error | Bug/defect doc thiếu bước tái hiện hoặc expected/actual result |
| `pack-qc-bug-missing-severity-priority` | warn | Bug/defect doc có severity mà thiếu priority (hoặc ngược lại) |
| `pack-qc-release-no-evidence` | error | Release/gate decision không có test evidence (pass/fail/coverage/trend) |
| `pack-qc-regression-vague-scope` | warn | Regression plan dùng mô tả mơ hồ (all as needed/normal regression/...) |

## Layer-2 self-check

```md
### Quality Control (pack-qc)
- Defect có đủ repro + expected/actual
- Severity và priority được ghi tách biệt
- Release decision có evidence kiểm thử
- Regression scope rõ module/flow/level
```

## Related

- Implementation: [`scripts/rules.py`](../../scripts/rules.py)
- Engine validator pipeline: [`agents/pipeline/validator-rules.md`](../../../../agents/pipeline/validator-rules.md)
