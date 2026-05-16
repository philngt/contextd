# pack-qc — Constraints

Additive constraints cho quality control workflow.

## Quality Gate Integrity

- Mọi khuyến nghị release PHẢI dựa trên evidence test execution (pass/fail counts hoặc defect trend), không quyết định theo cảm tính.
- Không được gắn trạng thái `passed` khi còn defect severity cao chưa có decision rõ ràng (fix/defer + risk accepted).

## Defect Traceability

- Bug report PHẢI có tối thiểu: steps to reproduce, expected result, actual result.
- Severity và priority phải tách biệt; không dùng thay thế cho nhau.

## Regression Discipline

- Thay đổi scope release PHẢI kéo theo cập nhật regression scope tương ứng.
- Không bỏ regression critical path khi chưa có risk acceptance rõ ràng từ stakeholder chịu trách nhiệm.

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../../agents/cross-cutting-principles.md)
