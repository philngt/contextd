# pack-operator-steering — Constraints

> Manifest-v2 compatibility adapter. Canonical v3 standards live in
> [`../knowledge.md`](../knowledge.md); do not add a weaker or competing rule here.

Hard rules cho agent-operator steering. Additive trên engine constraints. Strict-only direction.

## Evidence And Assumptions (`pack-operator-steering-evidence-assumptions`)

- `pack-operator-steering-evidence-before-judgment` — Findings PHẢI tách facts/evidence, missing evidence, assumptions, inferences, and judgment.
- `pack-operator-steering-no-assumption-as-fact` — Assumption PHẢI có label + confidence; KHÔNG được dùng như fact trong decision/remediation.
- `pack-operator-steering-gap-status-required` — Khi thiếu evidence/root cause, output PHẢI dùng status `needs-evidence`, `needs-decision`, hoặc `needs-research`; KHÔNG kết luận chắc.

## Root Cause And Remediation (`pack-operator-steering-remediation`)

- `pack-operator-steering-root-cause-before-remediation` — Remediation PHẢI chỉ rõ root cause hoặc nói root cause chưa đủ evidence.
- `pack-operator-steering-acceptance-verification-required` — Remediation PHẢI có owner, acceptance criteria, and verification method.
- `pack-operator-steering-stop-on-deepening-drift` — Nếu tiếp tục sẽ làm sâu thêm conflict với decision/constraint, output PHẢI có stop recommendation.

## Decision And Handoff (`pack-operator-steering-decision-handoff`)

- `pack-operator-steering-decision-ledger-required` — Decision durable PHẢI có status, context, decision, consequences, owner, and revisit trigger.
- `pack-operator-steering-handoff-state-required` — Handoff PHẢI nêu current state, what is proven, what is not proven, risks, next action, and stop condition.
- `pack-operator-steering-no-double-source-of-truth` — Không tạo memory store song song ngoài workspace/context artifact; nếu cần persist, ghi vào workspace docs hoặc report path được owner chọn.

## Wayfinding And Human Agency (`pack-operator-steering-wayfinding-agency`)

- `pack-operator-steering-discover-facts-before-asking` — Trong wayfinding, fact có thể kiểm tra từ repo, runtime, context artifact hoặc source hiện có PHẢI được agent tự inspect; chỉ hỏi user về intent, value, risk tolerance hoặc material decision thật sự thuộc owner.
- `pack-operator-steering-decision-frontier-required` — Material decisions PHẢI được dependency-order thành decision frontier; không hỏi hoặc tự chốt decision downstream khi prerequisite còn mở. Thiếu fact/expertise phải route `needs-evidence`/`needs-research`, không giả thành một option.
- `pack-operator-steering-decision-ready-knowledge` — Wayfinding PHẢI tách `must-understand`, `safe-to-delegate`, và `needs-evidence-or-expert` cho current decision. Agent không được che trade-off/risk bằng implementation jargon hoặc dump knowledge không cần cho decision hiện tại.
- `pack-operator-steering-recommendation-preserves-agency` — Mỗi material decision question PHẢI có AI recommendation, rationale, trade-off và impact nếu sai; operator có quyền accept, revise, defer hoặc dừng. Câu “AI tự quyết” không phải blanket approval cho scope/architecture/risk direction.
- `pack-operator-steering-wayfinding-stop-gate` — Wayfinding checkpoint PHẢI kết luận `continue`, `pause`, `pivot`, hoặc `stop` bằng evidence; kèm một bounded next step hoặc revisit trigger. Không default `continue` chỉ vì vẫn còn việc có thể làm.
- `pack-operator-steering-no-material-action-before-alignment` — Trong explicit wayfinding session, KHÔNG implement material path mới trước khi operator xác nhận shared understanding đủ dùng hoặc chủ động kết thúc wayfinding.

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../../agents/cross-cutting-principles.md)

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md).
