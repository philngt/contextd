# pack-ba — Constraints

Additive constraints cho business analysis workflow.

## Requirement Clarity

- Requirement PHẢI mô tả outcome business, actor, và trigger; không chấp nhận requirement chỉ mô tả solution kỹ thuật.
- Mọi requirement có impact cross-team PHẢI nêu dependency/handoff rõ ràng.

## Acceptance Discipline

- Acceptance criteria PHẢI measurable và testable; tránh từ mơ hồ như "nhanh", "tốt hơn", "thân thiện" khi không có metric.
- Không được trộn assumptions ngầm vào acceptance criteria; assumption phải được ghi rõ và reviewable.

## Terminology Consistency

- Business term chính (entity/process/status) phải nhất quán trong cùng tài liệu; tránh dùng nhiều tên cho cùng một khái niệm.
- Khi thay đổi nghĩa của term đã có, phải nêu migration note cho stakeholder liên quan.

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../../agents/cross-cutting-principles.md)
