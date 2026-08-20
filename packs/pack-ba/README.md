# pack-ba

Business analysis pack cho người dùng BA: mô hình hóa yêu cầu, acceptance criteria, process mapping, và stakeholder alignment.

## When to enable

Workspace opts in by adding `- pack-ba` under `## Packs` in `workspaces/{ws}/workspace.md`.

Enable when workspace cần:
- Chuẩn hóa chất lượng requirement trước implementation
- Đồng bộ business terms giữa BA, QC, và engineering

## What it adds

- **Constraints** (`pack-ba/agents/constraints.md`) - hard rules cho requirement quality
- **Working rules** (`pack-ba/agents/coding-rules.md`, compatibility filename) - conventions viết tài liệu BA
- **Validator rules** (`pack-ba/agents/pipeline/validator-rules.md` + `scripts/rules.py`) - automated gates
- **Retrieval map** (`pack-ba/agents/pipeline/retrieval-map.md`) - mapping component BA -> knowledge docs
- **Prompt overrides** (`pack-ba/agents/pipeline/prompt-overrides.md`) - self-check bổ sung cho BA tasks

## Components declared

- `requirements-modeling`
- `acceptance-criteria`
- `process-mapping`
- `stakeholder-alignment`

## Conflicts with

(none)

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)

## When not to enable

- Task đã có requirement/acceptance contract rõ và chỉ cần implement code.
- Thiết kế kiến trúc kỹ thuật hoặc test automation; dùng engineering pack hoặc `pack-qc`.

## Retrieval behavior

Mỗi component route tới knowledge BA tương ứng: requirement, acceptance criteria, process map, hoặc stakeholder decision. Nếu workspace thiếu doc được map, runtime phải báo gap thay vì mượn tài liệu từ workspace khác.

## Verification

```bash
contextd pack-validate --pack pack-ba --format text
contextd context "Review acceptance criteria for refund workflow" --preview --format json
python scripts/validate.py --file <requirement-fixture> --workspace <workspace-with-pack>
```
