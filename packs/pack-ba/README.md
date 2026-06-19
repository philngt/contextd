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
