# Code Analysis Prompts — CORE-CODE variant

Reference cho `/evidence-analyze` khi `source.yaml#source_type == "code"` AND `code_variant ∈ {null, "code"}` (classic runtime codebase).

Sibling files:
- [code-analysis-prompts.md](code-analysis-prompts.md) — orchestrator (variant dispatch, shared conventions).
- [code-analysis-prompts-agentic.md](code-analysis-prompts-agentic.md) — variant cho markdown-heavy engine repo.

> CORE 4 (`04-questions.md`) và CORE 8 (`08-knowledge-gaps.md`) DÙNG CHUNG filename ở mọi variant — chỉ override prompt template theo variant.

---


## Conventions

Mỗi prompt có:
- **Inputs**: file đọc trước khi run (raw.md, source.yaml, wiki context).
- **Output file**: path tương đối `analysis/{evid-id}/`.
- **Output schema**: structure markdown bắt buộc.
- **Cite rule**: mọi claim cite một trong:
  - `(raw.md#section-N)` — về snapshot section
  - `(raw.md#L<start>-L<end>)` — về dòng raw cụ thể
  - `({path}:L..-L..)` — về code thật trong repo (path relative tới repo root)
  - `({ws}/path/to/file.md#section)` — về wiki

### Khi nào dùng `raw.normalized.md`

Nếu raw.md > 50KB và đã có `raw.normalized.md` → input nói `raw.normalized.md (full)` thay vì `raw.md`. Cite format đổi thành `(raw.normalized.md#section-N)`.

Theo Section 7 của [code-snapshot-conventions.md](code-snapshot-conventions.md).



---

## CORE-CODE 1 — Tech Stack Inventory

**Output**: `c01-tech-stack.md`

**Inputs**:
- `sources/{id}/raw.md` Section 1, 2 (project metadata + dependencies)
- `sources/{id}/source.yaml`

**Prompt**:
> Inventory đầy đủ tech stack của codebase. Cấu trúc:
> 1. **Languages & runtimes** với version pin (vd Java 21 LTS, Node 20.x).
> 2. **Frameworks chính** (web, ORM, messaging, test) — kèm version + role.
> 3. **Build & deploy tools** (Maven/Gradle plugins quan trọng, Dockerfile presence, CI hints).
> 4. **Infra dependencies** suy ra từ deps (Postgres? Redis? Kafka? MQTT broker?).
> 5. **Risks**:
>    - Dependency outdated (major version cũ > 2 năm)
>    - 2 framework cùng level conflict (vd Spring + Quarkus)
>    - Deprecated API trong version đang dùng

