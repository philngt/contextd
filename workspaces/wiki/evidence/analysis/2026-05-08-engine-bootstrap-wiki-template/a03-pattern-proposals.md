# a03 — Agent Prompt Pattern Proposals

> Source evidence: `2026-05-08-engine-bootstrap-wiki-template` (variant=agentic-engine)
> Inputs: `raw.md` Section 4 (commands), 5 (agents), 6 (pipeline) + `a01-engine-stack.md` + `a02-command-map.md` + `{ws}/patterns-index.md` (empty) + `{ws}/platform/patterns/` (empty)

Workspace baseline: `{ws}/platform/patterns/` rỗng → mọi proposal status = `[NEW]`.

---

## P-001 — workspace-resolve-step0  [NEW]

### Occurrences (15 commands)
- `/evidence-analyze` `(.claude/commands/evidence-analyze.md:L28-L36)`
- `/code-analyze` `(.claude/commands/code-analyze.md:L26-L36)`
- `/wiki-trace` `(.claude/commands/wiki-trace.md)` (Bước 0)
- `/wiki-viz` `(.claude/commands/wiki-viz.md)` (Bước 0)
- `/wiki-eval` `(.claude/commands/wiki-eval.md)` (Bước 0)
- `/use-wiki` `(.claude/commands/use-wiki.md)` (Bước 0)
- `/obsidian-ingest` `(.claude/commands/obsidian-ingest.md)` (Bước 0)
- `/evidence-qa` `(.claude/commands/evidence-qa.md)` (Bước 0)
- `/evidence-apply` `(.claude/commands/evidence-apply.md)` (Bước 0)
- `/evidence-ingest` `(.claude/commands/evidence-ingest.md)` (Bước 0)
- `/list-workspaces` `(.claude/commands/list-workspaces.md)` (Bước 0)
- `/switch-workspace` `(.claude/commands/switch-workspace.md)` (Bước 0)
- `/new-workspace` `(.claude/commands/new-workspace.md)` (Bước 0)
- `/rebase-wiki` `(.claude/commands/rebase-wiki.md)` (Bước 0)
- `/update-wiki` `(.claude/commands/update-wiki.md)` (Bước 0)

### Canonical structure
```
1. Tìm `.claude/wiki.json`: từ `<cwd>` đi lên parent cho tới khi gặp file. Lưu `wiki_json_dir`.
2. Đọc file → `workspace` + `wiki_root` resolve theo system-prompt.md `wiki_root` Resolution Rule:
   - Absolute path → dùng nguyên
   - Relative ("." / "./...") → resolve relative TỚI `project_root` (= parent của `.claude/`)
   - `null`/empty → fallback `~/.claude/wiki-global.json#wiki_root`
3. STOP nếu file thiếu hoặc `.workspace` rỗng → guide `/switch-workspace` hoặc `/wiki-setup`.
4. Set `workspace_active = .workspace`, `effective_wiki_root = <resolved absolute>`,
   `{ws} = {effective_wiki_root}/workspaces/{workspace_active}/`.
5. Validate: `{ws}/workspace.md` tồn tại.
```

### Invariants
- KHÔNG đọc/copy knowledge từ workspace khác `{workspace_active}`.
- `wiki_root: "."` resolve relative TỚI parent của `.claude/`, KHÔNG phải `.claude/` literal, KHÔNG phải cwd.
- `.workspace` rỗng → STOP, không guess.
- `{ws}/workspace.md` missing → workspace bị broken, không tiếp tục.

### Diff vs existing
- N/A (workspace empty).

### Recommendation
**Canonicalize** thành pattern doc tại `{ws}/platform/patterns/workspace-resolve-step0.md`. Mọi command mới PHẢI start với Bước 0 này. Workspace override không apply (engine-level invariant).

---

## P-002 — askuser-confirm-preview  [NEW]

### Occurrences
- `/code-analyze` Bước 3 — preview block + "Tiếp tục? (yes/edit-scope/cancel)" `(.claude/commands/code-analyze.md:L106-L182)`
- `/evidence-ingest` (preview confirm trước khi commit ingest) `(.claude/commands/evidence-ingest.md)`
- `/wiki-setup` (preview detected components trước khi tạo wiki.json) `(.claude/commands/wiki-setup.md)`
- `/new-workspace` (preview workspace skeleton trước khi scaffold) `(.claude/commands/new-workspace.md)`

### Canonical structure
```
1. Build preview block — list mọi field user cần verify:
     - Workspace, Project, Variant, Branch, Git SHA, Scope, Evid-id, Label, ...
