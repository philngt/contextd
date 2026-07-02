# Domain Packs

## Purpose

The wiki-template core engine is **stack-agnostic** — it only keeps workspace isolation, retrieval pipeline, evidence pipeline, and generic rules (no-hardcoded-config, constructor-injection, domain-no-new-states, ...).

Stack-specific knowledge (Kafka/MQTT, REST, frontend, mobile, AI/agentic, ...) lives in **packs** — modular bundles that can be enabled/disabled per workspace.

## Pack structure

```
packs/{pack-name}/
├── pack.yaml                          # manifest
├── README.md                          # docs
├── agents/
│   ├── constraints.md                 # additive constraints (hard rules)
│   ├── coding-rules.md                # additive working rules; filename kept for compatibility
│   ├── common-pitfalls.md             # Top 10 anti-patterns (rule/why/detect/severity)
│   └── pipeline/
│       ├── validator-rules.md         # rule table (prefix pack-{name}-)
│       ├── retrieval-map.md           # component → file map
│       └── prompt-overrides.md        # self-check additions (refs common-pitfalls.md)
└── scripts/
    └── rules.py                       # Layer-1 rule functions for validate.py
```

## Lifecycle

1. **Workspace opt-in**: add the pack to the `## Packs` section in `workspaces/{ws}/workspace.md`:
   ```md
   ## Packs

   - pack-event-driven
   ```
2. **Pipeline resolution**:
   - Engine constraints/rules are **always** loaded first (immutable).
   - Each pack is loaded sequentially (alphabetical) — additive.
   - Workspace-level overrides (`{ws}/agents/...`) are loaded last — additive.
3. **Validator**: `scripts/validate.py` resolves active packs from the workspace, dynamically imports each pack’s `scripts/rules.py`, and appends them to `ALL_RULES`.

## Naming conventions

| Layer | Rule prefix |
|-------|-------------|
| Engine | (none) — e.g. `no-hardcoded-config` |
| Pack | `pack-{name}-` — e.g. `pack-event-driven-kafka-no-hardcoded-topic` |
| Workspace | `ws-` — e.g. `ws-no-mongodb-direct` |

The loader is fail-fast when duplicate rule names are found across layers.

## Conflict & priority

- **Strict-only direction**: pack/workspace can only ADD or tighten rules. They cannot relax engine rules.
- Pack manifests may declare `conflicts_with: [other-pack]` — the loader fails fast if both are enabled in the same workspace.
- Constraints are expressed additively — all active rules must hold at the same time.

## Create a new pack

**Fast path** — use the scaffold generator:
```bash
python scripts/scaffold-pack.py pack-{your-name}
```
This generates all 8 files (pack.yaml, README, 5 agent docs, scripts/rules.py with built-in `_vio()` helper). Then customize: `pack.yaml` components + keywords, `constraints.md`, retrieval map, and add rule functions to the `RULES` list in `rules.py`.

`agents/coding-rules.md` is a compatibility filename. Non-code packs should treat it as **working rules** for product, BA, QC, UX, security, ops, or domain-research writing.

**Manual path** (when you need fine-grained control):

1. Copy `templates/pack.yaml` → `packs/{your-pack}/pack.yaml`.
2. Create the folder structure above.
3. Write constraints/rules with prefix `pack-{your-pack}-`.
4. Test with `python scripts/validate.py --file <fixture> --workspace <ws-with-pack>`.

## Current catalog

