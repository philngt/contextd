# pack-operator-steering — Validator Rules

> Manifest-v2 compatibility adapter. `knowledge.md` is the canonical v3 rule
> catalog and must document every ID implemented by `scripts/rules.py`.

Rule IDs MUST be prefixed `pack-operator-steering-`.

## Catalog

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-operator-steering-report-missing-evidence` | error | Operator audit/drift/remediation markdown lacks an Evidence/Bằng chứng section. |
| `pack-operator-steering-remediation-missing-verification` | error | Remediation-oriented markdown lacks acceptance criteria or verification method. |
| `pack-operator-steering-decision-missing-ledger-fields` | warn | Decision/ADR markdown lacks status, owner, or revisit trigger. |
| `pack-operator-steering-handoff-missing-next-action` | warn | Handoff/session brief lacks next action or stop condition. |
| `pack-operator-steering-wayfinding-missing-control-fields` | error | Wayfinding checkpoint lacks orientation, knowledge recovery, decision frontier, recommendation, operator decision, or continue/pause/pivot/stop gate. |

## Layer-2 self-check

```md
### Operator Steering (pack-operator-steering)
- Findings separate evidence, missing evidence, assumptions, inference, confidence, and judgment.
- Remediation has root cause, owner, acceptance criteria, verification method, residual risk.
- Drift check has mismatch type and continue/stop recommendation.
- Decision note has status, context, decision, consequences, owner, revisit trigger.
- Handoff has current state, proven/unproven items, risks, next action, and stop condition.
- Wayfinding checkpoint has current orientation, gap classification, knowledge boundary, decision frontier, AI recommendation, operator decision, and `continue|pause|pivot|stop` gate.
- Unknown root cause uses `needs-evidence`; unknown domain/workflow uses `needs-research`.
```

## Related

- Implementation: [`scripts/rules.py`](../../scripts/rules.py)
- Engine validator pipeline: [`agents/pipeline/validator-rules.md`](../../../../agents/pipeline/validator-rules.md)
