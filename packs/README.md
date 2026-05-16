# Domain Packs

## Mục đích

Engine core của wiki-template **stack-agnostic** — chỉ giữ workspace isolation, retrieval pipeline, evidence pipeline, và các generic rule (no-hardcoded-config, constructor-injection, domain-no-new-states, ...).

Knowledge đặc thù theo stack (Kafka/MQTT, REST, frontend, mobile, AI/agentic, ...) sống trong **packs** — các bundle có thể bật/tắt per-workspace.

## Cấu trúc một pack

```
packs/{pack-name}/
├── pack.yaml                          # manifest
├── README.md                          # docs
├── agents/
│   ├── constraints.md                 # additive constraints
│   ├── coding-rules.md                # additive coding rules
│   └── pipeline/
│       ├── validator-rules.md         # rule table (prefix pack-{name}-)
│       ├── retrieval-map.md           # component → file map
│       └── prompt-overrides.md        # self-check additions
└── scripts/
    └── rules.py                       # Layer-1 rule fn cho validate.py
```

## Lifecycle

1. **Workspace opt-in**: thêm pack vào section `## Packs` của `workspaces/{ws}/workspace.md`:
   ```md
   ## Packs

   - pack-event-driven
   ```
2. **Pipeline resolution**:
   - Engine constraints/rules **luôn** load trước (immutable).
   - Mỗi pack được load tuần tự (alphabetical) — additive.
   - Workspace-level overrides (`{ws}/agents/...`) load sau cùng — additive.
3. **Validator**: `scripts/validate.py` resolve packs từ workspace, dynamic-import `scripts/rules.py` của mỗi pack, append vào `ALL_RULES`.

## Naming conventions

| Layer | Rule prefix |
|-------|-------------|
| Engine | (none) — vd `no-hardcoded-config` |
| Pack | `pack-{name}-` — vd `pack-event-driven-kafka-no-hardcoded-topic` |
| Workspace | `ws-` — vd `ws-no-mongodb-direct` |

Loader fail-fast nếu trùng tên giữa các layer.

## Conflict & priority

- **Strict-only direction**: pack/workspace chỉ được THÊM hoặc làm chặt. Không nới lỏng engine rule.
- Pack manifest có thể khai báo `conflicts_with: [other-pack]` — loader fail-fast nếu cùng workspace bật cả hai.
- Constraint diễn đạt là additive — mọi rule cùng đúng cùng lúc.

## Tạo pack mới

**Cách nhanh** — dùng scaffold generator:
```bash
python scripts/scaffold-pack.py pack-{your-name}
```
Sinh đủ 8 file (pack.yaml, README, 5 agent docs, scripts/rules.py với `_vio()` helper sẵn). Sau đó chỉ cần customize: pack.yaml components + keywords, constraints.md, và thêm rule functions vào RULES list trong rules.py.

**Cách thủ công** (khi cần kiểm soát chi tiết):

1. Copy `templates/pack.yaml` → `packs/{your-pack}/pack.yaml`.
2. Tạo cấu trúc folder như trên.
3. Viết constraints/rules với prefix `pack-{your-pack}-`.
4. Test bằng `python scripts/validate.py --file <fixture> --workspace <ws-có-pack>`.

## Catalog hiện tại

| Pack | Status | Use cho |
|------|--------|---------|
| [pack-event-driven](pack-event-driven/) | stable (v1.0) | Kafka, MQTT, RabbitMQ, NATS, batch processing |
| [pack-web-api](pack-web-api/) | stable (v1.0) | REST/GraphQL/gRPC API — input validation, error shape, idempotency, no info leak |
| [pack-frontend-react](pack-frontend-react/) | stable (v1.0) | React + Next.js — hooks rules, a11y, effect cleanup, list keys, server/client boundary |
| [pack-ai-app](pack-ai-app/) | stable (v1.0) | LLM apps — prompt caching, structured output, eval harness, no PII leak |
| [pack-agentic](pack-agentic/) | stable (v1.0) | Agent loops, tool use, MCP, multi-agent — bounded steps, idempotent tools, human-in-the-loop |
| [pack-claude-plugin-dev](pack-claude-plugin-dev/) | stable (v1.0) | Build Claude Code plugins — plugin manifest, slash commands, subagents, skills, hooks, MCP servers per Anthropic standard |
| [pack-product](pack-product/) | beta (v0.1) | Product/business knowledge — briefs, OKR, roadmap, personas, journeys, metrics. Cho **non-tech contributors** (PM, business). Pair với `/product-brief`, `/business-view`, `/wiki-explain` |
| [pack-qc](pack-qc/) | beta (v0.1) | Quality control knowledge — test case design, test execution, defect triage, regression & release quality gates. Cho **QC/Tester** users cần evidence-driven quality workflow |
| [pack-ba](pack-ba/) | beta (v0.1) | Business analysis knowledge — requirements modeling, acceptance criteria, process mapping, stakeholder alignment. Cho **BA** users cần requirement clarity/testability |
| [pack-pentest](pack-pentest/) | beta (v0.1) | Authorized pentest knowledge — scope boundary, evidence-based findings, risk rating, remediation reporting. Giảm lỗi false-positive và thiếu bằng chứng |
| [pack-security](pack-security/) | beta (v0.1) | Security engineering knowledge — threat modeling, authz boundary, secret hygiene, logging redaction guidance |
| [pack-optimize](pack-optimize/) | beta (v0.1) | Performance optimization knowledge — baseline/target metrics, bottleneck-first tuning, regression guardrails |
| [pack-dba](pack-dba/) | beta (v0.1) | Database administration knowledge — migration rollback safety, query evidence, backup/restore readiness, DB operational guardrails |
| [pack-solo-builder](pack-solo-builder/) | beta (v0.1) | Cho **non-tech expert** (cơ khí, kế toán, y tế, ...) dùng Claude Code làm "no-code IDE" — tool design coach + tech recipe library cross-platform (Linux native + Windows Docker). Pair với `/tool-design`, `/tool-list`, `/tool-extend` |

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
- pack-agentic       # nếu plugin ship MCP server với tool implementations
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

**Defensive validation flow**:
```md
## Packs

- pack-security
- pack-pentest
```

**Performance hardening flow**:
```md
## Packs

- pack-web-api
- pack-optimize
- pack-security
```