| Pack | Status | Best for |
|------|--------|----------|
| [pack-event-driven](pack-event-driven/) | stable (v1.0) | Kafka, MQTT, RabbitMQ, NATS, batch processing |
| [pack-web-api](pack-web-api/) | stable (v1.0) | REST/GraphQL/gRPC APIs — input validation, error shape, idempotency, no info leak |
| [pack-frontend-react](pack-frontend-react/) | stable (v1.0) | React + Next.js — hooks rules, a11y, effect cleanup, list keys, server/client boundary |
| [pack-ai-app](pack-ai-app/) | stable (v1.0) | LLM apps — prompt caching, structured output, eval harness, no PII leak |
| [pack-agentic](pack-agentic/) | stable (v1.0) | Agent loops, tool use, MCP, multi-agent — bounded steps, idempotent tools, human-in-the-loop |
| [pack-claude-plugin-dev](pack-claude-plugin-dev/) | stable (v1.0) | Build Claude Code plugins — plugin manifest, slash commands, subagents, skills, hooks, MCP servers per Anthropic standards |
| [pack-operator-steering](pack-operator-steering/) | beta (v0.1) | Agent-operator steering — context audits, drift checks, remediation plans, decision ledgers, handoff quality, workflow mental models |
| [pack-product](pack-product/) | beta (v0.1) | Product/business knowledge — briefs, OKRs, roadmap, personas, journeys, metrics. For **non-technical contributors** (PM, business). Pairs with `/product-brief`, `/business-view`, `/contextd-explain` |
| [pack-qc](pack-qc/) | beta (v0.2) | Quality control + performance optimization — test design/execution, defect triage, regression & release gates, baseline metrics, bottleneck profiling, safe optimization, regression guards. Absorbs former `pack-optimize` |
| [pack-ba](pack-ba/) | beta (v0.1) | Business analysis knowledge — requirements modeling, acceptance criteria, process mapping, stakeholder alignment. For **BA** users needing requirement clarity/testability |
| [pack-security](pack-security/) | beta (v0.2) | Security engineering + authorized pentest — threat modeling, authz boundaries, secret hygiene, logging redaction, scope discipline, evidence-based findings, risk rating, remediation reporting. Absorbs former `pack-pentest` |
| [pack-dba](pack-dba/) | beta (v0.1) | Database administration knowledge — migration rollback safety, query evidence, backup/restore readiness, DB operational guardrails |
| [pack-solo-builder](pack-solo-builder/) | beta (v0.1) | For **non-technical domain experts** (mechanical, accounting, healthcare, ...) using Claude Code as a "no-code IDE" — tool design coach + cross-platform tech recipe library (Linux native + Windows Docker). Pairs with `/tool-design`, `/tool-list`, `/tool-extend` |
| [pack-ui-ux](pack-ui-ux/) | beta (v0.1) | UI/UX design — design system, design tokens, WCAG 2.1 AA accessibility, user flows, UX writing conventions. Pairs with `pack-frontend-react` (design doc ↔ code impl) |

Roadmap (Phase 3+): `pack-mobile-react-native`, `pack-mobile-flutter`, `pack-mobile-ios-swift`, `pack-mobile-android-kotlin`, `pack-data-engineering`, `pack-ml-training`, `pack-devops-iac`.

## Composition examples

**Solo fullstack dev (webapp + AI feature)**:
```md
## Packs

- pack-web-api
- pack-frontend-react
- pack-ai-app
```

**AI agent product (MCP server + frontend)**:
```md
## Packs

- pack-ai-app
- pack-agentic
- pack-web-api
- pack-frontend-react
```

**Backend microservices (event-driven + REST gateway)**:
```md
## Packs

- pack-event-driven
- pack-web-api
```

**Claude Code plugin developer**:
```md
## Packs

- pack-claude-plugin-dev
- pack-agentic       # if the plugin ships an MCP server with tool implementations
```

**Product team with BA + QC collaboration**:
```md
## Packs

- pack-product
- pack-ba
- pack-qc
```

**Security-heavy backend**:
```md
## Packs

- pack-web-api
- pack-security
```

**Defensive validation flow** (security + pentest now combined):
```md
## Packs

- pack-security
```

**Performance hardening flow** (qc + optimize now combined):
```md
## Packs

- pack-web-api
- pack-qc
- pack-security
```

**Product + design team (BA, UX, frontend)**:
```md
## Packs

- pack-ba
- pack-product
- pack-ui-ux
- pack-frontend-react
```

**Agent operator / long-running AI work**:
```md
## Packs

- pack-operator-steering
- pack-agentic       # if the project builds agent loops/tools
```
