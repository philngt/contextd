# Agent Constraints — Engine (Universal)

Hard rules. No exceptions. If a constraint conflicts with a user request, state the conflict explicitly before proceeding.

> Engine constraints in this file are **stack-agnostic** — they apply to every workspace regardless of language, framework, or messaging stack.
>
> Stack-specific rules (Kafka/MQTT, REST, frontend, mobile, AI/agentic, ...) live in **packs** under `packs/{pack-name}/agents/constraints.md` and are loaded only when the workspace opts into them.
>
> **Single source of truth.** This file defines the canonical rule text + stable IDs. Other files (CLAUDE.md, validator-rules.md, packs, workspaces) MUST reference rules by ID (e.g. `engine-no-hardcoded-config`) and MUST NOT restate the rule prose — restating creates drift. To add an engine-baseline rule, edit this file only.

## Resolution Order

```
engine constraints (this file, immutable)
  → pack constraints  (additive, alphabetical, per workspace.md `## Packs`)
    → workspace constraints (additive, `workspaces/{ws}/agents/constraints.md`)
```

All three layers are **additive** — pack/workspace can only THÊM hoặc làm chặt hơn, KHÔNG nới lỏng. Muốn nới lỏng engine constraint → patch engine file qua git, KHÔNG silent override.

Rule ID prefixes:
- `engine-*` — engine baseline (this file).
- `pack-{name}-*` — pack-specific (vd `pack-event-driven-kafka-no-hardcoded-topic`).
- `ws-*` — workspace-specific (`workspaces/{ws}/agents/constraints.md`).

## Engine Rule Catalog

### Architecture

- `engine-no-api-outside-contract` — **Do not create APIs** outside the defined contracts. No new endpoints, schemas, or message formats without a contract update in `{ws}/platform/contracts/`.
- `engine-no-assumed-api-signature` — **Do not assume** API signatures, payload schemas, or formats. Read the contract first.
- `engine-no-duplicate-pattern` — **Do not duplicate** pattern implementations. If a pattern exists in `{ws}/platform/patterns/`, apply it; do not rewrite it.

### Code

- `engine-no-hardcoded-config` — **Do not hardcode** connection strings, region codes, credentials, batch sizes, timeouts, concurrency, retries, or other config values. Read from configuration.
- `engine-stateless-service` — **Do not add state** to service classes. All services remain stateless (request-scoped state in method params or context object).

### Domain

- `engine-no-new-workflow-state` — **Do not add workflow states** beyond what is defined in `{ws}/domains/{domain}/workflow.md`.
- `engine-no-unlisted-transition` — **Do not allow transitions** not listed in the workflow doc.
- `engine-no-auto-approve` — **Do not auto-approve** domain actions that require explicit actor identity.

### Knowledge

- `engine-no-guess-on-gap` — **Do not fill knowledge gaps with guesses**. If information is missing, report it.
- `engine-no-cross-workspace-knowledge` — **Do not borrow knowledge across workspaces**. If a workspace lacks something, write to Knowledge Gaps; do not read from another workspace.
- `engine-no-cross-workspace-evidence` — **Do not apply evidence** from another workspace. `source.yaml#workspace_at_ingest` MUST match the active workspace resolved from the shared config resolver.
- `engine-immutable-raw-evidence` — **Do not modify raw evidence** after ingest. `{ws}/evidence/sources/{id}/raw.*` and `source.yaml` are immutable.

## When a Constraint Cannot Be Met

State the conflict clearly:
```

## Compatibility

During migration, the shared config resolver may accept legacy `.claude/wiki.json` / `.Codex/wiki.json` adapters after canonical `.contextd/config.json` is absent.
CONSTRAINT CONFLICT: {rule-id}
Layer: engine | pack-{name} | ws
Reason: {why it cannot be met in this case}
Options: update the constraint, update the knowledge base, or accept a deviation with explicit documentation
```

## Related

- Pack system overview: [packs/README.md](../packs/README.md)
- Engine coding rules: [coding-rules.md](coding-rules.md)
- Validator rules (mechanical checks + Layer 2 self-check): [pipeline/validator-rules.md](pipeline/validator-rules.md)
