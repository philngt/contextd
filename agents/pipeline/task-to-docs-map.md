# Task → Docs Map

Single-stop spec cho 2 việc liên quan chặt: (1) parse user task thành **intent JSON**, và (2) map intent → **danh sách file wiki để retrieve**.

---

## 1. Intent schema

**Canonical schema**: [`templates/run-trace.schema.json`](../../templates/run-trace.schema.json) — `oneOf[0]` (stage `01-planner`), under `properties.intent`. To add/remove/rename a field, edit schema.json first; this doc only documents **resolution semantics** for the field set, not the field list itself.

Effective packs are resolved from project config/workspace defaults and surfaced
through the context artifact's static pack guidance and component routes, not as
an inferred field on intent. Manifest-v3 guidance uses `pack-metadata` and
`pack-knowledge`; v2 compatibility content retains its legacy categories.

### Field resolution

**`workspace`**
- Default = `<cwd>/.contextd/config.json.workspace` (active của codebase).
- Fallback nếu file thiếu: `~/.contextd/config.json.default_workspace`.
- Nếu task chỉ rõ workspace khác (vd "trong workspace company-b, ...") → cảnh báo, gợi ý `/switch-workspace` trước. KHÔNG silently override.
- Cả 2 nguồn thiếu → STOP (xem [workspace-resolution.md](workspace-resolution.md)).

### Compatibility

During migration, legacy adapters `<cwd>/.claude/wiki.json.workspace`, `<cwd>/.Codex/wiki.json.workspace`, and legacy globals may be read after canonical config fails.

**`domain` & `scope`**
- `domain` ∈ subdirs của `{ws}/domains/`.
- `scope` ∈ subdirs của `{ws}/projects/`.
- Không khớp → `null`, ghi vào `gaps[]` trong `current-task.json`.

**Active packs** = `.contextd/config.json#packs` when it is an array, otherwise
`{ws}/workspace.md ## Packs` (verify every pack has `packs/{name}/pack.yaml`).
Use the shared resolver; do not implement another pack-selection path.

Optional first-class non-code fields:
- `workstream`: `engineering | product | business_analysis | quality | security | design | ops | domain_research`.
- `audience`: `engineering | product | ba | qc | security | design | ops | domain`.
- `context_goal`: short machine-readable goal such as `shape_product_decision` or `support_quality_decision`.

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

