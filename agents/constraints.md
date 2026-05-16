# Agent Constraints — Engine (Universal)

Hard rules. No exceptions. If a constraint conflicts with a user request, state the conflict explicitly before proceeding.

> Engine constraints in this file are **stack-agnostic** — they apply to every workspace regardless of language, framework, or messaging stack.
>
> Stack-specific rules (Kafka/MQTT, REST, frontend, mobile, AI/agentic, ...) live in **packs** under `packs/{pack-name}/agents/constraints.md` and are loaded only when the workspace opts into them.

## Resolution Order

```
engine constraints (this file, immutable)
  → pack constraints  (additive, alphabetical, per workspace.md `## Packs`)
    → workspace constraints (additive, `workspaces/{ws}/agents/constraints.md`)
```

All three layers are **additive** — pack/workspace can only THÊM hoặc làm chặt hơn, KHÔNG nới lỏng. Muốn nới lỏng engine constraint → patch engine file qua git, KHÔNG silent override.

Workspace constraint heading prefix `WS:` để dễ phân biệt khi merge view.
Pack constraint heading prefix theo pack name (vd `pack-event-driven` đã tự gắn trong file).

## Architecture Constraints

- **Do not create APIs** outside the defined contracts — no new endpoints, schemas without a contract update
- **Do not assume** API signatures, payload schemas, or formats — read the contract trong `{ws}/platform/contracts/`
- **Do not duplicate** pattern implementations — if a pattern exists trong `{ws}/platform/patterns/`, apply it; do not rewrite it

## Code Constraints

- **Do not hardcode** connection strings, region codes, credentials, batch sizes, timeouts, concurrency, or other config values — read from configuration
- **Do not add state** to service classes — all services must remain stateless (request-scoped state in method params or context object)

## Domain Constraints

- **Do not add workflow states** beyond what is defined trong `{ws}/domains/{domain}/workflow.md`
- **Do not allow transitions** not listed trong the workflow doc
- **Do not auto-approve** domain actions that require explicit actor identity

## Knowledge Constraints

- **Do not fill knowledge gaps with guesses** — if information is missing, report it
- **Do not borrow knowledge across workspaces** — if a workspace lacks something, ghi vào Knowledge Gaps; KHÔNG đọc từ workspace khác
- **Do not apply evidence** từ workspace khác — `source.yaml#workspace_at_ingest` PHẢI khớp `<cwd>/.claude/wiki.json.workspace`
- **Do not modify raw evidence** sau khi ingest (`{ws}/evidence/sources/{id}/raw.*` và `source.yaml` immutable)

## When a Constraint Cannot Be Met

State the conflict clearly:
```
CONSTRAINT CONFLICT: [constraint name]
Layer: [engine | pack-{name} | workspace]
Reason: [why it cannot be met in this case]
Options: [update the constraint, update the knowledge base, or accept a deviation with explicit documentation]
```

## Related

- Pack system overview: [packs/README.md](../packs/README.md)
- Engine coding rules: [coding-rules.md](coding-rules.md)
- Validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
