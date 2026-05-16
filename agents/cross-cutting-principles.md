# Cross-Cutting Principles

Index của các nguyên tắc xuất hiện ở nhiều pack với cách áp dụng (rule cụ thể) khác nhau theo domain. Doc này KHÔNG thay thế pack constraints — chỉ giúp tra cứu nhanh "nguyên tắc X được pack nào áp dụng cụ thể thế nào".

Mỗi nguyên tắc bên dưới có:
- Tên + 1 dòng giải thích
- Bảng pack-nào-áp-dụng + link tới rule cụ thể trong pack constraints.md

Khi viết feature touching nhiều domain (vd web API gọi LLM agent → cả pack-web-api lẫn pack-ai-app cùng apply) → tra doc này trước để biết constraint nào ở mỗi tầng.

---

## 1. Idempotency

Thao tác có thể retry an toàn — kết quả lần thứ N giống lần 1.

| Pack | Áp dụng cho | Rule cụ thể |
|---|---|---|
| pack-web-api | Mutating endpoint (POST/PUT/PATCH/DELETE) | Idempotency key header + dedup store, hoặc upsert. [constraints.md#Idempotency](../packs/pack-web-api/agents/constraints.md) |
| pack-agentic | Tool calls | Document side-effect tools explicitly; idempotent by default. [constraints.md#Tool Use](../packs/pack-agentic/agents/constraints.md) |
| pack-event-driven | Kafka consumer | Commit offset only AFTER processing (avoid replay duplicate side-effects). [constraints.md#Code](../packs/pack-event-driven/agents/constraints.md) |

---

## 2. Secrets & PII protection

Không log/leak credential, token, PII.

| Pack | Áp dụng cho | Rule cụ thể |
|---|---|---|
| pack-ai-app | Prompt logging | Never `log.info(prompt)`; mask hoặc log metadata only. [constraints.md#Prompt & Context](../packs/pack-ai-app/agents/constraints.md) |
| pack-web-api | Request body logging | Mask field-by-field per data classification. [constraints.md#Information Leak](../packs/pack-web-api/agents/constraints.md) |
| pack-claude-plugin-dev | Plugin code + hooks | Pattern cấm: `sk-...`, `ghp_...`, `AKIA...`, `xoxb-...`, `AIza...`. Hook sanitize input/output trước log. [constraints.md#Security](../packs/pack-claude-plugin-dev/agents/constraints.md) |
| pack-event-driven | Broker config | Không hardcode broker connection strings. [constraints.md#Code](../packs/pack-event-driven/agents/constraints.md) |

---

## 3. Boundary input validation

Validate ở edge (entry point) thay vì kiểm tra rải rác trong business logic.

| Pack | Áp dụng cho | Rule cụ thể |
|---|---|---|
| pack-web-api | API endpoint | `@Valid` / Pydantic / Zod / schema — KHÔNG ad-hoc `if`. [constraints.md#API Boundary](../packs/pack-web-api/agents/constraints.md) |
| pack-agentic | Tool input | `input_schema` explicit, không generate runtime. [constraints.md#Tool Use](../packs/pack-agentic/agents/constraints.md) |
| pack-ai-app | LLM structured output | Schema validation qua tool_choice / response_format / function calling — KHÔNG regex parse. [constraints.md#Structured Output](../packs/pack-ai-app/agents/constraints.md) |

---

## 4. Retry, backoff & circuit breaker

Không tight-loop. Bảo vệ downstream khỏi thundering herd.

| Pack | Áp dụng cho | Rule cụ thể |
|---|---|---|
| pack-ai-app | LLM provider 5xx / rate limit | Exponential backoff + circuit breaker. [constraints.md#Model & Provider](../packs/pack-ai-app/agents/constraints.md) |
| pack-web-api | Heavy endpoint → downstream | Circuit breaker. [constraints.md#Rate Limiting & Abuse](../packs/pack-web-api/agents/constraints.md) |
| pack-event-driven | Failed Kafka message | Retry + DLQ per platform pattern. [constraints.md#Architecture](../packs/pack-event-driven/agents/constraints.md) |
| pack-agentic | Agent loop | Max steps bounded + repeated-state detection. [constraints.md#Agent Loop Safety](../packs/pack-agentic/agents/constraints.md) |

---

## 5. Namespacing & collision avoidance

Identifier prefix để tránh đụng độ khi merge nhiều nguồn.

| Pack | Áp dụng cho | Rule cụ thể |
|---|---|---|
| pack-agentic | MCP tool name | `{server-name}__{tool}` prefix. [constraints.md#MCP Server](../packs/pack-agentic/agents/constraints.md) |
| pack-claude-plugin-dev | MCP tool name + plugin name | Plugin name kebab-case `[a-z0-9][a-z0-9-]*`; MCP tool `{server}__{tool}`. [constraints.md#Plugin Manifest, MCP Servers](../packs/pack-claude-plugin-dev/agents/constraints.md) |

---

## 6. Token / resource budget

Bounded resource consumption — không để unbounded.

| Pack | Áp dụng cho | Rule cụ thể |
|---|---|---|
| pack-ai-app | LLM call | `max_tokens` explicit per call. [constraints.md#Prompt & Context](../packs/pack-ai-app/agents/constraints.md) |
| pack-agentic | Agent loop | `MAX_STEPS` limit + cumulative token tracking + context compaction. [constraints.md#Agent Loop Safety](../packs/pack-agentic/agents/constraints.md) |

---

## How to use

- Khi viết feature → check pack đang active trong workspace (`workspace.md#Packs`) → đọc constraints.md của mỗi pack đó.
- Khi feature span nhiều domain (vd web API gọi LLM) → check doc này để thấy nguyên tắc nào áp dụng ở cả 2 layer.
- Khi propose constraint mới — nếu đã có nguyên tắc tương đương ở doc này → mở rộng bảng thay vì tạo rule độc lập.
