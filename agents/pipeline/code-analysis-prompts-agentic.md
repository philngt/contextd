# Code Analysis Prompts — CORE-AGENTIC variant

Reference cho `/evidence-analyze` khi `source.yaml#source_type == "code"` AND `code_variant == "agentic-engine"` (markdown-heavy agentic-coding engine: slash commands, sub-agents, prompt templates).

Sibling files:
- [code-analysis-prompts.md](code-analysis-prompts.md) — orchestrator (variant dispatch, shared conventions).
- [code-analysis-prompts-code.md](code-analysis-prompts-code.md) — variant cho classic runtime codebase.

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

# CORE-AGENTIC prompts (when `code_variant: agentic-engine`)

Áp dụng khi codebase target là agentic-coding engine repo (markdown-heavy: slash commands, sub-agents, prompt templates). raw.md theo schema Section 12 của [code-snapshot-conventions.md](code-snapshot-conventions.md):

- Section 1: Engine metadata
- Section 2: Dependencies (MCP servers, Claude Code version target, script-tool deps)
- Section 3: Configs (settings.json, wiki.json schemas)
- Section 4: Slash commands
- Section 5: Sub-agents & system prompts
- Section 6: Pipeline stages / Modules
- Section 7: Templates
- Section 8: Hooks & settings
- Section 9: Git summary
- Section 10: Notes

CORE-AGENTIC dispatch tới wiki target giống CORE-CODE (`{ws}/platform/patterns/`, `{ws}/platform/contracts/`, `{ws}/projects/{p}/services/`, `{ws}/decisions/`) — chỉ semantic khác:
- "service" → "agent" hoặc "command"
- "platform pattern" → "agent prompt pattern"
- "contract" → "prompt/file format contract" (vd Section structure invariant, evid-id format, citation rule)

---

## CORE-AGENTIC A1 — Engine Stack Inventory

**Output**: `a01-engine-stack.md`

**Inputs**:
- `sources/{id}/raw.md` Section 1, 2 (engine metadata + deps)
- `sources/{id}/source.yaml`

**Prompt**:
> Inventory engine runtime + integration surface. Cấu trúc:
> 1. **Host runtime**: Claude Code version target (nếu README/CLAUDE.md có ghi); fallback `_(not stated)_`.
> 2. **MCP servers required**: từ `mcp.json` Section 2. Mỗi server: name, role, transport (stdio/http), command-or-url.
> 3. **External integrations** (suy ra từ commands/agents): Obsidian, Confluence, Linear, Slack, GitHub, web fetch, etc.
> 4. **Script-tool deps**: nếu Section 2 có package.json/pyproject — list runtime deps + role.
> 5. **Configurable surface**: env vars, hooks, permissions từ Section 3 + Section 8.
> 6. **Risks**:
>    - Command tham chiếu MCP server không khai báo
>    - Agent tools list mâu thuẫn với permissions trong settings.json
>    - Claude Code version target unspecified (engine có thể vỡ trên version khác)

**Output schema**:
```markdown
# a01 — Engine Stack Inventory

## Host runtime
- Claude Code version: {target | "not stated"} `(README.md:L..)`

## MCP servers required
| Name | Transport | Command/URL | Role | Citation |
|------|-----------|-------------|------|----------|
| ... | ... | ... | ... | `(mcp.json:L..)` |

## External integrations (inferred)
- {integration} — used by `{command-or-agent-file}` `({path}:L..)`

## Script-tool deps
| Source | Name | Version | Role | Citation |

## Configurable surface
- Env vars: ... `(settings.json:L..)`
- Hooks: ... `(settings.json:L..)`
- Permissions: ... `(settings.json:L..)`

## Risks
- [HIGH] {risk} — reason
- [LOW] {risk}
```

---

## CORE-AGENTIC A2 — Command & Agent Map

**Output**: `a02-command-map.md`

**Inputs**:
- `sources/{id}/raw.md` Section 4, 5, 6, 7 (commands, agents, pipeline, templates)
- `{ws}/projects/*/services/*.md` (existing agent/command docs nếu có)

