# Evidence Analyze

Chạy critical-analysis prompts trên 1 evidence set. CORE prompts chạy mặc định — đủ để mở Q&A loop. ON-DEMAND prompts chạy qua `--prompt`.

Pipeline branches theo `source.yaml#source_type` (+ `code_variant` khi source_type=code) **và packs active trong workspace**:

| `source_type` (+ variant)                          | Packs active                        | CORE set                            | Reference                                                                          |
|----------------------------------------------------|--------------------------------------|-------------------------------------|------------------------------------------------------------------------------------|
| `paste` / `api` / `mcp`                            | engineering pack(s) (default)       | `[01, 02, 04, 08]`                  | [critical-analysis-prompts.md](../../agents/pipeline/critical-analysis-prompts.md) |
| `paste` / `api` / `mcp`                            | **only `pack-solo-builder`** (no engineering pack) | `[d01, d02, d04, d08]` (DOMAIN) | [pack-solo-builder/agents/pipeline/domain-analysis-prompts.md](../../packs/pack-solo-builder/agents/pipeline/domain-analysis-prompts.md) |
| `code` + `code_variant ∈ {null, "code"}`           | any                                 | `[c01, c02, c03, c04, 04, 08]`      | [code-analysis-prompts.md](../../agents/pipeline/code-analysis-prompts.md) (CORE-CODE) |
| `code` + `code_variant == "agentic-engine"`        | any                                 | `[a01, a02, a03, a04, 04, 08]`      | [code-analysis-prompts.md](../../agents/pipeline/code-analysis-prompts.md) (CORE-AGENTIC) |

**Engineering packs** (trigger default critical-analysis-prompts.md): `pack-event-driven`, `pack-web-api`, `pack-frontend-react`, `pack-ai-app`, `pack-agentic`, `pack-claude-plugin-dev`, `pack-product`.

> Step 2 trong pipeline: ingest → **analyze** → qa → apply.
> Reference: [evidence-lifecycle.md](../../agents/pipeline/evidence-lifecycle.md). CORE 4 (`04-questions.md`) và CORE 8 (`08-knowledge-gaps.md`) DÙNG CHUNG filename + output schema ở cả hai pipeline.

---

## Input

| Arg          | Required | Notes                                                                |
|--------------|----------|----------------------------------------------------------------------|
| `--id`       | optional | Evid-id. Mặc định: latest entry state=`ingested` trong `_index.md`.  |
| `--prompt`   | optional | Chạy thêm ON-DEMAND prompt. Text: `03` \| `05` \| `06` \| `07` \| `09` \| `10`. Code (variant=code): `c05` \| `c06` \| `c07`. Code (variant=agentic-engine): `a05` \| `a06` \| `a07`. Có thể repeat. Cross-variant reject (vd `c05` cho agentic-engine evidence). |
| `--persona`  | optional | Cho prompt 03 (expert briefing). Default: `engineering lead`.        |
| `--tone`     | optional | Cho prompt 10 (final report). `academic|professional|conversational`. Default: professional. |
| `--force-profile` | optional | Override pack-detection profile. `domain` \| `engineering`. Dùng khi mix-content guard fail hoặc muốn override default. |

---

## Bước 0 — Workspace check