2. List "Sẽ tạo:" với đường dẫn files chính sẽ thay đổi.
3. AskUserQuestion với 3 options điển hình:
     - {primary action} (Recommended) → continue
     - edit-{detail}                     → quay lại bước resolve
     - cancel                             → STOP
4. Wait user. Branch theo answer.
```

### Invariants
- Preview PHẢI hiển thị mọi field "non-trivial to recompute" (workspace lock, scope, file paths sẽ ghi).
- Cancel option BẮT BUỘC có mặt — user luôn có exit lane.
- Edit option đưa user back đến bước trước, KHÔNG qua step intermediate.
- Sau confirm = irreversible (file sẽ được tạo) → preview là last line of defense.

### Recommendation
Canonicalize thành `{ws}/platform/patterns/askuser-confirm-preview.md`. Apply cho mọi command có **side effects** lên filesystem (tạo file evidence, edit wiki, scaffold workspace).

---

## P-003 — hard-blocklist-plus-askuser-gate  [NEW]

### Occurrences
- `/code-analyze` Bước 4.3 — config guard 2 tầng `(.claude/commands/code-analyze.md:L207-L229)`
- `agents/pipeline/code-snapshot-conventions.md` Section 6 — full spec `(agents/pipeline/code-snapshot-conventions.md:L156-L251)`

### Canonical structure
```
Tầng 1 (Hard blocklist — NEVER READ):
  - Match patterns: `.env`, `*-prod.yaml`, `*.key`, `*.pem`, `*secret*`, `secrets/`...
  - Khớp → ghi `[HARD-BLOCKED: {path}]`, không đọc. Không có flag bypass.

Tầng 2 (User confirm via AskUserQuestion):
  - Còn lại sau Tầng 1 → list cho user, AskUserQuestion chọn include/skip per-file.
  - File không chọn → `[SKIPPED-BY-USER: {path}]`.

Tầng 3 (Redaction post-read):
  - Tokens/passwords/keys → `<REDACTED-SECRET>`.
  - Internal hostnames có credentials → `<REDACTED-URL>`.
  - Emails → `<REDACTED-EMAIL>`.

Tầng 4 (Guard log):
  - Cuối Section, append "Config guard log": included / hard-blocked / skipped-by-user.

Tầng 5 (Workspace override):
  - Workspace có thể ADD vào blocklist qua `{ws}/evidence/STORAGE.md`. KHÔNG được REMOVE.
```

### Invariants
- Hard blocklist KHÔNG có flag bypass — user explicit cũng không thể đọc `.env`.
- Workspace override CHỈ THÊM, không thu hẹp engine blocklist.
- Default state = block-all; flag `--allow-configs` OPT-IN.

### Recommendation
Canonicalize thành `{ws}/platform/patterns/secrets-blocklist-gate.md`. Apply cho mọi command đọc file content nhạy cảm (configs, credentials, env files). Có thể reuse trong workflow ingest external sources có content nhạy cảm.

---

## P-004 — redaction-post-pass  [NEW]

### Occurrences
- `/code-analyze` Bước 4.10 — scan post-build `(.claude/commands/code-analyze.md:L274-L282)`
- `agents/pipeline/code-snapshot-conventions.md` Section 6.2 `(agents/pipeline/code-snapshot-conventions.md:L218-L238)`

### Canonical structure
```
Sau khi build raw.md/output xong, BẮT BUỘC scan toàn file cho pattern:
  - `password\s*[:=]\s*[^<\s]+`               → `<REDACTED-SECRET>`
  - `(token|api[-_]?key|secret|jwt[-_]?key)\s*[:=]\s*[^<\s]+` → `<REDACTED-SECRET>`
  - Email regex `[\w.+-]+@[\w-]+\.[\w.-]+`     → `<REDACTED-EMAIL>` (ngoại trừ Section 1 README excerpt)
  - Internal URL có credentials inline `https?://\w+:\w+@` → `<REDACTED-URL>`

Nếu **vẫn còn** match sau redaction → STOP với error
  `SECRET DETECTED IN SNAPSHOT — fix manually before continue`.