**Prompt**:
> Vẽ bản đồ entry-points + control flow của engine. Mỗi entry-point = 1 slash command HOẶC 1 sub-agent có thể được invoke trực tiếp.
>
> Với mỗi entry-point:
> 1. **name** — `/command-name` hoặc `agent-name`
> 2. **type** — slash-command | subagent | system-prompt-doc
> 3. **purpose** — 1 line
> 4. **inputs** — args, expected user state (workspace, files)
> 5. **outputs** — file changes, state transitions, downstream commands triggered
> 6. **calls** — list agents/templates/pipeline-stages mà entry-point này tham chiếu (cite citation)
> 7. **called_by** — agents/commands khác trigger entry-point này (nếu detect được)
> 8. **wiki_status** — `[NEW]` | `[EXISTS:{path}]` | `[STALE:{path}]`

**Output schema**:
```markdown
# a02 — Command & Agent Map

## Entry-points (N total)

### E-001 — /wiki-setup  [NEW | EXISTS:{path}]
- **type**: slash-command
- **purpose**: ...
- **inputs**: ...
- **outputs**:
  - creates `.claude/wiki.json` `(.claude/commands/wiki-setup.md:L..)`
  - creates `workspaces/{ws}/workspace.md`
- **calls**:
  - template `templates/workspace.md` `(.claude/commands/wiki-setup.md:L..)`
  - agent `agents/system-prompt.md` (referenced) `(...)`
- **called_by**:
  - (none — top-level user entry)

### E-002 — /code-analyze  [...]
...

## Sub-agents (N total)

### A-001 — wiki-curator  [NEW | EXISTS:{path}]
- **type**: subagent
- **role**: ...
- **tools**: ...
- **invoked_by**: ...
```

---

## CORE-AGENTIC A3 — Agent Prompt Pattern Proposals

**Output**: `a03-pattern-proposals.md`  ← **alias** của `c03-pattern-proposals.md` cho agentic-engine. `/evidence-apply` router dùng cùng logic.

**Inputs**:
- `sources/{id}/raw.md` Section 4, 5, 6 (commands + agents + pipeline)
- `a01-engine-stack.md`
- `a02-command-map.md`
- `{ws}/patterns-index.md`
- `{ws}/platform/patterns/*.md`

**Prompt**:
> Phát hiện **repeated prompt structure** lặp lại trong commands/agents — đây là agent prompt patterns nên canonicalize.
>
> Patterns điển hình cần check:
> - **Workspace check (Step 0)**: pattern resolve `.claude/wiki.json` → `{ws}` lặp ở đầu mỗi command
> - **AskUserQuestion confirm preview**: pattern in preview block + ask continue/edit/cancel
> - **Validator rules pattern**: cite `validator-rules.md` + reject conditions
> - **State machine transitions**: `ingested → analyzed → qa_done → applied`
> - **Citation rule**: `({path}:L..-L..)` format invariant
> - **Redaction post-pass**: scan + STOP-on-secret pattern
> - **Hard blocklist + AskUserQuestion gate**: pattern config guard 2 tầng
> - **Output schema header style**: `# {prefix}NN — {title}` convention
>
> Với mỗi proposal:
> 1. **name** (kebab-case, vd `workspace-resolve-step0`)
> 2. **status** — `[NEW]` | `[EXTENDS:{existing-pattern}]` | `[DUPLICATE-OF:{existing-pattern}]`
> 3. **occurrences** — list command/agent file:line nơi pattern xuất hiện ≥ 2 lần
> 4. **canonical structure** — 5–7 dòng hoặc Mermaid mô tả flow
> 5. **invariants** — điều kiện không được vi phạm (vd "STOP nếu .workspace rỗng")
> 6. **diff vs existing** (nếu EXTENDS hoặc DUPLICATE-OF)

**Output schema**:
```markdown
# a03 — Agent Prompt Pattern Proposals

## P-001 — workspace-resolve-step0  [NEW | EXTENDS:{x}]

### Occurrences
- `/code-analyze` Step 0 `(.claude/commands/code-analyze.md:L26-L36)`
- `/evidence-ingest` Step 0 `(.claude/commands/evidence-ingest.md:L..)`
- `/wiki-setup` Step 0 `(.claude/commands/wiki-setup.md:L..)`

### Canonical structure
1. Tìm `.claude/wiki.json` từ cwd đi lên parent
2. Đọc → resolve `wiki_root` (absolute / relative / fallback global)
3. STOP nếu thiếu hoặc `.workspace` rỗng
4. Set `{ws} = {wiki_root}/workspaces/{workspace}/`
5. Validate `{ws}/workspace.md` tồn tại

### Invariants
- KHÔNG đọc workspace khác `.workspace` đang active
- `wiki_root: "."` resolve relative TỚI parent của `.claude/`, KHÔNG phải cwd

### Diff vs existing
- ...

## P-002 — askuser-confirm-preview  [...]
```

