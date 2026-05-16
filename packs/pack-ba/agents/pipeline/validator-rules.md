# pack-ba — Validator Rules

Layer-1 rule. Prefix `pack-ba-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-ba-requirement-missing-actor-or-outcome` | error | Requirement thiếu actor hoặc business outcome |
| `pack-ba-acceptance-vague-language` | warn | Acceptance criteria chứa từ mơ hồ (fast/easy/better/user-friendly/...) |
| `pack-ba-process-missing-asis-tobe` | warn | Process mapping thiếu phân tách As-Is/To-Be |
| `pack-ba-stakeholder-missing-owner` | warn | Tài liệu stakeholder/dependency không nêu owner/chịu trách nhiệm |

## Layer-2 self-check

```md
### Business Analysis (pack-ba)
- Requirement có actor + trigger + outcome
- Acceptance criteria measurable/testable
- Process mapping rõ As-Is và To-Be
- Stakeholder/dependency có owner rõ ràng
```

## Related

- Implementation: [`scripts/rules.py`](../../scripts/rules.py)
- Engine validator pipeline: [`agents/pipeline/validator-rules.md`](../../../../agents/pipeline/validator-rules.md)
