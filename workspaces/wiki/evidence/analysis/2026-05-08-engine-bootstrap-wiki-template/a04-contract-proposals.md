# a04 — Prompt/File Contract Proposals

> Source evidence: `2026-05-08-engine-bootstrap-wiki-template` (variant=agentic-engine)
> Inputs: `raw.md` Section 4 (commands), 5 (agents), 7 (templates) + `a02-command-map.md` + `{ws}/platform/contracts/` (empty)

Workspace baseline: `{ws}/platform/contracts/` rỗng → mọi proposal status = `[NEW]`.

---

## C-001 — evid-id-format  [NEW]

### Rule
Mọi evidence ID PHẢI follow pattern:
```
{YYYY-MM-DD}-{src}-{slug}[-{n}]
```
- `src ∈ {paste, api, mcp, code, engine, platform}`
  - `paste|api|mcp` cho text sources
  - `code` cho variant=code single-repo
  - `engine` cho variant=agentic-engine single-repo
  - `platform` cho bundle mode (multi-repo)
- `slug` = kebab-case, derived từ `--label` (slugify) hoặc fallback project-name, ≤ 30 chars
- `-{n}` suffix khi trùng entry trong `_index.md` (n = 2, 3, ...)

### Observed evidence
- ✅ Single-repo code: format `{date}-code-{slug}` `(agents/pipeline/code-snapshot-conventions.md:L40-L50)`
- ✅ Bundle mode: format `{date}-platform-{slug}` `(agents/pipeline/code-snapshot-conventions.md:L52-L61)`
- ✅ Agentic-engine: format `{date}-engine-{slug}` `(agents/pipeline/code-snapshot-conventions.md:L375-L383)`
- ✅ Text sources: `2026-05-04-paste-PROJ-1234`, `2026-05-03-api-changelog-v2` `(templates/evidence-index.md:L11-L12)`
- ✅ This evidence: `2026-05-08-engine-bootstrap-wiki-template` `(workspaces/wiki/evidence/_index.md:L11)`
- ✅ source.yaml field validation `(templates/evidence-source.yaml:L5)`

### Counter-examples
_(none detected)_

### Confidence
- Coverage: 5/5 ingestion entry-points follow → **high** (●●●)

### Diff vs existing
N/A (workspace empty).

### Recommendation
Canonicalize thành `{ws}/platform/contracts/evid-id-format.md`. Future src additions (vd `--source ticket` cho Jira) phải declare prefix mới và update contract.

---

## C-002 — evidence-file-layout  [NEW]

### Rule
Mỗi evidence set PHẢI follow file layout invariant:
```
{ws}/evidence/sources/{evid-id}/
  ├── source.yaml          (REQUIRED — schema theo C-004)
  ├── raw.{ext}            (REQUIRED — ext ∈ {md, json, html, txt}; với source_type=code: luôn .md)
  └── raw.normalized.md    (CONDITIONAL — auto-tạo nếu raw.{ext} > 50KB; chunked theo Section heading)
```

Sub-paths analysis & qa & apply:
```
{ws}/evidence/analysis/{evid-id}/{NN-name.md|cNN-name.md|aNN-name.md}
{ws}/evidence/qa/{evid-id}/{recommendations.md, batches/, verified-facts.md, pending-external.md?}
{ws}/evidence/_index.md  (single source of truth cho state)
```

Index file:
```
{ws}/evidence/_index.md → Active table + Archived table + State legend
```

### Observed evidence
- ✅ `code-snapshot-conventions.md` Section 2 layout `(agents/pipeline/code-snapshot-conventions.md:L25-L34)`
- ✅ `raw-storage-conventions.md` (engine-level rules) `(agents/pipeline/raw-storage-conventions.md:L1)`
- ✅ Template `evidence-index.md` matches layout `(templates/evidence-index.md:L1)`
- ✅ This evidence layout: `sources/{id}/{raw.md, source.yaml}` + `_index.md` created `(workspaces/wiki/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md:L1)`

### Counter-examples
_(none detected)_

### Confidence: **high** (●●●)

### Recommendation
Canonicalize thành `{ws}/platform/contracts/evidence-file-layout.md`.

---

## C-003 — raw-md-section-structure  [NEW]

### Rule
`raw.md` PHẢI có 10 sections theo thứ tự, mỗi section có anchor `#section-N`. Skip section trống bằng `_(none detected)_` — KHÔNG xóa heading.