Theo [workspace-resolution.md Profile A](../../agents/pipeline/workspace-resolution.md#profile-a--active-workspace-required). Set: `config_dir`, `workspace`, `effective_knowledge_root`, `{ws}`.

## Bước 1 — Resolve evidence

1. Nếu không có `--id`:
   - Đọc `{ws}/evidence/_index.md`, lấy entry mới nhất state=`ingested`.
   - Nếu không có → STOP, hướng dẫn `/evidence-ingest`.
2. Đọc `{ws}/evidence/sources/{evid-id}/source.yaml`.
3. **Workspace lock check (I-2)**: `source.yaml#workspace_at_ingest` PHẢI khớp `{active}`. Nếu không → STOP với error format trong `evidence-lifecycle.md`.
4. State PHẢI ∈ {`ingested`, `analyzed`}. Nếu `analyzed` và không có `--prompt` → in warning "đã analyze rồi, dùng --prompt để rerun ON-DEMAND" → STOP.

## Bước 2 — Decide prompts to run

### Bước 2.0 — Pack detection

Resolve **effective_packs** theo [workspace-resolution.md Effective Packs Resolution](../../agents/pipeline/workspace-resolution.md#effective-packs-resolution):

```
local_packs    = config.json#packs           (per-codebase override)
workspace_packs = workspace.md ## Packs    (workspace-wide default)
effective_packs = local_packs IF isinstance(local_packs, list) ELSE workspace_packs
```

Set:
- `engineering_packs_active = effective_packs ∩ {pack-event-driven, pack-web-api, pack-frontend-react, pack-ai-app, pack-agentic, pack-claude-plugin-dev, pack-product}`
- `solo_builder_active = "pack-solo-builder" in effective_packs`

Decide **prompt profile**:
- `solo_builder_active = true` AND `engineering_packs_active = ∅` → **profile: domain** (non-tech)
- Else → **profile: engineering** (default)

In: `📋 Prompt profile: {domain|engineering}` ở đầu output.

> Mix case (cả pack-solo-builder + engineering pack) → profile=engineering vì có engineer trong workspace, prompts kỹ thuật vẫn relevant. UX adjustments cho non-tech vẫn áp ở `/evidence-qa` (xem `qa-batch-non-tech.md`).

Branch theo `source.yaml#source_type`:

### Khi `source_type ∈ {paste, api, mcp}` (text pipeline)

**Profile = engineering** (default):
- Nếu state = `ingested` → CORE set: `[01, 02, 04, 08]` từ [critical-analysis-prompts.md](../../agents/pipeline/critical-analysis-prompts.md). Plus `--prompt` flags.
- Nếu state = `analyzed` (rerun) → chỉ ON-DEMAND `--prompt` flags.
- Validate `--prompt` values ∈ {03, 05, 06, 07, 09, 10}. Reject unknown.

**Profile = domain** (pack-solo-builder only):
- Nếu state = `ingested` → CORE set: `[d01, d02, d04, d08]` từ [domain-analysis-prompts.md](../../packs/pack-solo-builder/agents/pipeline/domain-analysis-prompts.md). Output filenames vẫn là `01-resource-upload.md`, `02-contradiction.md`, `04-questions.md`, `08-knowledge-gaps.md` (cùng schema, body khác).
- Nếu state = `analyzed` (rerun) → ON-DEMAND `--prompt` flags từ critical-analysis-prompts.md (3, 5, 6, 7, 9, 10) vẫn dùng được — domain pipeline chỉ override CORE 1/2/4/8.
- Mix-content guard: nếu raw chứa cả domain content (term, formula) VÀ engineering content (API, schema) → STOP với warning:
  ```
  ⚠ Evidence chứa mix domain + engineering content. Recommend tách:
    1. Cancel → tách raw thành 2 file, ingest 2 evidence riêng.
    2. Force domain profile (ignore engineering parts) — `--force-profile domain`
    3. Force engineering profile — `--force-profile engineering`
  ```

### Khi `source_type = code` (code pipeline)

Sub-branch theo `source.yaml#code_variant`:

#### `code_variant ∈ {null, "code"}` (classic runtime codebase)
- Nếu state = `ingested` → CORE set: `[c01, c02, c03, c04, 04, 08]` từ [code-analysis-prompts.md](../../agents/pipeline/code-analysis-prompts.md) (CORE-CODE).
  - `c01`–`c04` là code-specific (tech stack, service map, pattern proposals, contract proposals).
  - `04` (questions) và `08` (gaps) DÙNG CHUNG filename với text pipeline; nội dung khác (xem code-analysis-prompts.md "CORE 4 — Question Generator" và "CORE-CODE 8").
- Nếu state = `analyzed` (rerun) → chỉ ON-DEMAND `--prompt` flags.
- Validate `--prompt` values ∈ {c05, c06, c07}. Reject unknown (text-pipeline prompts như `03` hoặc agentic-engine prompts như `a05` KHÔNG hợp lệ cho code variant).

#### `code_variant == "agentic-engine"` (markdown-heavy engine: slash commands, sub-agents, prompt templates)
- Nếu state = `ingested` → CORE set: `[a01, a02, a03, a04, 04, 08]` từ [code-analysis-prompts.md](../../agents/pipeline/code-analysis-prompts.md) (CORE-AGENTIC).
  - `a01` Engine Stack Inventory, `a02` Command & Agent Map, `a03` Pattern Proposals, `a04` Contract Proposals.
  - `04` và `08` DÙNG CHUNG filename; CORE 4 dùng "agentic-engine override" prompt; CORE 8 dùng agentic-engine variant.
- Nếu state = `analyzed` (rerun) → chỉ ON-DEMAND `--prompt` flags.
- Validate `--prompt` values ∈ {a05, a06, a07}. Reject cross-variant (`c05`/`c06`/`c07` KHÔNG hợp lệ cho agentic-engine).

## Bước 3 — Load contexts

Đọc song song để feed các prompt:

**Always**:
- `sources/{id}/raw.normalized.md` (nếu có) HOẶC `raw.{ext}` (nếu là markdown/text)
- `sources/{id}/source.yaml`

**For prompts 02, 08** (so sánh với wiki):
- `{ws}/patterns-index.md`
- `{ws}/platform/contracts/*.md` (tất cả file)
- `{ws}/platform/patterns/*.md` (tất cả file)
- `{ws}/projects/*/services/*.md` lọc theo `source.yaml#related_projects`/`related_files` (nếu rỗng → load top-3 service docs khớp keyword trong raw)
- `{ws}/domains/*/workflow.md` nếu `source.yaml#related_domains` non-empty

**For prompt 04**: cộng thêm `01-resource-upload.md` + `02-contradiction.md` + `08-knowledge-gaps.md` (nếu đã sinh ở step 4 dưới).

**For prompt 10**: cộng thêm `qa/{id}/verified-facts.md` (nếu đã có).

## Bước 4 — Run prompts (sequential, có dependency)

Tạo folder `{ws}/evidence/analysis/{evid-id}/` nếu chưa có.

### Text pipeline (`source_type ∈ {paste, api, mcp}`) — Run order
1. **01-resource-upload.md** — chạy đầu tiên, không depend gì.
2. **02-contradiction.md** — depend on 01 + wiki context.
3. **08-knowledge-gaps.md** — depend on 01 + 02 + wiki.
4. **04-questions.md** — depend on 01 + 02 + 08.
5. **ON-DEMAND** (theo thứ tự `--prompt` flags):
   - 03 → depend on 01, 02, raw
   - 05 → depend on 01, raw
   - 06 → depend on 01, raw
   - 07 → depend on 01, 02, 09 (nếu có)
   - 09 → depend on 01, 02, 04
   - 10 → depend on **all** files có trong `analysis/{id}/` + `verified-facts.md` (nếu có)

### Code pipeline (`source_type = code`, `code_variant ∈ {null, "code"}`) — Run order
1. **c01-tech-stack.md** — depend on raw.md Section 1, 2.
2. **c02-service-map.md** — depend on raw.md Section 4, 5, 6, 7 + wiki services context.
3. **c03-pattern-proposals.md** — depend on c01, c02, wiki patterns context.
4. **c04-contract-proposals.md** — depend on c02, raw.md Section 4/5/7, wiki contracts context.
5. **08-knowledge-gaps.md** (code variant) — depend on c01–c04 + wiki context.
6. **04-questions.md** (shared, code-mode prompt) — depend on c01–c04 + 08.
7. **ON-DEMAND** (theo thứ tự `--prompt` flags):
   - c05 (service drafts) → depend on c02 + raw, dùng `templates/service.md`
   - c06 (decision drafts) → depend on raw Section 9 + Section 2/6, dùng `templates/adr.md`
   - c07 (config overrides) → depend on raw Section 3 + c03 + wiki patterns Default Config tables

### Agentic-engine pipeline (`source_type = code`, `code_variant = "agentic-engine"`) — Run order
1. **a01-engine-stack.md** — depend on raw.md Section 1, 2 (engine metadata + MCP/integration deps).
2. **a02-command-map.md** — depend on raw.md Section 4, 5, 6, 7 (commands, agents, pipeline, templates) + wiki services/agent docs nếu có.
3. **a03-pattern-proposals.md** — depend on a01, a02 + raw.md Section 4–6 + wiki patterns context.
4. **a04-contract-proposals.md** — depend on a02 + raw.md Section 4/5/7 + wiki contracts context.
5. **08-knowledge-gaps.md** (agentic-engine variant) — depend on a01–a04 + wiki context.
6. **04-questions.md** (shared, agentic-engine override prompt) — depend on a01–a04 + 08.
7. **ON-DEMAND** (theo thứ tự `--prompt` flags):
   - a05 (command/agent doc drafts) → depend on a02 + raw, dùng `templates/service.md` adapted
   - a06 (decision drafts) → depend on raw Section 9 + Section 4–7 + git log, dùng `templates/adr.md`
   - a07 (settings/hook overrides) → depend on raw Section 8 + a03 + wiki patterns

Với mỗi prompt:
- Build prompt theo template trong [critical-analysis-prompts.md](../../agents/pipeline/critical-analysis-prompts.md).
- Output PHẢI tuân schema markdown nêu trong reference.
- Mọi claim phải có citation (`raw.normalized.md#section-N` hoặc `{ws}/path`).
- Nếu output thiếu citation → re-prompt 1 lần với reminder "missing citations". Sau đó vẫn thiếu → ghi với marker `[NO-CITE]` và warn user.

## Bước 5 — Validate (V-04)

Check mỗi file CORE vừa ghi:
- Non-empty
- Có ít nhất 1 entry với citation
- Schema match (heading hierarchy đúng)

Nếu fail → STOP, không transition state. Báo file nào fail.

## Bước 6 — Update state

Transition `ingested → analyzed` chỉ khi **đủ CORE set** cho `source_type` (+ variant nếu code):
- Text pipeline: 4 files (`01`, `02`, `04`, `08`).
- Code pipeline (variant=code): 6 files (`c01`, `c02`, `c03`, `c04`, `04`, `08`).
- Code pipeline (variant=agentic-engine): 6 files (`a01`, `a02`, `a03`, `a04`, `04`, `08`).

Nếu pass → Update `{ws}/evidence/_index.md` row tương ứng: state → `analyzed`, last_updated = today.

Nếu state đang `analyzed` và chỉ rerun ON-DEMAND: KHÔNG đổi state, chỉ update `last_updated`.

## Bước 7 — Confirm

In:
```
✅ Analysis complete — {evid-id}
   Workspace : {active}
   CORE      : 01-resource-upload, 02-contradiction, 04-questions, 08-knowledge-gaps
   On-demand : {list nếu có}
   State     : analyzed

Highlights:
  - {N} contradictions found ({M} vs wiki, {K} internal)
  - {N} questions generated (P0={x}, P1={y}, P2={z}, P3={w})
  - {N} blocking gaps identified

Next:
  /evidence-qa --id {evid-id}    → start Q&A loop with user
```

---

## Khi nào on-demand

| Prompt | Khi nào dùng                                                              |
|--------|---------------------------------------------------------------------------|
| 03     | Cần brief cho stakeholder/lead về evidence này                            |
| 05     | Có nhiều claim mạnh, cần grade trước khi hỏi user                         |
| 06     | Domain có yếu tố lịch sử (incident, evolution)                            |
| 07     | Trước khi present kết quả ra ngoài, muốn anticipate phản biện             |
| 09     | Sau khi qa_done, muốn extract insight không hiển nhiên                    |
| 10     | Sinh báo cáo cuối cho stakeholder hoặc PR description                     |

---

## Common errors

| Error                          | Fix                                                                  |
|--------------------------------|----------------------------------------------------------------------|
| State ≠ ingested/analyzed      | Check `_index.md`; rerun previous step                               |
| Workspace lock fail (I-2)      | `/switch-workspace {workspace_at_ingest}`                            |
| Output missing citations       | Manual edit, add citation, then `/evidence-qa` continues             |
| Wiki context too large         | `source.yaml#related_files` quá rộng — narrow lại và rerun           |
