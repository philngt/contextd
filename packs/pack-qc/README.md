# pack-qc

Quality control pack cho người dùng QC: thiết kế test, thực thi test, triage defect, và quản trị regression/release gate.

## When to enable

Workspace opts in by adding `- pack-qc` under `## Packs` in `workspaces/{ws}/workspace.md`.

Enable when workspace cần:
- Chuẩn hóa quality gate cho release
- Quản lý defect lifecycle và regression planning có evidence

## What it adds

- **Constraints** (`pack-qc/agents/constraints.md`) - hard rules cho QC workflow
- **Coding rules** (`pack-qc/agents/coding-rules.md`) - conventions cho docs/checklists QC
- **Validator rules** (`pack-qc/agents/pipeline/validator-rules.md` + `scripts/rules.py`) - automated gates
- **Retrieval map** (`pack-qc/agents/pipeline/retrieval-map.md`) - mapping component QC -> knowledge docs
- **Prompt overrides** (`pack-qc/agents/pipeline/prompt-overrides.md`) - self-check bổ sung cho QC tasks

## Components declared

- `test-case-design`
- `test-execution`
- `defect-triage`
- `regression-plan`

## Conflicts with

(none)

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)