**Variant=code (classic runtime):**
```
1. Project metadata
2. Dependencies
3. Configs (gated by --allow-configs)
4. REST endpoints
5. Message consumers
6. Services & components
7. DB schema
8. Public APIs
9. Git summary
10. Notes
```

**Variant=agentic-engine (markdown-heavy):**
```
1. Engine metadata
2. Dependencies (MCP servers, runtime/script-tool deps, external integrations)
3. Configs (gated by --allow-configs)
4. Slash commands
5. Sub-agents & system prompts
6. Pipeline stages / Modules
7. Templates
8. Hooks & settings (gated)
9. Git summary
10. Notes
```

**Bundle mode**: Section 0 (Bundle Overview) trước, sau đó Sections 1–9 lặp per-repo (heading suffix `[{repo-name}]`), kết thúc bằng Docs section nếu có.

### Observed evidence
- ✅ Code variant: full spec `(agents/pipeline/code-snapshot-conventions.md:L67-L86)`; template `(templates/code-snapshot.md:L1)`
- ✅ Agentic-engine variant: full spec `(agents/pipeline/code-snapshot-conventions.md:L385-L402)`; template `(templates/agentic-engine-snapshot.md:L1)`
- ✅ Bundle mode: `(agents/pipeline/code-snapshot-conventions.md:L88-L133)`
- ✅ This evidence raw.md: 10 sections agentic-engine variant `(workspaces/wiki/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md:L1)`

### Counter-examples
_(none detected — both templates strictly follow the schema)_

### Confidence: **high** (●●●)

### Diff vs existing
N/A (workspace empty).

### Recommendation
Canonicalize thành `{ws}/platform/contracts/raw-md-section-structure.md`. Multiple variants documented in same contract — variant table makes contract self-extensible khi thêm variant mới (vd `infra`, `data-pipeline`).

---

## C-004 — source-yaml-required-fields  [NEW]

### Rule
`source.yaml` PHẢI có required fields:
```yaml
evid_id: "{C-001-format}"
source_type: "paste|api|mcp|code"
origin: "{description-with-source-pointer}"
label: "{≤ 30-char human-readable}"
fetched_at: "{ISO8601 với timezone}"
fetched_by: "{email user}"
sha256: "{SHA256 của raw.{ext}}"
raw_filename: "raw.{ext}"
raw_size_bytes: {integer}
normalized: {bool}                # true nếu có raw.normalized.md
workspace_at_ingest: "{name}"     # CRITICAL — invariant I-2 lock
```

**Conditional fields (source_type=code)**:
```yaml
code_variant: "code|agentic-engine"   # default omitted → "code"
git_sha: "{full 40-char SHA hoặc 'unmanaged-{sha256-tree}'}"
git_branch: "{branch hoặc 'unmanaged'}"
code_scope: ["{glob}", ...]
code_repo_path: "{path}"
```

**Bundle mode**:
```yaml
code_repos: [{name, path, role, variant?, git_sha, git_branch, scope}, ...]
include_docs: [{path, type, label}, ...]   # optional
```

### Observed evidence
- ✅ Template definition `(templates/evidence-source.yaml:L1-L54)`
- ✅ This evidence source.yaml has all required fields `(workspaces/wiki/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/source.yaml:L1-L40)`
- ✅ Validator V-02 reject if `source_type=code` mà `git_sha` null `(agents/pipeline/code-snapshot-conventions.md:L271-L279)`

### Counter-examples
_(none detected)_

### Confidence: **high** (●●●)

### Recommendation
Canonicalize thành `{ws}/platform/contracts/source-yaml-schema.md`. Companion với C-002 (file layout). Conditional fields cho `source_type=code` là sub-contract (có thể tách C-004a sau).

---

## C-005 — evidence-state-machine-transitions  [NEW]

### Rule
State machine của `_index.md` strict DAG, mỗi transition có owning command:

```
ingested → analyzed → qa_in_progress ⇄ qa_awaiting_external → qa_done → applied → archived
```

**Transition ownership** (chỉ command sau được phép thực hiện transition tương ứng):

| Transition | Owning command | Precondition |
|------------|----------------|--------------|
| (none) → ingested | `/evidence-ingest`, `/code-analyze`, `/obsidian-ingest` | source.yaml valid + raw.{ext} written |
| ingested → analyzed | `/evidence-analyze` | đủ CORE set (text: 4 files; code variant=code: 6 files; code variant=agentic-engine: 6 files) |
| analyzed → qa_in_progress | `/evidence-qa` | recommendations.md generated |
| qa_in_progress ⇄ qa_awaiting_external | `/evidence-qa` | có ≥ 1 P0/P1 deferred to expert |
| qa_in_progress → qa_done | `/evidence-qa` | verified-facts.md complete |
| qa_done → applied | `/evidence-apply` | dry-run review pass |
| applied → archived | manual (no command) | mark `(manual)` row |