---

## CORE-AGENTIC A4 — Prompt/File Contract Proposals

**Output**: `a04-contract-proposals.md`  ← **alias** của `c04-contract-proposals.md` cho agentic-engine.

**Inputs**:
- `sources/{id}/raw.md` Section 4, 5, 7 (commands, agents, templates)
- `a02-command-map.md`
- `{ws}/platform/contracts/*.md`

**Prompt**:
> Phát hiện **invariant rules / format contracts** mà nhiều commands/agents/templates đang follow — đây là contracts nên document chính thức:
>
> - **File layout contracts** — vd `evidence/sources/{evid-id}/{raw.md, source.yaml, raw.normalized.md?}` invariant
> - **evid-id format contracts** — `{date}-{src}-{slug}` pattern
> - **Section structure invariants** — vd "raw.md PHẢI có 10 sections theo thứ tự X"
> - **Citation format contracts** — `({path}:L<start>-L<end>)` relative tới repo root
> - **State machine contracts** — `ingested → analyzed → qa_done → applied`
> - **Frontmatter schema** — vd evidence source.yaml required fields
> - **Naming conventions** — kebab-case slash commands, agent names
> - **Redaction contracts** — REDACTED-SECRET / REDACTED-EMAIL / REDACTED-URL placeholder format
>
> Với mỗi proposal:
> 1. **name** (vd `evidence-file-layout-contract`)
> 2. **status** — `[NEW]` | `[EXTENDS:{x}]` | `[CONFLICT:{x}]`
> 3. **rule statement** — clear, không mơ hồ
> 4. **observed evidence** — list cụ thể từ commands/agents/templates
> 5. **counter-examples** — case vi phạm (nếu có)
> 6. **diff vs existing**

**Output schema**:
```markdown
# a04 — Prompt/File Contract Proposals

## C-001 — evid-id-format  [NEW | EXTENDS:{x}]

### Rule
Mọi evidence ID PHẢI follow `{YYYY-MM-DD}-{src}-{slug}`:
- `src ∈ {paste, api, mcp, code, engine, platform}`
- `slug` = kebab-case, ≤ 30 chars
- Trùng → append `-{n}`

### Observed evidence
- ✅ `code-snapshot-conventions.md Section 3` định nghĩa format `(agents/pipeline/code-snapshot-conventions.md:L40-L62)`
- ✅ `/evidence-ingest` follow `(.claude/commands/evidence-ingest.md:L..)`
- ✅ `/code-analyze` follow `(.claude/commands/code-analyze.md:L..)`

### Counter-examples
- (none detected)

### Confidence
- Coverage: 5/5 ingestion entry-points follow → high

## C-002 — ...
```

---

## CORE-AGENTIC 8 — Knowledge Gap Map (agentic-engine variant)

**Output**: `08-knowledge-gaps.md` ← cùng filename với CORE 8.

**Inputs**:
- All aXX files (a01–a04)
- `{ws}/patterns-index.md`
- `{ws}/projects/*/knowledge-map.md`
- `{ws}/platform/contracts/*.md`

**Prompt**:
> Xác định gap giữa **engine implementation** và **wiki của workspace `{active}`**:
> 1. Slash command / agent trong a02 chưa có doc trong `{ws}/projects/*/services/` (hoặc tương đương)
> 2. Agent prompt pattern (a03) chưa có entry trong `{ws}/patterns-index.md`
> 3. Contract proposal (a04) chưa có file trong `{ws}/platform/contracts/`
> 4. Doc đã có nhưng stale (mô tả không match raw.md)
> 5. Implicit decision (vd "switched from X to Y", "deprecate command Z") chưa có ADR
>
> Mỗi gap đánh `[BLOCKING]` hoặc `[NICE-TO-HAVE]`.

Output schema giống CORE 8 ở critical-analysis-prompts.md.

---

## CORE 4 — Question Generator (agentic-engine override)

