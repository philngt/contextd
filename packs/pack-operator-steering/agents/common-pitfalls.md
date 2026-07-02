# pack-operator-steering — Top 10 Common Pitfalls

Anti-pattern lặp lại với agent-operator steering. Additive trên [constraints.md](constraints.md).
Applies to components: `context-audit`, `drift-check`, `remediation-planning`, `decision-ledger`, `handoff-quality`, `workflow-mental-model`.

## P01 — Judgment without evidence
- **NG**: kết luận "root cause là X" khi chưa nêu evidence inspected.
- **OK**: facts/evidence, missing evidence, inference, confidence tách riêng.
- **Why**: agent sửa symptom, không sửa nguyên nhân.
- **Detect**: Layer-1 `pack-operator-steering-report-missing-evidence`.
- **Severity**: error

## P02 — Assumption leak
- **NG**: viết assumption như fact hoặc accepted decision.
- **OK**: label assumption + confidence + impact if wrong.
- **Why**: operator mất quyền steer khi assumption ẩn.
- **Detect**: Layer-2 self-check.
- **Severity**: error

## P03 — Remediation without verification
- **NG**: "fix/update/improve" nhưng không có acceptance criteria hoặc verification method.
- **OK**: owner + acceptance criteria + verification method + residual risk.
- **Why**: không nghiệm thu được, lỗi quay lại.
- **Detect**: Layer-1 `pack-operator-steering-remediation-missing-verification`.
- **Severity**: error

## P04 — Decision not recorded
- **NG**: đổi hướng trong chat nhưng không có decision note/ADR.
- **OK**: status, context, decision, consequences, owner, revisit trigger.
- **Why**: session sau dễ đảo ngược cam kết.
- **Detect**: Layer-1 `pack-operator-steering-decision-missing-ledger-fields`.
- **Severity**: warn

## P05 — Continue despite drift
- **NG**: plan tiếp tục dù evidence mâu thuẫn decision/constraint.
- **OK**: stop recommendation hoặc needs-decision trước khi làm tiếp.
- **Why**: mỗi bước tiếp theo làm sâu thêm hướng sai.
- **Detect**: Layer-2 self-check.
- **Severity**: error

## P06 — Handoff hides uncertainty
- **NG**: "next agent should continue" nhưng không nói proven/unproven/risk/stop condition.
- **OK**: handoff brief có current state, proven facts, open risks, next action, stop condition.
- **Why**: agent kế tiếp tái đoán từ đầu hoặc tiếp tục sai.
- **Detect**: Layer-1 `pack-operator-steering-handoff-missing-next-action`.
- **Severity**: warn

## P07 — Context overload treated as completeness
- **NG**: dump nhiều docs nhưng không nêu controlling facts.
- **OK**: context map có authority, freshness, relevance, contradictions, affected decisions.
- **Why**: nhiều context có thể che mất contract/decision quan trọng.
- **Detect**: Layer-2 self-check.
- **Severity**: warn

## P08 — Mental model skipped
- **NG**: operator không có stage/quality-gate model nhưng agent vẫn phán chất lượng.
- **OK**: workflow stages, artifacts, gates, failure modes, diagnosis cues.
- **Why**: không biết stage nào hỏng thì remediation sai chỗ.
- **Detect**: Layer-2 self-check.
- **Severity**: warn

## P09 — Skill mismatch invisible
- **NG**: dùng skill/playbook không hợp task nhưng không nêu mismatch.
- **OK**: skill stack map: visible skill, intended job, fit, gap, remediation.
- **Why**: agent output sai do upstream skill, không phải code.
- **Detect**: Layer-2 self-check.
- **Severity**: warn

## P10 — Double source of truth
- **NG**: ghi memory vào store riêng mà workspace/contextd không biết.
- **OK**: persist vào workspace docs/reports hoặc nêu rõ artifact chỉ là local fallback được owner chọn.
- **Why**: drift giữa memory stores là nguyên nhân của steering failure.
- **Detect**: Layer-2 self-check.
- **Severity**: warn

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 evidence | `pack-operator-steering-report-missing-evidence` | ✓ |
| P02 assumption | — | ✓ |
| P03 verification | `pack-operator-steering-remediation-missing-verification` | ✓ |
| P04 decision | `pack-operator-steering-decision-missing-ledger-fields` | ✓ |
| P05 drift | — | ✓ |
| P06 handoff | `pack-operator-steering-handoff-missing-next-action` | ✓ |
| P07 overload | — | ✓ |
| P08 mental model | — | ✓ |
| P09 skill mismatch | — | ✓ |
| P10 double source | — | ✓ |
