# pack-dba — Validator Rules

Layer-1 rule. Prefix `pack-dba-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-dba-migration-no-rollback` | error | Migration/schema change thiếu rollback plan hoặc forward-fix |
| `pack-dba-query-no-evidence` | warn | Query optimization thiếu evidence (plan/metric/slow query data) |
| `pack-dba-backup-no-rpo-rto` | error | Backup/DR doc thiếu RPO hoặc RTO |
| `pack-dba-no-restore-verification` | warn | Backup strategy thiếu restore test/verification cadence |

## Layer-2 self-check

```md
### Database Administration (pack-dba)
- Migration/schema change có rollback hoặc forward-fix strategy
- Query optimization có plan/metric evidence
- Backup/DR doc có đủ RPO và RTO
- Backup strategy có restore verification định kỳ
```

## Related

- Implementation: [`scripts/rules.py`](../../scripts/rules.py)
- Engine validator pipeline: [`agents/pipeline/validator-rules.md`](../../../../agents/pipeline/validator-rules.md)