```

### Invariants
- Redaction chạy SAU khi build (không phải in-place during build).
- STOP-on-secret = irreversible: KHÔNG ghi file output nếu còn match.
- Pattern coverage: password, token/api-key/secret/jwt-key, email, URL-with-creds.

### Recommendation
Canonicalize thành `{ws}/platform/patterns/redaction-post-pass.md`. Apply cho mọi output có khả năng chứa secrets (snapshots, logs, qa exports, reports). Companion cho P-003.

---

## P-005 — evidence-state-machine  [NEW]

### Occurrences
- `/evidence-ingest` (writes state=`ingested`)
- `/evidence-analyze` Bước 6 — transition `ingested → analyzed` `(.claude/commands/evidence-analyze.md)`
- `/evidence-qa` (transitions `analyzed → qa_in_progress ⇄ qa_awaiting_external → qa_done`)
- `/evidence-apply` (transitions `qa_done → applied`)
- `/code-analyze` Bước 7 (delegates state to `/evidence-analyze`) `(.claude/commands/code-analyze.md:L412-L420)`
- `agents/pipeline/evidence-state-rules.md` `(agents/pipeline/evidence-state-rules.md:L1)`
- `templates/evidence-index.md` Section "State legend" `(templates/evidence-index.md:L23-L36)`
- `workspaces/wiki/evidence/_index.md` Section "State legend" `(workspaces/wiki/evidence/_index.md:L21-L34)`

### Canonical structure
```
States: ingested → analyzed → qa_in_progress ⇄ qa_awaiting_external → qa_done → applied → archived

Transitions (only):
  - ingest commands              → ingested
  - /evidence-analyze (CORE done) → analyzed
  - /evidence-qa                 → qa_in_progress
  - /evidence-qa (defer expert)  → qa_awaiting_external
  - /evidence-qa (verified-facts done) → qa_done
  - /evidence-apply              → applied
  - manual archive               → archived

Validation:
  - Mỗi transition chỉ commit khi đủ artifact requirement (vd CORE set complete).
  - State stored as row trong `{ws}/evidence/_index.md` Active table.
  - KHÔNG sửa tay (sẽ bị overwrite). Manual edit phải mark `(manual)`.
```

### Invariants
- State machine là DAG (no skip). KHÔNG được apply trước khi qa_done.
- `_index.md` is single source of truth — không lưu state ở `source.yaml`.
- Workspace lock invariant I-2: state transition CHỈ trong workspace_at_ingest.

### Recommendation
Canonicalize thành `{ws}/platform/patterns/evidence-state-machine.md` HOẶC promote thành CONTRACT (xem a04 C-005). Pattern + contract pair.

---

## P-006 — citation-rule-relative-path  [NEW]

### Occurrences
- `agents/pipeline/code-snapshot-conventions.md` Section 5 — `({path}:L<start>-L<end>)` invariant `(agents/pipeline/code-snapshot-conventions.md:L138-L155)`
- `agents/pipeline/code-analysis-prompts.md` cite formats trong mọi prompt `(agents/pipeline/code-analysis-prompts.md:L21-L24)`
- `agents/pipeline/critical-analysis-prompts.md` cite formats `(agents/pipeline/critical-analysis-prompts.md)`
- Used throughout raw.md output (vd this very file)
- `validator-rules.md` reject claims missing citation `(agents/pipeline/code-analysis-prompts.md:L519-L523)`

### Canonical structure
```
Format: ({file-path-relative-to-repo-root}:L<start>-L<end>)

