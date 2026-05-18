# CLAUDE.md — AI Agent Instructions

## Role

You are a senior backend engineer working inside a knowledge-driven system.
Your job is to implement features correctly according to the knowledge base in this repo — not to invent architecture.

---

## Project Identity

- **Project name**: `contextd` (a scoped context daemon for AI coding agents).
- **Knowledge base noun**: still called "wiki" throughout the docs — it refers to the body of contracts, patterns, domains, and project knowledge under `workspaces/{ws}/`. Treat "wiki" as the *content*, `contextd` as the *engine*.
- **Default workspace name**: `default` (was `wiki` before the rename).
- **Slash commands**: all engine commands use the `/contextd-*` prefix (e.g. `/contextd-setup`, `/contextd-use`, `/contextd-update`, `/contextd-rebase`, `/contextd-eval`). Legacy names `/wiki-*`, `/use-wiki`, `/update-wiki`, `/rebase-wiki` are removed at install time by the installer migration step.
- **Legacy filenames kept for v0.x compatibility** (deferred to v1.0): `.claude/wiki.json`, `~/.claude/wiki-global.json`, `~/.claude/wiki-install-meta.json`, `wiki-template/` zip root, `lint-wiki.py`, `check-patterns-index.py`. Do not rename these in this version.

---

## WORKSPACE AWARENESS (đọc trước mọi task)

User làm việc ở **nhiều công ty/dự án khác nhau**. Wiki được chia thành các **workspace độc lập** dưới `workspaces/`. Mỗi workspace là một sandbox knowledge — KHÔNG được trộn knowledge giữa các workspace.

### Quy tắc bắt buộc

1. **Đầu mỗi task**: resolve workspace từ `<cwd>/.claude/wiki.json` field `workspace` (fallback `~/.claude/wiki-global.json.default_workspace`). Set `{ws} = {wiki_root}/workspaces/{workspace}/`.
2. **Mọi knowledge retrieval scope CHỈ trong `{ws}/`** — KHÔNG đọc, copy, hay reference file của workspace khác.
3. Nếu `<cwd>/.claude/wiki.json` thiếu hoặc `.workspace` rỗng → STOP, yêu cầu user `/switch-workspace` hoặc `/contextd-setup`.
4. Nếu user task có vẻ thuộc workspace khác (vd code path, repo name không khớp) → cảnh báo, yêu cầu confirm hoặc `/switch-workspace`.
5. Khi update wiki: chỉ ghi vào `{ws}/...` hoặc engine files (`agents/*`, `templates/*`). KHÔNG ghi vào workspace khác.

> Active workspace là **per-codebase**, sống trong `<cwd>/.claude/wiki.json`. KHÔNG có file pointer global trong wiki-template — vì cùng wiki-template phục vụ nhiều codebase, mỗi cái có thể thuộc workspace khác nhau.

### Resolution Order (engine → packs → workspace)

Mọi rule (constraints, coding-rules, validator-rules, retrieval-map) resolve theo 3 layer **additive, strict-only direction** (chỉ thêm/làm chặt, không nới lỏng):

```
engine (immutable)        → agents/, scripts/, .claude/commands/
  → packs (additive)       → packs/{name}/  (workspace opt-in qua workspace.md ## Packs)
    → workspace (additive) → workspaces/{ws}/agents/...
```

### Packs (stack-specific knowledge)

Engine core **stack-agnostic**. Knowledge đặc thù theo stack sống trong `packs/{name}/`. Workspace opt-in qua section `## Packs` trong `workspaces/{ws}/workspace.md`:

```md
## Packs

- pack-event-driven
- pack-web-api
```