**Output**: `04-questions.md`  ← reuse CORE 4 hiện tại.

**Override prompt khi code_variant=agentic-engine**:
> Generate question pool dựa vào a01–a04 và 08-knowledge-gaps.
> Question types điển hình cho agentic-engine evidence:
>
> 1. **Pattern confirmation** (P0):
>    - "Pattern A-X (`{name}`) có nên thêm vào `{ws}/platform/patterns/` (engine pattern category)?"
>
> 2. **Contract confirmation** (P0):
>    - "Contract C-X (`{rule}`) có chính xác là rule chính thức? Counter-examples cần fix hay là intentional exception?"
>
> 3. **Command/agent doc** (P1):
>    - "Command/agent `{name}` có cần doc riêng không? Hay merge?"
>    - "`{name}` thuộc project nào? `{ws}/projects/{?}` (hoặc workspace-level engine doc?)"
>
> 4. **ADR** (P1):
>    - "Decision detect được trong a06 (vd 'split /code-analyze thành 2 mode') có cần ADR riêng?"
>
> 5. **MCP integration** (P0/P1):
>    - "MCP server `{name}` có phải runtime requirement bắt buộc, hay optional? Cần doc setup?"
>
> 6. **Counter-arguments** (P3):
>    - "Có lý do gì pattern A-X không nên canonicalize không?"

---

## ON-DEMAND A5 — Command/Agent Doc Auto-Draft

**Output**: `a05-doc-drafts.md`

**Inputs**: `a02-command-map.md`, raw.md, `templates/service.md` (reuse) hoặc engine-specific template.

**Prompt**:
> Với mỗi entry-point mark `[NEW]` trong a02, sinh draft doc theo `templates/service.md` (adapted):
> - Purpose, Inputs (args), Outputs (file/state changes), Flow (referencing patterns from a03), Failure handling từ raw.md.
> - Mark field chưa có data là `{TODO: ask expert}`.
> - KHÔNG invent — chỉ điền những gì raw.md cite được.

---

## ON-DEMAND A6 — Implicit Decision Detector (agentic-engine)

**Output**: `a06-decision-drafts.md`

**Inputs**: `sources/{id}/raw.md` Section 9 (git), Section 4–7 (commands/agents/templates), commit messages.

**Prompt**:
> Phát hiện **implicit decisions** chưa có ADR:
> 1. **Command/agent split or merge** — git history cho thấy 1 command tách thành nhiều, hoặc nhiều merge thành 1
> 2. **Template restructure** — Section count đổi (vd raw.md trước có 8 sections, giờ có 10)
> 3. **MCP server choice** — switch từ server X→Y, hoặc add/remove server
> 4. **Hook strategy** — chuyển từ "no hooks" sang "PreToolUse blocking", v.v.
> 5. **Variant introduction** — vd thêm `code_variant: agentic-engine` (chính ADR này!)

Output schema giống C6.

---

## ON-DEMAND A7 — Settings/Hook Override Map

**Output**: `a07-settings-overrides.md`

**Inputs**: raw.md Section 8 (hooks & settings), `a03-pattern-proposals.md`, `{ws}/platform/patterns/*.md`.

**Prompt**:
> So sánh **settings.json hooks/permissions thực tế** với **default expected** từ engine pattern docs.
>
> Với mỗi override:
> 1. **scope** — global / workspace / project
> 2. **type** — hook / permission / env-var
> 3. **default** — expected từ pattern doc
> 4. **actual** — config hiện tại
> 5. **inferred reason** — nếu commit/comment giải thích

Output: table tương tự C7.

---

## Run order (agentic-engine)

1. `/evidence-analyze --id {id}` → CORE-AGENTIC A1, A2, A3, A4 + CORE 4 + CORE 8.
2. `/evidence-qa --id {id}` → C8 QA Recommender chạy bình thường (input là `04-questions.md` + a0X files thay c0X).
3. ON-DEMAND:
   - `--prompt a05` → command/agent doc drafts
   - `--prompt a06` → ADR drafts
   - `--prompt a07` → settings overrides
4. `/evidence-apply --id {id} --mode update` → ghi vào `{ws}/platform/patterns/`, `{ws}/platform/contracts/`, `{ws}/projects/{p}/services/` (hoặc engine-level doc location), `{ws}/decisions/`.
