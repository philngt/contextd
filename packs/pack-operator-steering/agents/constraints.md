# pack-operator-steering — Constraints

Hard rules cho agent-operator steering. Additive trên engine constraints. Strict-only direction.

## Evidence And Assumptions

- `pack-operator-steering-evidence-before-judgment` — Findings PHẢI tách facts/evidence, missing evidence, assumptions, inferences, and judgment.
- `pack-operator-steering-no-assumption-as-fact` — Assumption PHẢI có label + confidence; KHÔNG được dùng như fact trong decision/remediation.
- `pack-operator-steering-gap-status-required` — Khi thiếu evidence/root cause, output PHẢI dùng status `needs-evidence`, `needs-decision`, hoặc `needs-research`; KHÔNG kết luận chắc.

## Root Cause And Remediation

- `pack-operator-steering-root-cause-before-remediation` — Remediation PHẢI chỉ rõ root cause hoặc nói root cause chưa đủ evidence.
- `pack-operator-steering-acceptance-verification-required` — Remediation PHẢI có owner, acceptance criteria, and verification method.
- `pack-operator-steering-stop-on-deepening-drift` — Nếu tiếp tục sẽ làm sâu thêm conflict với decision/constraint, output PHẢI có stop recommendation.

## Decision And Handoff

- `pack-operator-steering-decision-ledger-required` — Decision durable PHẢI có status, context, decision, consequences, owner, and revisit trigger.
- `pack-operator-steering-handoff-state-required` — Handoff PHẢI nêu current state, what is proven, what is not proven, risks, next action, and stop condition.
- `pack-operator-steering-no-double-source-of-truth` — Không tạo memory store song song ngoài workspace/context artifact; nếu cần persist, ghi vào workspace docs hoặc report path được owner chọn.

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../../agents/cross-cutting-principles.md)

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md).
