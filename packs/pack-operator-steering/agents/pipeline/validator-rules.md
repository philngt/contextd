# pack-operator-steering — Validator Rules

Layer 1 (static) validator rules. Implemented in `scripts/rules.py` - this doc is the human-readable catalog.

Rule IDs MUST be prefixed `pack-operator-steering-`.

## Catalog

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-operator-steering-report-missing-evidence` | error | Operator audit/drift/remediation markdown lacks an Evidence/Bằng chứng section. |
| `pack-operator-steering-remediation-missing-verification` | error | Remediation-oriented markdown lacks acceptance criteria or verification method. |
| `pack-operator-steering-decision-missing-ledger-fields` | warn | Decision/ADR markdown lacks status, owner, or revisit trigger. |
| `pack-operator-steering-handoff-missing-next-action` | warn | Handoff/session brief lacks next action or stop condition. |

## Layer-2 self-check

```md
### Operator Steering (pack-operator-steering)
- Findings separate evidence, missing evidence, assumptions, inference, confidence, and judgment.
- Remediation has root cause, owner, acceptance criteria, verification method, residual risk.
- Drift check has mismatch type and continue/stop recommendation.
- Decision note has status, context, decision, consequences, owner, revisit trigger.
- Handoff has current state, proven/unproven items, risks, next action, and stop condition.
- Unknown root cause uses `needs-evidence`; unknown domain/workflow uses `needs-research`.
```

## Related

- Implementation: [`scripts/rules.py`](../../scripts/rules.py)
- Engine validator pipeline: [`agents/pipeline/validator-rules.md`](../../../../agents/pipeline/validator-rules.md)