**Output schema**:
```markdown
# c01 — Tech Stack Inventory

## Languages & runtimes
- {language} {version} — {role} `(raw.md#section-1)`

## Frameworks
| Framework | Version | Role | Citation |
|-----------|---------|------|----------|
| ... | ... | ... | `(raw.md#L..)` |

## Build & deploy
- ...

## Infra dependencies (inferred)
- {infra} — inferred from {dep} `(raw.md#L..)`

## Risks
- [HIGH] {risk} — reason
- [LOW] {risk}
```

---

## CORE-CODE 2 — Service & Module Map

**Output**: `c02-service-map.md`

**Inputs**:
- `sources/{id}/raw.md` Section 4, 5, 6, 7 (endpoints, consumers, services, DB) — hoặc per-repo `[{name}]` sections nếu bundle
- `{ws}/projects/*/services/*.md` (services đã có trong wiki — để mark exist vs new)

**Bundle mode note**: Mỗi service phải khai báo thêm `**repo**` field. Cross-repo upstream/downstream có thể detect trực tiếp (vd `shared-libs/KafkaPublisher` gọi topic mà `sample-project/KafkaConsumer` lắng nghe → upstream/downstream cross-repo rõ ràng hơn single-repo).

**Prompt**:
> Liệt kê mọi **service candidate** suy ra từ snapshot. 1 service = 1 đơn vị có entry-point (REST, message consumer, scheduled job) + business responsibility.
>
> Với mỗi service:
> 1. **name** đề xuất (kebab-case, vd `kafka-surgery-consumer`)
> 2. **type** — http-api | kafka-consumer | mqtt-router | scheduler | batch | composite
> 3. **repo** — tên repo nguồn (bundle mode) hoặc bỏ qua (single-repo)
> 4. **entry-points** — concrete (topic name, URL path, cron expression)
> 5. **downstream** — gọi DB/queue/HTTP gì (kèm repo-prefix nếu bundle)
> 6. **upstream** — ai gọi/publish vào service này (nếu detect được; cross-repo nếu bundle)
> 7. **wiki_status** — `[NEW]` (chưa có service doc) | `[EXISTS:{path}]` (đã có) | `[STALE:{path}]` (có nhưng raw cho thấy thay đổi)

**Output schema**:
```markdown
# c02 — Service & Module Map

## Services (N total)

### S-001 — {name}  [NEW | EXISTS:{path} | STALE:{path}]
- **type**: {type}
- **repo**: {repo-name}  ← bundle mode only; omit if single-repo
- **entry-points**:
  - `{topic|path|cron}` `({repo-name/code-path}:L..)`
- **downstream**:
  - {DB table | Kafka topic | HTTP endpoint} — `({path}:L..)`
- **upstream**:
  - {producer service | client} (if detected; `[CROSS-REPO:{other-repo}]` nếu cross-repo)
- **stereotype classes**:
  - `{FQN}` `(raw.md#section-6)`

### S-002 — ...
```

---

## CORE-CODE 3 — Pattern Extraction Proposals

**Output**: `c03-pattern-proposals.md`

**Inputs**:
- `sources/{id}/raw.md` Section 5, 6 (consumers + services) — hoặc per-repo `[{name}]` sections nếu bundle
- `c01-tech-stack.md`
- `c02-service-map.md`
- `{ws}/patterns-index.md`
- `{ws}/platform/patterns/*.md`

**Bundle mode note**: Pattern lặp ở ≥ 2 repo trong cùng bundle = tín hiệu mạnh nên canonicalize thành platform pattern. Đánh thêm tag `[CROSS-REPO:{repo-a}+{repo-b}]` bên cạnh `[NEW]`/`[EXTENDS]`.

**Prompt**:
> Phát hiện **repeated implementation skeleton** trong codebase (vd Kafka consumer + retry + DLQ lặp ở 3 service, MQTT routing logic giống nhau, retry-policy class share). So sánh với patterns đã có trong `{ws}/platform/patterns/`.
>
> Với mỗi proposal:
> 1. **name** đề xuất (kebab-case)
> 2. **status** — `[NEW]` | `[EXTENDS:{existing-pattern}]` | `[DUPLICATE-OF:{existing-pattern}]`; thêm `[CROSS-REPO:{repo-a}+{repo-b}]` nếu bundle và pattern xuất hiện ở nhiều repo
> 3. **occurrences** — list service:class:method nơi pattern xuất hiện ≥ 2 lần (kèm repo-name nếu bundle)
> 4. **canonical flow** — Mermaid hoặc text 5–7 bước
> 5. **default config** — config keys + values quan sát được
> 6. **failure handling** — retry / DLQ / circuit-breaker đã thấy trong code
> 7. **diff vs existing** (nếu EXTENDS hoặc DUPLICATE-OF) — chỗ khác biệt

**Output schema**:
```markdown
# c03 — Pattern Extraction Proposals

## P-001 — {name}  [NEW | EXTENDS:{x} | DUPLICATE-OF:{x}]  [CROSS-REPO:{a}+{b}]
<!-- [CROSS-REPO] chỉ thêm nếu bundle mode và pattern span nhiều repo -->

### Occurrences
- {service-A} ({repo-name}): `{class.method}` `({repo/path}:L..-L..)`
- {service-B} ({repo-name}): `{class.method}` `({repo/path}:L..-L..)`
- {service-C}: ...

### Canonical flow
1. ...

### Default config (observed)
```yaml
batch_size: 100   # observed in 2/3 services
retry_max: 5     # all 3
```

### Failure handling
| Scenario | Action | Cited |
|----------|--------|-------|
| ... | ... | `({path}:L..)` |

### Diff vs existing (if applicable)
- Existing `{ws}/platform/patterns/{x}.md` says: ...
- This proposal says: ...
- Recommendation: extend | replace | reject as duplicate

## P-002 — ...
```

---

## CORE-CODE 4 — Contract Extraction Proposals

**Output**: `c04-contract-proposals.md`

**Inputs**:
- `sources/{id}/raw.md` Section 4, 5, 7 (endpoints, consumers, schema) — hoặc per-repo `[{name}]` sections nếu bundle
- `c02-service-map.md`
- `{ws}/platform/contracts/*.md`

**Bundle mode note**: Cross-repo inconsistency (vd `core-framework` dùng topic pattern `domain.aggregate.verb` nhưng `sample-project` dùng `domain_aggregate_verb`) = high-value finding. Đánh `[CROSS-REPO-INCONSISTENCY]` với cả hai citation.

**Prompt**:
> Phát hiện **contract candidates** từ code:
> - **Topic naming conventions** — Kafka/MQTT/RabbitMQ. Vd `surgery.command.<verb>` pattern.
> - **API path conventions** — REST endpoint naming/versioning (`/api/v1/...`).
> - **Message schemas** — DTOs / Avro / Protobuf / JSON schema.
> - **Header/metadata conventions** — correlation-id, trace-id, source-id.
>
> Với mỗi proposal:
> 1. **name** (vd `kafka-topic-contract-surgery`)
> 2. **status** — `[NEW]` | `[EXTENDS:{existing-contract}]` | `[CONFLICT:{existing-contract}]`; thêm `[CROSS-REPO-INCONSISTENCY]` nếu bundle và cùng loại contract nhưng khác convention giữa 2 repo
> 3. **rule statement** — tuyên bố rõ ràng (vd "All Kafka topics MUST follow `<domain>.<aggregate>.<event-verb>`")
> 4. **observed evidence** — list cụ thể từ code (kèm repo-name nếu bundle)
> 5. **counter-examples** — case vi phạm rule (nếu có; `[CROSS-REPO-INCONSISTENCY]` nếu vi phạm nằm ở repo khác)
> 6. **diff vs existing** (nếu EXTENDS/CONFLICT)

**Output schema**:
```markdown
# c04 — Contract Extraction Proposals

## C-001 — {name}  [NEW | EXTENDS:{x} | CONFLICT:{x}]

### Rule
{Statement clear, không mơ hồ}

### Observed evidence
- ✅ `surgery.command.start` `({path}:L..)`
- ✅ `surgery.command.cancel` `({path}:L..)`
- ✅ `inventory.command.reserve` `({path}:L..)`

### Counter-examples (rule violated by current code)
- ❌ `legacy_surgery_start` `({path}:L..)` — does not follow

### Confidence
- Coverage: {N}/{total} cases follow → {high | medium | low}

### Diff vs existing
{nếu CONFLICT — describe disagreement, propose resolution}

## C-002 — ...
```

---

## CORE-CODE 8 — Knowledge Gap Map (code variant)

**Output**: `08-knowledge-gaps.md`  ← cùng filename với CORE 8 ở critical-analysis-prompts.md (KHÔNG đổi tên)

**Inputs**:
- All cXX files (c01–c04)
- `{ws}/patterns-index.md`
- `{ws}/projects/*/knowledge-map.md`
- `{ws}/platform/contracts/*.md`

**Prompt**:
> Xác định gap giữa **code thực tế** và **wiki của workspace `{active}`**:
> 1. Service trong c02 chưa có service doc trong `{ws}/projects/*/services/`
> 2. Pattern proposal (c03) chưa có entry trong `{ws}/patterns-index.md` hoặc file trong `{ws}/platform/patterns/`
> 3. Contract proposal (c04) chưa có file trong `{ws}/platform/contracts/`
> 4. Service doc đã có nhưng **stale** (`Config Overrides`, `Failure Handling`, `Flow` không match code)
> 5. Implicit decision (vd "switched from X to Y in Q2") chưa có ADR
>
> Mỗi gap đánh `[BLOCKING]` (block apply, P0/P1) hoặc `[NICE-TO-HAVE]`.
>
> **Authoritative**: file này là single source of truth cho phân loại gap. `qa-batching.md` derive `blocks_apply` và `gap_severity` từ đây.

**Output schema**:
```markdown
# 08 — Knowledge Gaps (vs workspace `{active}`)

## Blocking gaps (must resolve before apply)

### G-001 — {gap title}
- **Type**: missing-service-doc | missing-pattern | missing-contract | stale-doc | missing-adr
- **Affected**: `{ws}/projects/{p}/services/{s}.md` (will be created)
- **Needed info**: {what user needs to confirm}
- **Source in code**: `({path}:L..)`

[BLOCKING] G-002 — ...

## Nice-to-have gaps
- [NICE] G-{N} — ...

## Missing source types (if any)
- ...
```

---

## CORE 4 — Question Generator (shared with text pipeline)

**Output**: `04-questions.md`  ← reuse CORE 4 hiện tại từ critical-analysis-prompts.md.

**Inputs khi source_type=code**:
- `c01-tech-stack.md`, `c02-service-map.md`, `c03-pattern-proposals.md`, `c04-contract-proposals.md`
- `08-knowledge-gaps.md`
- `sources/{id}/raw.md`
- Wiki context (patterns-index, contracts, services của workspace)

**Override prompt khi source_type=code**:
> Generate question pool dựa vào c01–c04 và 08-knowledge-gaps.
> Question types điển hình cho code evidence:
>
> 1. **Pattern confirmation** (P0 — blocks_apply):
>    - "Pattern proposal P-X có nên thêm vào `{ws}/platform/patterns/` không? Tên đề xuất: `{name}`."
>    - "Pattern P-X mark `[EXTENDS:{y}]` — có muốn merge vào `{y}` hay tách file mới?"
>
> 2. **Contract confirmation** (P0):
>    - "Contract C-X (`{rule}`) có chính xác là rule chính thức không? Counter-examples nên ghi là exception hay code cần fix?"
>
> 3. **Service doc** (P1):
>    - "Service S-X (`{name}`) có cần service doc riêng không? Hay merge vào doc khác?"
>    - "S-X có ownership project nào? `{ws}/projects/{?}`"
>
> 4. **ADR** (P1):
>    - "Implicit decision phát hiện trong c06 (vd 'switched lib X→Y') có cần ADR riêng không?"
>
> 5. **Stale doc** (P1):
>    - "Service doc `{path}` mark stale — confirm Config Overrides cần update theo code thực tế?"
>
> 6. **Counter-arguments** (P3):
>    - "Có lý do gì pattern/contract proposal KHÔNG nên đưa vào wiki không?"
>
> Mỗi câu format giống CORE 4 hiện tại (q-XXX, priority, reason, source).

Output schema không đổi — giữ y nguyên format của `04-questions.md` ở `critical-analysis-prompts.md`.

---

## ON-DEMAND C5 — Service Doc Auto-Draft

**Output**: `c05-service-drafts.md`

**Inputs**: `c02-service-map.md`, raw.md, `templates/service.md`.

**Khi nào**: trước khi `/evidence-apply` để có draft sẵn cho từng service `[NEW]`.

**Prompt**:
> Với mỗi service mark `[NEW]` trong c02, sinh draft service doc theo `templates/service.md`:
> - Điền Purpose, Input, Output, Flow (sử dụng pattern từ c03 nếu match), Config từ raw Section 3, Failure Handling từ code thật.
> - Mark field chưa có data là `{TODO: ask expert}` để Q&A loop tạo question.
> - **KHÔNG** invent — chỉ điền những gì raw.md cite được.

**Output**: 1 markdown file chứa N draft, mỗi draft phân cách bằng `---` và header `## S-XXX — {name} (draft)`.

---

## ON-DEMAND C6 — Implicit Decision Detector

**Output**: `c06-decision-drafts.md`

**Inputs**: `sources/{id}/raw.md` Section 9 (git summary), Section 2 (deps), Section 6 (services), commit messages.

**Prompt**:
> Phát hiện **implicit decisions** chưa có ADR:
> 1. **Library substitution** — `pom.xml` history cho thấy switch X→Y (vd Caffeine→Guava cache, log4j→logback)
> 2. **Framework migration** — Section 9 commits có "migrate to", "switch from", "deprecate"
> 3. **Architecture choices** — pattern code phản ánh choice không document (vd "saga vs 2PC")
> 4. **Build/deploy decisions** — Dockerfile multi-stage, CI matrix
>
> Với mỗi decision draft:
> 1. **title** đề xuất (vd "Switch from Caffeine to Guava cache")
> 2. **scope** — workspace-wide | project-local
> 3. **context** — gì trigger decision (commit message, ticket reference nếu có)
> 4. **decision statement** — clear
> 5. **alternatives** — option khác (nếu detect được từ git log "considered X")
> 6. **trade-offs** — observed (vd performance regression test, dependency size)
> 7. **citation** — commit SHA + path

**Output schema**:
```markdown
# c06 — Implicit Decision Drafts

## D-001 — {title}

### Scope
{workspace | project:{name}}

### Context
{trigger — commit, ticket, incident}
- Commit: `{sha7}` "{subject}" `(raw.md#section-9)`

### Decision
{statement}

### Alternatives considered (if detected)
| Option | Source |
|--------|--------|
| ... | ... |

### Trade-offs (observed)
- ...

### Suggested ADR file path
`{ws}/decisions/{NNN}-{slug}.md` or `{ws}/projects/{p}/decisions/{NNN}-{slug}.md`

## D-002 — ...
```

---

## ON-DEMAND C7 — Config Override Map

**Output**: `c07-config-overrides.md`

**Inputs**: `sources/{id}/raw.md` Section 3 (configs), `c03-pattern-proposals.md`, `{ws}/platform/patterns/*.md` Default Config tables.

**Prompt**:
> So sánh **config thực tế** (raw.md Section 3 — `application.yaml`, `application.properties`) với **Default Config** trong `{ws}/platform/patterns/*.md`.
>
> Với mỗi override (config khác default):
> 1. **service** — service name từ c02
> 2. **pattern** — pattern reference
> 3. **key** — config key
> 4. **default** — value trong pattern doc
> 5. **actual** — value trong code
> 6. **inferred reason** — nếu commit history hoặc comment giải thích
>
> Output này feed vào service doc `Config Overrides` table khi apply.

**Output schema**:
```markdown
# c07 — Config Overrides Map

## Service: {service-name}

Pattern ref: `{ws}/platform/patterns/{pattern}.md`

| Key | Default | Actual | Reason | Source |
|-----|---------|--------|--------|--------|
| `batch_size` | 100 | 50 | "high-memory pressure" (comment) | `({path}:L..)` |
| `retry_max` | 5 | 3 | (no reason found) | `({path}:L..)` |

## Service: {next} ...
```

---

## ON-DEMAND C8 — QA Recommender

> **Invoked by**: `/evidence-qa` (tự động khi `source_type=code`), KHÔNG phải `/evidence-analyze`.
> **Khác C5–C7**: C8 phục vụ Q&A loop, không phải analysis pipeline.

**Output**: `qa/{id}/recommendations.md`

**Inputs**:
- `analysis/{id}/04-questions.md` — full question pool với priority
- `analysis/{id}/c01-tech-stack.md`, `c02-service-map.md`, `c03-pattern-proposals.md`, `c04-contract-proposals.md`
- `sources/{id}/raw.md` (hoặc `raw.normalized.md` nếu > 50KB)
- `{ws}/platform/patterns/*.md` — so sánh EXTENDS / DUPLICATE
- `{ws}/platform/contracts/*.md` — so sánh CONFLICT / NEW

**Scope**: **P0 + P1 questions only.** P2/P3 → ghi note `_(P2/P3 — user answers directly)_`, không phân tích.

**Prompt**:
> Đọc toàn bộ P0/P1 questions trong `04-questions.md`. Với **mỗi câu hỏi**:
>
> 1. **Xác định loại câu hỏi**:
>    - Pattern confirmation → đọc c03-pattern-proposals.md entry tương ứng
>    - Contract confirmation → đọc c04-contract-proposals.md + so sánh `{ws}/platform/contracts/`
>    - Service doc → đọc c02-service-map.md entry + so sánh `{ws}/projects/*/services/`
>    - ADR → đọc c06 nếu có; nếu không → infer từ c01-c03 + git summary (raw.md#section-9)
>    - Stale doc → đọc `[STALE:{path}]` flag trong c02 + raw.md section cite bởi question
>
> 2. **Thu thập evidence**: đọc analysis file liên quan + raw.md section được cite trong question. Không grep actual codebase — chỉ dùng snapshot và analysis files.
>
> 3. **Đưa ra kết luận** (1 trong 4):
>    - `NÊN THÊM`: evidence đủ mạnh (≥ 2 occurrences HOẶC ≥ 2 analysis files đồng thuận)
>    - `KHÔNG NÊN THÊM`: DUPLICATE-OF existing artifact hoặc evidence quá yếu (< 2 occurrences, no clear pattern)
>    - `CẦN XEM XÉT THÊM`: có evidence nhưng thiếu 1 thông tin cụ thể user phải xác nhận (nêu rõ)
>    - `CHUYỂN CHUYÊN GIA`: architectural / business decision — code không đủ thông tin
>
> 4. **Độ tin cậy**:
>    - `CAO (●●●)`: ≥ 3 occurrences hoặc evidence trong ≥ 2 analysis files đồng thuận
>    - `VỪA (●●○)`: 2 occurrences hoặc inferred từ context gián tiếp
>    - `THẤP (●○○)`: 1 occurrence hoặc architectural judgment — cần cảnh báo user
>
> 5. **Viết đề xuất câu trả lời hoàn chỉnh** (không phải tóm tắt):
>    - Câu trả lời như thể một kỹ sư đang trả lời: đủ chi tiết để `/evidence-apply` dùng được
>    - Include: tên file wiki sẽ tạo/sửa, config values quan sát được, cross-references
>    - Nếu `CẦN XEM XÉT THÊM`: viết câu trả lời với placeholder rõ ràng `[USER CẦN ĐIỀN: ...]`
>    - Nếu `CHUYỂN CHUYÊN GIA`: viết `_(Không đủ evidence kỹ thuật — nên defer to expert.)_`
>
> 6. **Cite cụ thể** vào analysis file section + raw.md section (không cite vague).

**Output schema**: theo `templates/evidence-qa-recommendations.md`.

**Không được**:
- Invent information không có trong raw.md hoặc analysis files.
- Recommend `NÊN THÊM` cho P0 question khi chỉ có 1 occurrence và không có existing pattern để extends.
- Bỏ qua P0 question vì khó — phải cho `CHUYỂN CHUYÊN GIA` với lý do cụ thể.

---

## Run order

1. `/evidence-analyze --id {id}` (khi source_type=code) → CORE-CODE C1, C2, C3, C4 + CORE 4 (questions) + CORE 8 (gaps) — luôn chạy.
2. `/evidence-qa --id {id}` → tự động invoke **C8 (QA Recommender)** trước batch-1 nếu source_type=code (blocking). User review gợi ý + confirm P0/P1 batches.
3. User trigger ON-DEMAND nếu muốn draft sẵn:
   - `/evidence-analyze --id {id} --prompt c05` → service drafts
   - `/evidence-analyze --id {id} --prompt c06` → ADR drafts
   - `/evidence-analyze --id {id} --prompt c07` → config override map
4. `/evidence-apply --id {id} --mode update` → ghi proposals vào platform/projects/decisions theo router (xem evidence-apply.md Bước 5).

---

## Bundle mode notes (tóm tắt)

Khi `source.yaml#code_repos` non-empty (bundle mode):

| Prompt | Thay đổi |
|--------|---------|
| C1 | Thêm cross-repo version consistency vào Risks (vd framework A dùng Spring Boot 3.2, sample dùng 3.0) |
| C2 | Thêm `repo` field vào mỗi service; upstream/downstream có thể span nhiều repo |
| C3 | Thêm `[CROSS-REPO:{a}+{b}]` tag; occurrences kèm repo-name |
| C4 | Thêm `[CROSS-REPO-INCONSISTENCY]` tag cho convention bất đồng cross-repo |
| C5–C7 | Không đổi schema; draft tham chiếu đúng repo-prefixed citations |
| CORE 4 | Question pool tự thêm câu hỏi về cross-repo findings |
| CORE 8 | Gap về cross-repo inconsistency được phân loại `[BLOCKING]` nếu cùng loại contract |

---

## Cite consistency check

Validator (`validator-rules.md`) sẽ reject nếu:
- File cXX/aXX có claim không kèm citation `(raw.md#...)` hoặc `({path}:L..)`.
- File cXX/aXX cite path ngoài `code_scope` của source.yaml (bundle mode: ngoài tất cả `code_repos[].scope`).
- File cXX/aXX cite `{ws}/...` trỏ về workspace khác workspace_at_ingest.

---