**Invariants**:
- KHÔNG skip stage (vd ingested → applied = invalid).
- `_index.md` là single source of truth — KHÔNG lưu state ở `source.yaml`.
- Manual edit `_index.md` PHẢI mark `(manual)` để audit trail rõ ràng `(templates/evidence-index.md:L4-L5)`.
- I-2 workspace lock: state transition CHỈ trong `workspace_at_ingest` `(agents/pipeline/evidence-state-rules.md)`.

### Observed evidence
- ✅ State legend `(templates/evidence-index.md:L23-L36)`
- ✅ State transitions diagram `(templates/evidence-index.md:L33-L37)`
- ✅ This workspace `_index.md` legend `(workspaces/wiki/evidence/_index.md:L21-L34)`
- ✅ `/evidence-analyze` Bước 6 transition logic `(.claude/commands/evidence-analyze.md Bước 6)`
- ✅ Reference: `agents/pipeline/evidence-state-rules.md` `(agents/pipeline/evidence-state-rules.md:L1)`

### Counter-examples
_(none detected — state model consistent across docs)_

### Confidence: **high** (●●●)

### Recommendation
Canonicalize thành `{ws}/platform/contracts/evidence-state-machine.md`. **Companion** với P-005 (pattern). Pattern describes implementation; contract describes invariant.

---

## C-006 — citation-format  [NEW]

### Rule
Mọi claim trong analysis/snapshot output PHẢI có citation, format:
```
({path}:L<start>[-L<end>])           ← cite vào file thật trong repo
(raw.md#section-N)                    ← cite vào snapshot section
(raw.md#L<start>-L<end>)              ← cite vào snapshot line range
({ws}/path/to/file.md#section)        ← cite vào wiki workspace
({repo-name}/{path}:L..-L..)          ← bundle mode (repo prefix)
```

**Path rules**:
- PATH RELATIVE TO REPO ROOT (NOT absolute, NOT cwd-relative).
- Single line: `L42`. Range: `L42-L58`.
- Anchor: `#section-N` cho raw.md sections; `#heading-slug` cho markdown sub-section.

**Validator behavior**:
- Cite missing → analyzer re-prompt 1 lần với reminder.
- Vẫn thiếu → mark `[NO-CITE]` + warn user.
- Cite path ngoài `code_scope` → reject.
- Cite path workspace khác `workspace_at_ingest` → reject.

### Observed evidence
- ✅ Single-repo cite rule `(agents/pipeline/code-snapshot-conventions.md:L138-L155)`
- ✅ Bundle cite rule `(agents/pipeline/code-snapshot-conventions.md:L146-L150)`
- ✅ Analysis prompt cite formats `(agents/pipeline/code-analysis-prompts.md:L21-L24)`
- ✅ Validator behavior `(.claude/commands/evidence-analyze.md Bước 4)`
- ✅ Validator reject conditions `(agents/pipeline/code-analysis-prompts.md:L519-L523)`
- ✅ This file follows the rule throughout

### Counter-examples
_(none detected)_

### Confidence: **high** (●●●)

### Recommendation
Canonicalize thành `{ws}/platform/contracts/citation-format.md`. **Companion** với P-006 (pattern). Universal rule cho mọi analysis/snapshot/report output.

---

## C-007 — slash-command-naming  [NEW]

### Rule
Slash commands trong `.claude/commands/` PHẢI follow naming:
```
/{kebab-case-lowercase}
```
- Filename `.claude/commands/{kebab-case}.md`
- Invocation `/{kebab-case}` (no positional or kwargs in name itself)
- Multi-word: hyphen separator (`/wiki-setup`, `/evidence-ingest`, `/code-analyze`)
- Verb-first hoặc subject-first consistent within group:
  - "verb-subject": `/list-workspaces`, `/switch-workspace`, `/new-workspace`
  - "subject-verb": `/wiki-setup`, `/wiki-detect`, `/wiki-trace`, `/wiki-report`
  - "subject-action" (evidence pipeline): `/evidence-ingest`, `/evidence-analyze`, `/evidence-qa`, `/evidence-apply`

