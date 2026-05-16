# Task → Docs Map

Single-stop spec cho 2 việc liên quan chặt: (1) parse user task thành **intent JSON**, và (2) map intent → **danh sách file wiki để retrieve**. Trước đây tách 2 file (`intent-parser.md` + `context-retrieval-map.md`) — gộp lại vì luôn đọc cùng nhau.

---

## 1. Intent schema

```json
{
  "workspace": "{name}",
  "type": "implement_feature | fix_bug | design | incident | review",
  "domain": "{domain-folder-name} | null",
  "components": [...],
  "scope": "{project-folder-name} | global | null",
  "packs": [...]
}
```

Schema canonical cho `01-planner.json#intent` cũng nằm trong [`templates/run-trace.schema.json`](../../templates/run-trace.schema.json) (oneOf[0]). 2 nguồn phải đồng bộ.

### Field resolution

**`workspace`**
- Default = `<cwd>/.claude/wiki.json.workspace` (active của codebase).
- Fallback nếu file thiếu: `~/.claude/wiki-global.json.default_workspace`.
- Nếu task chỉ rõ workspace khác (vd "trong workspace company-b, ...") → cảnh báo, gợi ý `/switch-workspace` trước. KHÔNG silently override.
- Cả 2 nguồn thiếu → STOP (xem [workspace-resolution.md](workspace-resolution.md)).

**`domain` & `scope`**
- `domain` ∈ subdirs của `{ws}/domains/`.
- `scope` ∈ subdirs của `{ws}/projects/`.
- Không khớp → `null`, ghi vào Knowledge Gaps trong `current-task.md`.

**`packs`** = list pack active từ `{ws}/workspace.md ## Packs` (verify mỗi pack có `packs/{name}/pack.yaml`).

### Type definitions

| Type | Triggered When | Example Task |
|------|---------------|--------------|
| `implement_feature` | Building new functionality | "Add a price-history endpoint to the catalog API" |
| `fix_bug` | Diagnosing or fixing a failure | "Login redirect breaks on Safari" |
| `design` | Architecture or approach decisions | "How should we structure the offline-sync layer?" |
| `incident` | Live production issue | "Production checkout latency spiking" |
| `review` | Code or doc review | "Review this PR for the auth middleware" |

### Component detection

Components KHÔNG hardcoded trong engine — load từ active packs' `pack.yaml#keywords` mapping `{component: [keyword,...]}`.

Algorithm:
1. Read `{ws}/workspace.md ## Packs` → pack names.
2. For each pack: load `packs/{name}/pack.yaml#keywords`.
3. Merge maps.
4. Lowercase task text, scan keywords (substring or word-boundary).
5. Emit unique component list.

Keyword không thuộc pack active → leave unmapped, ghi vào Knowledge Gaps. KHÔNG đoán.

Example (`pack-event-driven` active):

| Task fragment | Component |
|---------------|-----------|
| `kafka`, `consumer`, `@KafkaListener`, `offset`, `dlq` | `kafka` |
| `mqtt`, `publish`, `subscribe`, `gateway` | `mqtt` |
| `batch`, `chunk`, `max.poll.records` | `batch` |

### Implementation options

- **Rule-based** (default, fast, predictable) — keyword match → schema.
- **LLM-based** (flexible, slower) — feed task + schema, ask model output JSON. Dùng cho task free-form/multi-language.

---

## 2. Retrieval rules — intent → file paths

Mọi path prefix `{ws} = workspaces/{intent.workspace}/`. KHÔNG retrieve ngoài `{ws}/`.

Engine baseline (`agents/constraints.md`, `agents/coding-rules.md`) luôn load cho mọi intent + **out-of-budget** — xem [context-filter.md → Baseline](context-filter.md#baseline-out-of-budget-docs).

### By intent type

| Intent Type | Always Retrieve | Conditionally Retrieve |
|------------|----------------|----------------------|
| `implement_feature` | `{ws}/platform/contracts/`, `{ws}/platform/patterns/`, `{ws}/projects/{scope}/knowledge-map.md` | `{ws}/domains/{domain}/workflow.md` (nếu domain known) |
| `fix_bug` | `{ws}/runbooks/`, `{ws}/projects/{scope}/services/{service}.md` | `{ws}/platform/patterns/` (nếu component known) |
| `design` | `{ws}/platform/architecture/`, `{ws}/decisions/` | `{ws}/platform/patterns/`, `{ws}/domains/{domain}/` |
| `incident` | `{ws}/runbooks/` | `{ws}/projects/{scope}/services/{service}.md` |
| `review` | `agents/constraints.md`*, `agents/coding-rules.md`*, `{ws}/platform/patterns/` (+ `{ws}/agents/constraints.md`* nếu có) | `{ws}/domains/{domain}/workflow.md`, `{ws}/platform/contracts/` |

> *Baseline — tracked nhưng out-of-budget per [context-filter.md](context-filter.md#baseline-out-of-budget-docs).*

### By component (pack-driven)

Engine KHÔNG hardcode `component → file` map. Mỗi pack khai báo trong `packs/{name}/agents/pipeline/retrieval-map.md`. Pipeline merge map của tất cả pack active.

Ví dụ với `pack-event-driven`:

| Component | Docs |
|-----------|------|
| `kafka` | `{ws}/platform/patterns/kafka-event-processing.md` |
| `mqtt` | `{ws}/platform/patterns/mqtt-routing.md`, `{ws}/platform/contracts/mqtt-topic-contract.md` |
| `batch` | `{ws}/platform/patterns/kafka-event-processing.md` (batch section) |

- File không tồn tại trong `{ws}/` → ghi Knowledge Gaps. KHÔNG fallback workspace khác/pack docs.
- Component không thuộc pack active → bỏ qua, ghi Knowledge Gaps gợi ý pack có thể bật.

### By domain & scope

| Field | Docs |
|-------|------|
| `domain = {d}` | `{ws}/domains/{d}/workflow.md` |
| `scope = {p}` | `{ws}/projects/{p}/knowledge-map.md` + relevant `services/*.md` |

---

## 3. Worked example

**Task:** `"Implement Kafka consumer for surgery file processed events and publish result via MQTT"`
**Active workspace** (`.claude/wiki.json.workspace`): `example-surgery`
**Active packs** (`workspace.md ## Packs`): `pack-event-driven`

### Intent (output của Stage 1 — wiki-planner)

```json
{
  "workspace": "example-surgery",
  "type": "implement_feature",
  "domain": "surgery",
  "components": ["kafka", "mqtt", "batch"],
  "scope": "surgery-service",
  "packs": ["pack-event-driven"]
}
```

### Retrieved files (output của Stage 2 — wiki-context-selector)

```
workspaces/example-surgery/platform/contracts/mqtt-topic-contract.md            ← contracts (always first)
workspaces/example-surgery/platform/patterns/kafka-event-processing.md           ← kafka + batch
workspaces/example-surgery/platform/patterns/mqtt-routing.md                     ← mqtt
workspaces/example-surgery/projects/surgery-service/knowledge-map.md             ← scope
workspaces/example-surgery/projects/surgery-service/services/kafka-consumer.md   ← scope
workspaces/example-surgery/domains/surgery/workflow.md                           ← domain
```

Pass danh sách này tới [Context Filter + Rank](context-filter.md) → cuối cùng ghi `current-task.md`.
