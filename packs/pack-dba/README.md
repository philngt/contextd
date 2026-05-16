# pack-dba

Pack cho DBA: giảm lỗi thường gặp khi thay đổi schema, tối ưu query, và vận hành backup/restore.

## When to enable

Workspace opts in by adding `- pack-dba` under `## Packs` in `workspaces/{ws}/workspace.md`.

Enable when workspace cần:
- Chuẩn hóa quy trình schema change/migration an toàn
- Tăng độ sẵn sàng backup/restore và giảm rủi ro vận hành DB

## What it adds

- **Constraints** (`pack-dba/agents/constraints.md`) - hard rules cho DBA workflow
- **Coding rules** (`pack-dba/agents/coding-rules.md`) - conventions cho docs/checklists DBA
- **Validator rules** (`pack-dba/agents/pipeline/validator-rules.md` + `scripts/rules.py`) - automated gates
- **Retrieval map** (`pack-dba/agents/pipeline/retrieval-map.md`) - mapping component DBA -> knowledge docs
- **Prompt overrides** (`pack-dba/agents/pipeline/prompt-overrides.md`) - self-check bổ sung cho DBA tasks

## Components declared

- `schema-change-management`
- `query-performance-hygiene`
- `backup-restore-readiness`
- `db-operational-guardrails`

## Conflicts with

(none)

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)
