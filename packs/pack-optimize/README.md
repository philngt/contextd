# pack-optimize

Pack cho performance optimization: chống tối ưu cảm tính bằng baseline metric, profiling, và regression guard.

## When to enable

Workspace opts in by adding `- pack-optimize` under `## Packs` in `workspaces/{ws}/workspace.md`.

Enable when workspace cần:
- Chuẩn hóa cách tối ưu hiệu năng dựa trên evidence thay vì cảm tính
- Quản lý regression risk khi rollout optimization

## What it adds

- **Constraints** (`pack-optimize/agents/constraints.md`) - hard rules cho performance optimization workflow
- **Coding rules** (`pack-optimize/agents/coding-rules.md`) - conventions cho docs/checklists optimize
- **Validator rules** (`pack-optimize/agents/pipeline/validator-rules.md` + `scripts/rules.py`) - automated gates
- **Retrieval map** (`pack-optimize/agents/pipeline/retrieval-map.md`) - mapping component optimize -> knowledge docs
- **Prompt overrides** (`pack-optimize/agents/pipeline/prompt-overrides.md`) - self-check bổ sung cho optimize tasks

## Components declared

- `performance-profiling`
- `bottleneck-analysis`
- `optimization-safety`
- `regression-guard`

## Conflicts with

(none)

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)
