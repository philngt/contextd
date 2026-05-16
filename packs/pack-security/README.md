# pack-security

Pack cho security engineering: chuẩn hóa threat modeling, secure design review, vulnerability management, và security controls.

## When to enable

Workspace opts in by adding `- pack-security` under `## Packs` in `workspaces/{ws}/workspace.md`.

Enable when workspace cần:
- Chuẩn hóa yêu cầu security-by-design trước khi triển khai
- Đồng bộ chất lượng tài liệu security review, triage, và control verification

## What it adds

- **Constraints** (`pack-security/agents/constraints.md`) - hard rules cho security workflow
- **Coding rules** (`pack-security/agents/coding-rules.md`) - conventions cho docs/checklists security
- **Validator rules** (`pack-security/agents/pipeline/validator-rules.md` + `scripts/rules.py`) - automated gates
- **Retrieval map** (`pack-security/agents/pipeline/retrieval-map.md`) - mapping component security -> knowledge docs
- **Prompt overrides** (`pack-security/agents/pipeline/prompt-overrides.md`) - self-check bổ sung cho security tasks

## Components declared

- `threat-modeling`
- `secure-design-review`
- `vulnerability-management`
- `security-controls`

## Conflicts with

(none)

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)