Examples:
  (src/main/java/com/example/Foo.java:L42-L58)
  (.claude/commands/code-analyze.md:L106-L182)
  (raw.md#section-4)         ← when cite within snapshot
  ({ws}/platform/patterns/foo.md#section)  ← when cite into wiki

Bundle mode (a04 contract subset):
  ({repo-name}/{path}:L..-L..)
  (core-framework/src/main/java/Foo.java:L42-L58)

Rules:
  - PATH RELATIVE TO REPO ROOT (not absolute, not cwd-relative).
  - Line range: single line `L42` or range `L42-L58`.
  - Anchor citation `#section-N` cho raw.md sections.
  - Mỗi claim PHẢI cite (no claim without citation).
```

### Invariants
- Path NEVER absolute (no `/Users/...` or `D:/...`).
- Path NEVER cwd-relative (no `./foo`).
- Cite missing → re-prompt 1 lần với reminder "missing citations" → vẫn thiếu thì mark `[NO-CITE]` + warn user `(.claude/commands/evidence-analyze.md Bước 4)`.

### Recommendation
Canonicalize thành `{ws}/platform/patterns/citation-rule.md` HOẶC promote thành CONTRACT C-006 (xem a04). Pattern engineering rule áp dụng mọi analysis output.

---

## P-007 — multi-stage-subagent-pipeline  [NEW]

### Occurrences
- `/use-wiki` 5-stage flow `(.claude/commands/use-wiki.md)`
- `agents/pipeline/README.md` Section "Pipeline (5 stage)" `(agents/pipeline/README.md:L27-L46)`
- `agents/pipeline/multi-agent-pipeline.md` (full spec — I/O schemas)
- `agents/pipeline/PIPELINE-VISUAL.md` (Mermaid diagram)

### Canonical structure
```
User Task
   ↓
[Stage 0] Main agent              → resolve workspace + wiki_root  (P-001)
   ↓
[Stage 1] wiki-planner            → parse intent → intent JSON     (A-001)
   ↓
[Stage 2] wiki-context-selector   → retrieve + filter + slice      (A-002)
                                  → ghi {project_dir}/.claude/context/current-task.md
   ↓
[Stage 2.5] wiki-plan-reviewer    → APPROVED / BLOCK gate          (A-003)
   ↓
[Stage 3] Main agent (Builder)    → đọc current-task.md, code      (no subagent)
                                  → theo prompt-template.md
   ↓
[Stage 4] wiki-reviewer (optional)→ check code vs context          (A-005)
                                  → theo validator-rules.md
   ↓
Output
```

### Invariants
- Stage 2.5 gate là blocking — BLOCK → STOP, không tiếp tục Stage 3.
- Stage 4 là optional nhưng recommended cho task wiki-aware.
- Sub-agents tools allowlist (P-008 candidate? — see C-008): planner/context/plan-reviewer/reviewer = read-only, curator = write.
- Trace emitted to `.claude/runs/{run_id}/` cho `/wiki-trace` consume `(agents/pipeline/observability.md:L1)`.

### Recommendation
Canonicalize thành `{ws}/platform/patterns/multi-stage-subagent-pipeline.md`. Đây là **flagship pattern** của engine — mọi command wiki-aware nên follow.

---

## P-008 — variant-discriminated-dispatcher  [NEW]

### Occurrences
- `/code-analyze` Bước 1.4 (variant detection) + Bước 4 (variant-specific build) + Bước 7 (variant-specific analyze) `(.claude/commands/code-analyze.md:L43-L70, L194-L297, L412-L420)`
- `/evidence-analyze` Bước 2 (sub-branch theo `code_variant`) — vừa được patched ở Phase 1 `(.claude/commands/evidence-analyze.md)`
- `agents/pipeline/code-snapshot-conventions.md` Section 12 (agentic-engine variant) `(agents/pipeline/code-snapshot-conventions.md:L324-L399)`
- `agents/pipeline/code-analysis-prompts.md` Variant dispatch table `(agents/pipeline/code-analysis-prompts.md:L8-L18)`

### Canonical structure
```
1. Detect variant from explicit flag OR auto-detect markers:
     - `--variant {value}` → use as-is
     - else: count markers per-variant → highest wins; tied → AskUserQuestion

2. Validation gate per variant:
     - variant=code: require `.git/` OR build file
     - variant=agentic-engine: require ≥ 1 agentic marker (agents/, .claude/commands/, etc.)

3. Default scope per variant.

4. Output template per variant (`templates/{variant}-snapshot.md`).

5. Source.yaml writes `code_variant: {value}` (default omitted = `code`).

6. Downstream commands dispatch on `source.yaml#code_variant`:
     - `code` → CORE-CODE prompts (cXX)
     - `agentic-engine` → CORE-AGENTIC prompts (aXX)
     - text source_types → CORE prompts (NN)

7. Cross-variant prompt validation: reject `--prompt c05` cho agentic-engine, etc.
```

### Invariants
- `code_variant` field default omitted → treat as `code` (backward-compat).
- variant=agentic-engine softens validation gate (no .git/build-file required).
- evid-id prefix differs per variant (`code` vs `engine` vs `platform` for bundle).
- Origin field in source.yaml differs (`code:{slug}@{sha}` vs `engine:{slug}@{sha}`).

### Recommendation
Canonicalize thành `{ws}/platform/patterns/variant-discriminated-dispatcher.md`. Pattern này xuất hiện vì introduce variant agentic-engine — formalize để khi thêm variant mới (vd `--variant infra` cho Terraform/k8s codebase) không phải reinvent.

---

## Notes for downstream prompts

1. **8 patterns proposed** — tất cả `[NEW]` vì workspace `wiki` empty.
2. **P-005 và P-006 dual-nature**: vừa pattern (re-implementation skeleton) vừa contract (invariant rule). a04 sẽ promote subset thành contracts (C-005, C-006).
3. **P-007 là flagship** — đại diện engine identity. Khi user document workspace, P-007 nên là pattern đầu tiên.
4. **P-008 là byproduct** của variant introduction — chính variant agentic-engine đã follow pattern này. Nếu workspace promote pattern này, future variant additions sẽ nhanh hơn.
5. **Coverage check**: 19 commands + 5 sub-agents + 16 pipeline docs đều check qua ≥ 1 pattern. Confidence: HIGH (mỗi pattern có ≥ 2 occurrences, 6/8 patterns có ≥ 4 occurrences).