Engine baseline (`agents/constraints.md`, `agents/coding-rules.md`) luôn load cho
mọi intent. Chúng nằm ngoài retrieved-doc slot count nhưng vẫn nằm trong total
token budget — xem [context-filter.md → Baseline](context-filter.md#baseline-static-docs).

### By intent type

| Intent Type | Always Retrieve | Conditionally Retrieve |
|------------|----------------|----------------------|
| `implement_feature` | `{ws}/platform/contracts/`, `{ws}/platform/patterns/`, `{ws}/projects/{scope}/knowledge-map.md` | `{ws}/domains/{domain}/workflow.md` (nếu domain known) |
| `fix_bug` | `{ws}/runbooks/`, `{ws}/projects/{scope}/services/{service}.md` | `{ws}/platform/patterns/` (nếu component known) |
| `design` | `{ws}/platform/architecture/`, `{ws}/decisions/` | `{ws}/platform/patterns/`, `{ws}/domains/{domain}/` |
| `incident` | `{ws}/runbooks/` | `{ws}/projects/{scope}/services/{service}.md` |
| `review` | `agents/constraints.md`*, `agents/coding-rules.md`*, `{ws}/platform/patterns/` (+ `{ws}/agents/constraints.md`* nếu có) | `{ws}/domains/{domain}/workflow.md`, `{ws}/platform/contracts/` |

> *Baseline — outside the retrieved-doc slot count, included in static/total
> token estimates per [context-filter.md](context-filter.md#baseline-static-docs).*

### Pack static guidance (mọi intent)

- Manifest v3: include compact manifest metadata and
  `knowledge.md#Global Principles` for every intent. Append only the
  `## Component: ...` sections matched by the current task.
- Manifest v2: preserve static manifest, constraints, coding rules, and
  common-pitfalls inputs. Retrieval maps route referenced docs; declared
  validator scripts run in the validation layer. Prompt-overrides remain an
  authoring adapter, not a hidden second plane in the canonical artifact.

Both planes are included in the final context budget report. A static file is
not “free” merely because it sits outside `referenced_docs`.

### By component (pack-driven)

Engine KHÔNG hardcode stack-specific `component → file` map. Manifest-v3 packs
declare the canonical map in `pack.yaml#retrieval`; manifest-v2 packs use
`agents/pipeline/retrieval-map.md`. Pipeline merges only effective packs.

Retrieval-map rows may point to workspace docs (`product/`, `requirements/`, `platform/design/`, `quality/`, `runbooks/`, `evidence/`), plus pack/template docs. `{domain}` and `{project}` placeholders expand only when detected; otherwise the artifact emits an explicit non-blocking gap.

Evidence retrieval is summary-only: context artifacts may use `_index.md`, analysis, verified facts, recommendations, pending external notes, or applied summaries, but must not retrieve immutable `evidence/sources/*/raw.*` wholesale.

Ví dụ với `pack-event-driven`:

| Component | Docs |
|-----------|------|
| `kafka` | `{ws}/platform/patterns/kafka-event-processing.md` |
| `mqtt` | `{ws}/platform/patterns/mqtt-routing.md`, `{ws}/platform/contracts/mqtt-topic-contract.md` |
| `batch` | `{ws}/platform/patterns/kafka-event-processing.md` (batch section) |

- Workspace file không tồn tại trong `{ws}/` → ghi Knowledge Gaps. KHÔNG
  fallback workspace khác. A route may intentionally name a file inside its own
  active pack or `templates/`; it may never read another pack.
- Component không thuộc pack active → bỏ qua, ghi Knowledge Gaps gợi ý pack có thể bật.
- Exact files từ matched component route mang explicit route provenance và được
  ưu tiên hơn incidental text overlap; directory expansions chỉ nhận tie-break
  nhỏ. Tất cả vẫn chịu category/max-doc budget. Điều này giữ owner template/map
  ổn định giữa các ngôn ngữ mà không cho một thư mục pack chiếm toàn context.

### By domain & scope

| Field | Docs |
|-------|------|
| `domain = {d}` | `{ws}/domains/{d}/workflow.md` |
| `scope = {p}` | `{ws}/projects/{p}/knowledge-map.md` + relevant `services/*.md` |

---

## 3. Worked example

**Task:** `"Implement Kafka consumer for surgery file processed events and publish result via MQTT"`
**Active workspace** (`.contextd/config.json.workspace`): `example-surgery`
**Active packs** (`workspace.md ## Packs`): `pack-event-driven`

### Intent (output của Stage 1 — contextd-planner)

Full output shape: see [`run-trace.schema.json`](../../templates/run-trace.schema.json) `oneOf[0]`. Key fields populated cho ví dụ này:

| Field | Value |
|-------|-------|
| `intent.workspace` | `example-surgery` |
| `intent.type` | `implement_feature` |
| `intent.domain` | `surgery` |
| `intent.components` | `["kafka", "mqtt", "batch"]` |
| `intent.scope` | `surgery-service` |
| `intent.patterns_needed` | `["kafka-event-processing", "mqtt-routing"]` |
| `intent.contracts_touched` | `["mqtt-topic-contract"]` |

Planner cũng emit `patterns_verified[]` + `contracts_verified[]` + `unverified_count` (xem schema).

### Retrieved files (output của Stage 2 — contextd-context-selector)

```
workspaces/example-surgery/platform/contracts/mqtt-topic-contract.md            ← contracts (always first)
workspaces/example-surgery/platform/patterns/kafka-event-processing.md           ← kafka + batch
workspaces/example-surgery/platform/patterns/mqtt-routing.md                     ← mqtt
workspaces/example-surgery/projects/surgery-service/knowledge-map.md             ← scope
workspaces/example-surgery/projects/surgery-service/services/kafka-consumer.md   ← scope
workspaces/example-surgery/domains/surgery/workflow.md                           ← domain
```

Pass danh sách này tới [Context Filter + Rank](context-filter.md) → cuối cùng ghi `.contextd/context/current-task.json` và render `.contextd/context/current-task.md`.
