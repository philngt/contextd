# Workspace — default

> Seed workspace ship kèm `contextd`. Mục đích: cung cấp một library generic platform patterns + contracts (citation, evidence-state-machine, secrets-blocklist, askuser-confirm, slash-command-naming, sub-agent-frontmatter-schema, ...) để workspace mới có thể tham khảo hoặc copy.
> KHÔNG dùng workspace này để document engine internals — engine spec sống tại `agents/`, `.claude/agents/`, `.claude/commands/`, `scripts/`. Mỗi codebase nên tạo workspace riêng qua `/contextd-setup` hoặc `/new-workspace`.

## Identity

- Company: (seed — không thuộc company nào)
- Role: library workspace
- Period: 2026-05 → present
- Repo(s): contextd engine repo

## Packs

(none — bật pack tương ứng khi xác định stack, vd `pack-event-driven` nếu có Kafka/MQTT)

## Entry Points

Đọc theo thứ tự khi bắt đầu task trong workspace này:

- Contracts: [platform/contracts/](platform/contracts/)
- Patterns Index: [patterns-index.md](patterns-index.md)
- Active Projects: [projects/](projects/)
- Domains: [domains/](domains/)
- Demo Product Brief: [product/briefs/agent-context-build.md](product/briefs/agent-context-build.md)
- Demo Requirement: [requirements/agent-context-build.md](requirements/agent-context-build.md)
- Demo Design Flow: [platform/design/design-system.md](platform/design/design-system.md)
- Demo Project Map: [projects/agent-context-demo/knowledge-map.md](projects/agent-context-demo/knowledge-map.md)
- Runbooks (incident): [runbooks/](runbooks/)
- Workspace ADRs: [decisions/](decisions/)

## Override Notes

Liệt kê file override engine defaults nếu có:

- `agents/constraints.md` — không có
- `agents/pipeline/validator-rules.md` — không có

## Glossary (optional)

| Term | Meaning |
|------|---------|
| TBD | TBD |