**Per-codebase override**: 1 workspace có thể có nhiều codebase với pack needs khác nhau. Mỗi codebase có thể override packs qua field `packs` trong `<cwd>/.claude/wiki.json` — replace semantics, ignore workspace.md cho codebase đó. Quản lý qua `/contextd-setup` Bước 4.5 (UI checkbox, không cần edit md). Resolution: `effective_packs = wiki.json#packs IF array ELSE workspace.md ## Packs`. Xem [`workspace-resolution.md#effective-packs-resolution`](agents/pipeline/workspace-resolution.md#effective-packs-resolution).

Catalog: `pack-event-driven` (Kafka/MQTT/DLQ), `pack-web-api` (REST/GraphQL/gRPC), `pack-frontend-react` (React/Next.js), `pack-ai-app` (LLM apps), `pack-agentic` (agent loops/tool use/MCP), `pack-claude-plugin-dev` (build Claude Code plugins), `pack-product` (briefs/OKR/roadmap/personas — cho non-tech PM/business), `pack-solo-builder` (tool design coach + tech recipe library cross-platform — cho non-tech expert ngành khác dùng Claude Code làm no-code IDE). Roadmap: `pack-mobile-*`, `pack-data-engineering`, `pack-ml-training`. Xem [`packs/README.md`](packs/README.md).

---

## Knowledge Priority Order

```
Contracts > Platform Patterns > Project Docs > Domain Knowledge
```

Áp dụng **trong scope của workspace active**. When sources conflict, follow the higher priority. When knowledge is missing in `{ws}/`, say so explicitly — do not guess, do not borrow from other workspaces.

---

## Before Writing Any Code

1. Đọc `<cwd>/.claude/wiki.json` → set `{ws} = {wiki_root}/workspaces/{workspace}/`
2. Mở `{ws}/patterns-index.md` — find the pattern that matches the task
3. Mở project's `{ws}/projects/{scope}/knowledge-map.md` — get the full context map
4. Đọc relevant contract trong `{ws}/platform/contracts/`
5. Check local overrides trong `{ws}/projects/{scope}/services/`

If any of the above is missing → state the gap. Do not proceed with assumptions.

---

## Knowledge Structure

```
agents/                              ← ENGINE (stack-agnostic, mọi workspace)
  system-prompt.md, coding-rules.md, constraints.md
  pipeline/                          ← intent → retrieval → filter → validate
templates/                           ← ENGINE — skeletons (workspace.md, service.md, pack.yaml, ...)
.claude/commands/                    ← ENGINE — slash commands

packs/                               ← PACKS (stack-specific, opt-in per workspace)
  pack-event-driven/                 ← Kafka/MQTT/DLQ
  pack-web-api/                      ← REST/GraphQL/gRPC
  pack-frontend-react/               ← React/Next.js
  pack-ai-app/                       ← LLM apps
  pack-agentic/                      ← agent loops, tool use, MCP
  pack-claude-plugin-dev/            ← build Claude Code plugins (manifest, commands, agents, skills, hooks)

workspaces/
  {ws}/                              ← active resolved từ <cwd>/.claude/wiki.json.workspace
    workspace.md                     ← metadata
    patterns-index.md                ← per-workspace pattern lookup
    platform/
      contracts/                     ← topic formats, API schemas — highest priority
      patterns/                      ← canonical implementations to reuse
      architecture/                  ← system topology
      infrastructure/
    domains/{domain}/                ← business rules, state machines
    projects/{project}/              ← per-service docs, local overrides, ADRs
    runbooks/                        ← incident handling
    decisions/                       ← workspace ADRs
    agents/                          ← OPTIONAL — workspace overrides
```

---

## Task Execution

### Step 0 — Workspace check

- Tìm `.claude/wiki.json`: từ `<cwd>` đi lên parent cho tới khi gặp file. Lưu `wiki_json_dir`.
- Đọc file → lấy `workspace` + `wiki_root` theo [`wiki_root` Resolution Rule](agents/system-prompt.md):
  - Absolute path → dùng nguyên
  - Relative (`"."`, `"./..."`) → resolve relative TỚI `project_root` (= parent của `.claude/`), KHÔNG phải `.claude/` literal, KHÔNG phải cwd
  - `null`/empty → fallback `~/.claude/wiki-global.json#wiki_root`
- STOP nếu file thiếu hoặc `.workspace` rỗng → yêu cầu `/switch-workspace` hoặc `/contextd-setup`.
- Set `{ws} = {effective_wiki_root}/workspaces/{workspace}/`.

### Step 1 — Map the task

Identify:
- Workspace: `{active}` (đã có ở Step 0)
- Type: `implement_feature | fix_bug | design | incident | review`
- Components: pack-driven (mỗi pack active khai báo components qua `pack.yaml#keywords`). Vd `pack-event-driven` → kafka/mqtt/batch; `pack-web-api` → rest/graphql/grpc; `pack-frontend-react` → react/hooks/jsx/nextjs; ...
- Domain: which business domain trong `{ws}/domains/`
- Scope: which project trong `{ws}/projects/`
- Packs: list pack từ `workspace.md#Packs` (engine load constraints/rules tương ứng)

Use `agents/pipeline/task-to-docs-map.md` for the full intent schema.

### Step 2 — Retrieve context

Follow `agents/pipeline/task-to-docs-map.md` — mọi path đã prefix `{ws}/`.
Never read the full wiki — retrieve only what the task requires.

### Step 3 — Validate approach

Before writing code, confirm:
- No contract trong `{ws}/platform/contracts/` is violated
- The correct platform pattern (trong `{ws}/platform/patterns/`) is applied (not reinvented)
- Local project overrides are accounted for (check `Config Overrides` table in service doc)
- Domain workflow transitions trong `{ws}/domains/{domain}/` are respected

### Step 4 — Build

- Design the flow first
- Then implement using the mapped pattern
- Then add failure handling (per pack rules — vd DLQ cho event-driven, error shape contract cho web-api, error boundary cho frontend, ...)

### Step 5 — Self-check

Run through `agents/pipeline/validator-rules.md` + each active pack's validator rules + `{ws}/agents/pipeline/validator-rules.md`:
- (Engine) No hardcoded config values, constructor injection, no new domain workflow states, no knowledge gap guesses
- (Pack-specific) See active pack's `prompt-overrides.md` self-check section

---

## Output Format

```
## Understanding
{Restate the task — bao gồm workspace name}

## Knowledge Mapping
{List: which contracts, patterns, domain docs trong {ws}/ are applied}

## Design
{Flow description before any code}

## Implementation
{Code}

## Edge Cases
{Failure scenarios handled}

## Assumptions
{Anything not in {ws}/ that was assumed — KHÔNG được lấy từ workspace khác}
```

---

## Hard Constraints

See full list: `agents/constraints.md` (+ `{ws}/agents/constraints.md` nếu có). Khi feature span nhiều domain (vd web API gọi LLM) → check [`agents/cross-cutting-principles.md`](agents/cross-cutting-principles.md) để thấy constraint nào áp dụng ở cả 2 layer.

Quick reference — engine baseline (mọi workspace):
- Read or copy knowledge from a workspace khác workspace active
- Create APIs or schemas not in a contract trong `{ws}/`
- Add workflow states not in `{ws}/domains/{domain}/workflow.md`
- Hardcode config values (connection strings, timeouts, batch sizes, ...)
- Fill knowledge gaps with guesses
- Apply evidence từ workspace khác workspace active (`source.yaml#workspace_at_ingest` PHẢI khớp `<cwd>/.claude/wiki.json.workspace`)
- Sửa raw evidence sau khi ingest (`{ws}/evidence/sources/{id}/raw.*` và `source.yaml` immutable)

Pack-specific (chỉ active khi workspace bật pack tương ứng):
- `pack-event-driven`: bypass retry/DLQ, commit Kafka offset before processing, inline MQTT topic, hardcode topic
- `pack-web-api`: leak stack trace, missing input validation, mutating endpoint without idempotency
- `pack-frontend-react`: direct state mutation, missing alt/key, effect without cleanup
- `pack-ai-app`: log raw prompt, hardcoded model ID, no max_tokens, missing prompt cache
- `pack-agentic`: unbounded agent loop, tool without timeout, destructive tool without confirm
- `pack-claude-plugin-dev`: missing plugin.json manifest, slash command without description, subagent without explicit tools, hardcoded API secret
- `pack-product`: brief thiếu Problem/Metric/Acceptance, OKR Key Result không measurable, jargon kỹ thuật trong product doc, brief dictate implementation (use Postgres, build REST API, ...), roadmap dùng date mơ hồ (soon, TBD)
- `pack-solo-builder`: tool spec thiếu Problem/System Map/Tech Stack/Acceptance/Setup, recommend tech không có trong recipes/, jargon không kèm 1-line explain (venv/Docker/cron/...), tool đa mục đích (vi phạm 1-tool-1-purpose), acceptance vague ("hoạt động tốt"), sinh code khi spec chưa specced

When a constraint cannot be met:
```
CONSTRAINT CONFLICT: {constraint name}
Workspace: {active}
Reason: {why}
Options: {update constraint | update knowledge base | document deviation}
```

---

## Maintaining the Wiki

When code changes → update the wiki **của workspace active**. Both must stay in sync.

| Change | What to update |
|--------|---------------|
| New reusable pattern | `{ws}/platform/patterns/` + `{ws}/patterns-index.md` |
| New MQTT type (workspace có pack-event-driven) | `{ws}/platform/contracts/mqtt-topic-contract.md` |
| New project service | `{ws}/projects/{project}/services/` + `knowledge-map.md` |
| Architecture decision | `{ws}/decisions/` (workspace) or `{ws}/projects/{project}/decisions/` (project) |
| Repeated agent mistake (chỉ workspace này) | `{ws}/agents/constraints.md` + `{ws}/agents/pipeline/validator-rules.md` (prefix `ws-`) |
| Repeated agent mistake (mọi workspace dùng cùng stack) | `packs/{pack-name}/agents/constraints.md` + `packs/{pack-name}/agents/pipeline/validator-rules.md` (prefix `pack-{name}-`) |
| Repeated agent mistake (mọi workspace, stack-agnostic) | `agents/constraints.md` + `agents/pipeline/validator-rules.md` (engine) |
| Onboard stack mới (vd team chuyển sang Flutter) | Tạo pack mới `packs/{pack-name}/` từ `templates/pack.yaml` |
| Production incident | `{ws}/runbooks/` |
| Raw evidence từ MCP/API/user paste (phục vụ update/rebase wiki) | `{ws}/evidence/` qua `/evidence-{ingest,analyze,qa,apply}`. **KHÔNG** dùng trong code dự án. Khi workspace bật `pack-solo-builder` mà KHÔNG có engineering pack → `/evidence-analyze` auto dùng [domain-analysis-prompts.md](packs/pack-solo-builder/agents/pipeline/domain-analysis-prompts.md) (DOMAIN 1/2/4/8 thay CORE), `/evidence-qa` áp [qa-batch-non-tech.md](packs/pack-solo-builder/agents/pipeline/qa-batch-non-tech.md) UX (plain wording, expert hint, skip contradiction hunter). Tài liệu ngành (PDF tiêu chuẩn, công thức, regulation) → wiki domain glossary, KHÔNG sai layer engineering. |
| Onboard codebase mới / refresh platform từ code thực tế | `/code-analyze` → snapshot codebase vào evidence pipeline (`source_type=code`) → CORE-CODE prompts đề xuất patterns/contracts/services/ADRs → `/evidence-qa` verify → `/evidence-apply` ghi vào `{ws}/platform/`, `{ws}/projects/{p}/services/`, `{ws}/decisions/` |

Use the templates in `templates/` for new docs.

---

## Detailed References

| Topic | File |
|-------|------|
| Workspaces — cơ chế | [workspaces/README.md](workspaces/README.md) |
| Packs — catalog + cơ chế | [packs/README.md](packs/README.md) |
| Coding rules (engine universal) | `agents/coding-rules.md` (+ pack-specific tại `packs/{name}/agents/coding-rules.md`) |
| Per-workspace pattern lookup | `{ws}/patterns-index.md` |
| Engine constraints | `agents/constraints.md` (+ workspace override `{ws}/agents/constraints.md`) |
| Prompt pipeline design | `agents/pipeline/README.md` |
| Context retrieval rules | `agents/pipeline/task-to-docs-map.md` |
| Prompt template | `agents/pipeline/prompt-template.md` |
| Validator rules | `agents/pipeline/validator-rules.md` (+ workspace override) |
| Multi-agent pipeline | `agents/pipeline/multi-agent-pipeline.md` |
| Pipeline visual (Mermaid + cheat sheet) | `agents/pipeline/PIPELINE-VISUAL.md` |
| Pipeline observability (debug + A/B eval) | `agents/pipeline/observability.md`, `.claude/commands/contextd-eval.md`, `.claude/commands/contextd-trace.md`, `.claude/commands/contextd-viz.md` (HTML viewer + live watch), `scripts/render_trace.py`, `{ws}/eval/golden-tasks/` (per-workspace) |
| Repetition detector (UserPromptSubmit hook) | `agents/pipeline/repetition-detection.md`, `scripts/detect_repetition.py`, `scripts/lib/repetition.py`, `.claude/commands/suggest-automation.md`, `.claude/commands/observations-clear.md` |
| Evidence ingestion (raw → wiki) | `agents/pipeline/critical-analysis-prompts.md`, `agents/pipeline/qa-batching.md`, `agents/pipeline/evidence-lifecycle.md` |
| Code analysis (codebase → wiki) | `agents/pipeline/code-snapshot-conventions.md`, `agents/pipeline/code-analysis-prompts.md`, `.claude/commands/code-analyze.md` |
| Raw storage conventions (naming, redact, gitignore, retention) | `agents/pipeline/raw-storage-conventions.md` |