### Observed evidence
All 19 commands follow:
- Workspace ops: `/wiki-setup`, `/wiki-detect`, `/switch-workspace`, `/new-workspace`, `/list-workspaces` `(.claude/commands/README.md:L16-L20)`
- Wiki usage: `/use-wiki`, `/update-wiki`, `/rebase-wiki` `(.claude/commands/README.md:L28-L30)`
- Codebase: `/code-analyze` `(.claude/commands/README.md:L38)`
- Reporting: `/wiki-report` `(.claude/commands/README.md:L48)`
- Observability: `/wiki-trace`, `/wiki-eval`, `/wiki-viz` `(.claude/commands/README.md:L58-L59)`, `(.claude/commands/wiki-viz.md:L1)`
- Evidence: `/evidence-ingest`, `/obsidian-ingest`, `/evidence-analyze`, `/evidence-qa`, `/evidence-apply` `(.claude/commands/README.md:L72-L76)`

### Counter-examples
_(none — 19/19 conform)_

### Confidence: **high** (●●●)

### Recommendation
Canonicalize thành `{ws}/platform/contracts/slash-command-naming.md`.

**Note**: Mixed convention "verb-subject" vs "subject-verb" trong cùng group (vd workspace ops trộn cả hai). Có thể tách contract C-007a refining convention sau khi user confirm preference.

---

## C-008 — sub-agent-frontmatter-schema  [NEW]

### Rule
Mọi file trong `.claude/agents/` PHẢI có frontmatter YAML với required fields:
```yaml
---
name: {kebab-case}                  # MUST match filename (without .md)
description: {1-3 sentence}         # bao gồm "DÙNG KHI ..." + "KHÔNG DÙNG ..." patterns
tools: {tool-list-comma-separated}  # vd "Read, Glob, Grep" hoặc "Read, Edit, Write, Glob, Grep"
model: {haiku|sonnet|opus}          # default sonnet
---
```

**`tools` allowlist convention** (observed):
- Read-only roles (planner, context-selector, plan-reviewer, reviewer): `Read, Glob, Grep` (+ optional `Write` cho context-selector ghi current-task.md)
- Write roles (curator): `Read, Edit, Write, Glob, Grep`

**`description` convention**: chứa 2 phần — "DÙNG KHI X" (positive trigger) + "KHÔNG DÙNG để Y" (negative trigger / scope constraint).

### Observed evidence
- ✅ `wiki-planner` `(.claude/agents/wiki-planner.md:L2-L5)` — name, description (DÙNG KHI/KHÔNG DÙNG), tools=`Read, Glob, Grep`, model=sonnet
- ✅ `wiki-context-selector` `(.claude/agents/wiki-context-selector.md:L2-L5)` — tools=`Read, Glob, Grep, Write` (write privilege cho current-task.md)
- ✅ `wiki-plan-reviewer` `(.claude/agents/wiki-plan-reviewer.md:L2-L5)` — tools=`Read, Grep, Glob`
- ✅ `wiki-curator` `(.claude/agents/wiki-curator.md:L2-L5)` — tools=`Read, Edit, Write, Glob, Grep` (write role)
- ✅ `wiki-reviewer` `(.claude/agents/wiki-reviewer.md:L2-L5)` — tools=`Read, Grep, Glob`

### Counter-examples
_(none — 5/5 conform)_

### Confidence: **high** (●●●)

### Recommendation
Canonicalize thành `{ws}/platform/contracts/sub-agent-frontmatter-schema.md`. Companion: extension contract C-008a có thể document tools allowlist principle (read-only vs write-allowed) — nhưng đợi user confirm vì hiện chỉ có 5 agents (sample size nhỏ).

---

## Notes for downstream prompts

1. **8 contracts proposed** — tất cả `[NEW]` vì workspace `wiki` empty.
2. **3 pattern–contract pairs**:
   - P-005 (state machine pattern) ↔ C-005 (state machine transitions contract)
   - P-006 (citation rule pattern) ↔ C-006 (citation format contract)
   - P-008 (variant dispatcher pattern) — chưa promote thành contract (chờ thêm variant để verify shape)
3. **C-001..C-004 là core evidence pipeline contracts** — high coverage, high confidence. Apply ngay được.
4. **C-007 (slash-command-naming)** có small inconsistency (verb-subject vs subject-verb mix) — flagged as P2 question trong 04-questions.md.
5. **C-008 (frontmatter)** sample size = 5 → tools-allowlist principle còn yếu evidence; tách C-008a chờ thêm sub-agents future.
6. Cross-variant inconsistency check: KHÔNG áp dụng vì single-repo (không phải bundle mode).
