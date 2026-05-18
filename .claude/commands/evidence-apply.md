# Evidence Apply

Feed `verified-facts.md` (+ optional `10-final-report.md`) vào logic của `/contextd-update` hoặc `/contextd-rebase`. Tạo audit trail tại `applied/{evid-id}/manifest.yaml`.

> Step 4 trong pipeline: ingest → analyze → qa → **apply**.
> Reference: [agents/pipeline/evidence-lifecycle.md](../../agents/pipeline/evidence-lifecycle.md), [contextd-update.md](contextd-update.md), [contextd-rebase.md](contextd-rebase.md).

---

## Input

| Arg                  | Required | Notes                                                              |
|----------------------|----------|--------------------------------------------------------------------|
| `--id`               | yes      | Evid-id. KHÔNG default — apply là destructive cho wiki, phải explicit. |
| `--mode`             | yes      | `update` \| `rebase`                                               |
| `--with-report`      | optional | Chạy CORE 10 (final-report) trước khi apply, attach vào prompt    |
| `--ignore-deferred`  | optional | Cho phép apply khi P0/P1 còn `deferred` (KHÔNG cho phép `awaiting_external`) |
| `--dry-run`          | optional | In list file sẽ sửa và diff dự kiến, KHÔNG ghi                     |
| `--resume`           | optional | Pick up từ checkpoint `applied/{id}/checkpoint.json` (sau crash/Ctrl+C/expert pause) |
| `--status`           | optional | Chỉ in checkpoint hiện tại (step nào đã done, đang ở đâu, file nào đã sửa). Read-only. |
| `--inline`           | optional | Skip wiki-curator delegation, main agent edit trực tiếp. Chỉ dùng khi curator unavailable (test/CI). Mất 1 safety layer — xem Bước 5 "Curator delegation vs inline mode". |

---

## Bước 0 — Workspace check

Theo [workspace-resolution.md Profile A](../../agents/pipeline/workspace-resolution.md#profile-a--active-workspace-required). Set: `wiki_json_dir`, `workspace`, `effective_wiki_root`, `{ws}`.

## Bước 0.5 — Checkpoint init / load

Toàn bộ semantic checkpoint (write convention, resume rules, concurrent-run detect, restart backup) tuân theo invariant **I-8** trong [evidence-lifecycle.md](../../agents/pipeline/evidence-lifecycle.md). Template: `templates/evidence-apply-checkpoint.json`. Checkpoint path: `{ws}/evidence/applied/{id}/checkpoint.json`.

**Modes:**

- **`--status`**: đọc checkpoint, in bảng tiến trình (mode, status, current_step `{i}/{total}`, files modified, facts done/pending, blocker, resume command), KHÔNG chạy apply.
- **`--resume`**: validate `evid_id` + `workspace` + `mode` khớp lệnh hiện tại (mismatch → STOP). Steps `done` SKIP, step `in_progress` re-run từ `current_file` (nếu file-by-file) hoặc từ đầu, step `pending` chạy như mới. Nếu không có checkpoint → STOP. Nếu `status = completed` → STOP, hint dùng `--id` mới.
- **Run mới** (không flag): nếu checkpoint cũ `status ≠ completed` → AskUserQuestion `["Resume", "Restart", "Cancel"]`; Restart backup `checkpoint-{ts}.json.bak` rồi tạo mới từ template (status=`in_progress`, step=`init`).

**Write rule:** sau MỖI sub-step → update `steps[]` entry (status, finished_at, result, files_modified) + top-level (current_step, last_updated_at, files_modified_total, facts_applied/pending, resume_token=`{step}:{current_file_or_subitem}`) → flush ngay. Interrupted giữa file-by-file → ghi `current_file` + `blocker`.

**Concurrency (I-8.1):** Khi initial write, generate `session_id = uuid4()` + ghi `last_writer.{pid,started_at}`. **TRƯỚC mỗi flush** → re-read checkpoint, verify `checkpoint.session_id` khớp session đang chạy. Mismatch → STOP `CHECKPOINT HIJACKED` (xem [evidence-lifecycle.md §I-8.1](../../agents/pipeline/evidence-lifecycle.md)). Read-modify-write phải wrap qua `with_advisory_lock` từ [`scripts/lib/atomic_write.py`](../../scripts/lib/atomic_write.py).

## Bước 1 — Resolve + state validation

1. Đọc `{ws}/evidence/sources/{id}/source.yaml`.
2. **Workspace lock check (I-2)**: `workspace_at_ingest` PHẢI = `{active}`. Nếu không → STOP với error.
3. Đọc `{ws}/evidence/_index.md`, lấy state của `{id}`. PHẢI = `qa_done`. Nếu khác → STOP với guide:
   - `analyzed` → `/evidence-qa --id {id}`
   - `qa_in_progress` / `qa_awaiting_external` → tiếp tục Q&A
   - `applied` → đã apply rồi; nếu cần re-apply → ingest evidence mới
   - `archived` → un-archive trước

## Bước 2 — Validator gate (I-4, I-5, V-08)

Đọc `qa/{id}/todo.json` và `qa/{id}/verified-facts.md`. Check tất cả:

| Check                                  | Pass condition                                              | Fail action                                  |
|----------------------------------------|-------------------------------------------------------------|----------------------------------------------|
| `verified-facts.md` exists + non-empty | File có ≥1 fact entry                                       | STOP                                         |
| Mọi P0/P1 không `awaiting_external`    | Lọc questions priority ∈ {P0,P1}, status ≠ `awaiting_external` | STOP, list pending external                |
| Mọi P0/P1 không `deferred` (hoặc có `--ignore-deferred`) | All P0/P1 status ∈ {answered, skipped} | STOP unless flag                          |
| Citations đầy đủ                       | Mọi fact có `Source:` + `Affects:`                          | STOP, list facts thiếu                       |
| Affects paths trong `{ws}/`            | Mọi `Affects:` path không escape `{ws}/`                    | STOP, vi phạm workspace isolation            |
| Contradictions resolved                | Mọi `[INVESTIGATE]` trong `02-contradiction.md` có fact cover | WARN, hỏi user confirm                     |

Nếu vi phạm → in error format trong [evidence-lifecycle.md](../../agents/pipeline/evidence-lifecycle.md) → STOP.

## Bước 3 — Optional: generate final-report

Nếu `--with-report`:
- Invoke logic của `/evidence-analyze --id {id} --prompt 10` (CORE 10).
- Output → `analysis/{id}/10-final-report.md`. Sẽ được attach vào prompt ở Bước 4.

## Bước 4 — Build augmented prompt

Đọc các source-of-truth file:
- `qa/{id}/verified-facts.md` (CHÍNH)
- `analysis/{id}/02-contradiction.md` (resolved positions)
- `analysis/{id}/08-knowledge-gaps.md` (note remaining gaps)
- `analysis/{id}/10-final-report.md` (nếu có)

Build prompt header:
```
EVIDENCE-DRIVEN UPDATE
Workspace : {active}
Evidence  : {id} ({label})
Sources   :
  - verified-facts: qa/{id}/verified-facts.md
  - contradictions: analysis/{id}/02-contradiction.md
  - gaps         : analysis/{id}/08-knowledge-gaps.md
  - report       : analysis/{id}/10-final-report.md  (optional)

Authority order:
  Contracts > Verified facts (this evidence) > Platform Patterns > Project Docs > Domain Knowledge

Apply via: /{contextd-update|contextd-rebase} workflow rules.
```

## Bước 5 — Invoke contextd-update / contextd-rebase logic (checkpointed)

Mỗi sub-step dưới đây map 1-1 với entry `steps[]` trong `checkpoint.json`. Sau mỗi sub-step finish → flush checkpoint (xem Bước 0.5). Resume sẽ đọc `current_step` + `resume_token` để skip.

### Affects-path router: edit vs create

Mỗi fact trong `verified-facts.md` có `Affects: {ws}/{path}`. Trước khi edit/create, classify theo path prefix + file existence:

| `Affects:` path pattern                                | File exists? | Action                                                             | Sub-step              |
|--------------------------------------------------------|--------------|--------------------------------------------------------------------|-----------------------|
| `platform/patterns/{name}.md`                          | yes          | EDIT (merge changes)                                               | `apply_edit_pattern`  |
| `platform/patterns/{name}.md`                          | no           | CREATE từ `templates/pattern.md` + append entry vào `patterns-index.md` | `apply_create_pattern`|
| `platform/contracts/{name}.md`                         | yes          | EDIT (extend rules / add registered types)                         | `apply_edit_contract` |
| `platform/contracts/{name}.md`                         | no           | CREATE — yêu cầu fact có đủ rule statement + format spec           | `apply_create_contract`|
| `projects/{p}/services/{s}.md`                         | yes          | EDIT (update Config Overrides, Flow, Failure Handling)             | `apply_edit_service`  |
| `projects/{p}/services/{s}.md`                         | no           | CREATE từ `templates/service.md` + append link vào `projects/{p}/knowledge-map.md` | `apply_create_service`|
| `decisions/{NNN}-{slug}.md`                            | no (luôn mới)| CREATE từ `templates/adr.md` (workspace-level ADR)                 | `apply_create_adr_ws` |
| `projects/{p}/decisions/{NNN}-{slug}.md`               | no (luôn mới)| CREATE từ `templates/adr.md` (project-level ADR)                   | `apply_create_adr_proj`|
| `patterns-index.md`                                    | yes          | EDIT (router auto-call sau create pattern; user fact direct cũng OK)| `apply_edit_index`    |
| `projects/{p}/knowledge-map.md`                        | yes          | EDIT (auto-call sau create service; hoặc fact direct)              | `apply_edit_kmap`     |

Rules:
- **CREATE actions** chỉ cho phép khi evidence cung cấp đủ data fill template tối thiểu (xem Bước 5 "Minimum data per CREATE action" dưới). Thiếu → STOP với hint "tạo follow-up question để fill, rồi resume".
- **ADR numbering**: `{NNN}` = next free number trong scope đó (workspace `{ws}/decisions/` hoặc project `{ws}/projects/{p}/decisions/`). Auto-resolve, KHÔNG để user gán tay.
- **Auto-side-effects sau CREATE pattern**: append row vào `patterns-index.md` Active table → tự động sinh sub-step `apply_edit_index`.
- **Auto-side-effects sau CREATE service**: append link vào project's `knowledge-map.md` → tự động sinh sub-step `apply_edit_kmap`.
- **Workspace isolation (I-2)**: tất cả `Affects:` paths PHẢI nằm trong `{ws}/`. Đã enforce ở Bước 2; router KHÔNG bypass.

### Minimum data per CREATE action

| Action | Required fields trong fact (hoặc analysis cite được) |
|--------|------------------------------------------------------|
| CREATE pattern | name, context, flow ≥ 3 steps, ≥ 1 default config key, ≥ 1 failure scenario |
| CREATE contract | name, rule statement (không mơ hồ), ≥ 2 observed examples, format spec |
| CREATE service | name, type, ≥ 1 entry-point, downstream summary, pattern reference (`Applies platform pattern: ...`) |
| CREATE ADR | title, context (1 đoạn), decision statement, ≥ 1 alternative considered |

Nếu thiếu → checkpoint mark sub-step `blocked`, `interrupted_reason = "create_missing_data: {field}"`. Generate follow-up question, push vào `qa/{id}/todo.json`. STOP với hint resume.

### Curator delegation vs inline mode

Default flow: edit wiki delegate qua `wiki-curator` subagent (theo contextd-update.md Bước 3).

**Fallback `--inline` flag** — khi curator subagent unavailable (vd test mode, subagent file bị xóa, môi trường không hỗ trợ Agent tool):

- Pass `--inline` → main agent edit trực tiếp file wiki (skip curator delegation).
- Khi inline:
  - Main agent BẮT BUỘC tự verify path sandbox trước MỖI Edit/Write call (giống Bước 4 Path Sandbox Verification của contextd-update.md).
  - Ghi `inline_apply: true` + lý do vào manifest.yaml.
  - Output `## Wiki Updated` table phải vẫn liệt kê absolute paths như curator format (audit trail không thay đổi).
- Default (không `--inline`): nếu curator unavailable → STOP với error `CURATOR UNAVAILABLE — chạy lại với --inline nếu chấp nhận inline edit (giảm safety layer 1)`.
- Lưu ý: inline mode mất layer "curator self-check" — chỉ còn main agent verify post-hoc. Acceptable cho test/CI nhưng KHÔNG khuyến nghị cho production wiki update thường ngày.

### Mode: `update`

Run [contextd-update.md](contextd-update.md) **Bước 1–5** với evidence là input chính. Map sub-steps:

| Sub-step                       | checkpoint `step` value                  | Resume granularity      |
|--------------------------------|------------------------------------------|-------------------------|
| Bước 1: classify changes (incl. router edit/create above) | `update_classify_changes`     | atomic                  |
| Bước 2-3: per-file edits / creates | `update_edit_files` (lặp per file/create action) | per file (`current_file`)|
| Bước 4: update knowledge-map   | `update_knowledge_map`                   | atomic                  |
| Bước 5: update patterns-index  | `update_patterns_index`                  | atomic                  |

### Mode: `rebase`

Run [contextd-rebase.md](contextd-rebase.md) **Bước 1–8** với rule bổ sung:
- Conflict code ≠ verified-facts → **verified-facts thắng**.
- Conflict wiki hiện tại ≠ verified-facts → wiki update theo facts.
- Conflict code ≠ wiki HIỆN TẠI và KHÔNG có fact cover → fall back behavior cũ.

Map sub-steps (chi tiết hơn vì rebase có nhiều khía cạnh per file):

| Sub-step contextd-rebase                                    | checkpoint `step` value          | Resume granularity         |
|---------------------------------------------------------|----------------------------------|----------------------------|
| Bước 1: list service docs + patterns + contracts        | `rebase_list_targets`            | atomic                     |
| Bước 2a: verify Config Overrides (per service file)     | `rebase_verify_config_overrides` | per file                   |
| Bước 2b: verify Flow                                    | `rebase_verify_flow`             | per file                   |
| Bước 2c: verify Pattern reference                       | `rebase_verify_pattern_ref`      | per file                   |
| Bước 2d: verify Failure handling                        | `rebase_verify_failure_handling` | per file                   |
| Bước 3a: verify Default Config                          | `rebase_verify_default_config`   | per pattern file           |
| Bước 3b: verify Used By table                           | `rebase_verify_used_by`          | per pattern file           |
| Bước 4a: verify Registered Types                        | `rebase_verify_registered_types` | per contract file          |
| Bước 4b: verify Format                                  | `rebase_verify_contract_format`  | per contract file          |
| Bước 5: verify knowledge-map.md                         | `rebase_verify_knowledge_map`    | per knowledge-map file     |
| Bước 6: verify patterns-index.md                        | `rebase_verify_patterns_index`   | atomic                     |
| Bước 7: verify workspace.md                             | `rebase_verify_workspace_md`     | atomic                     |

### Per file processing convention

Khi chạy 1 sub-step có `Resume granularity = per file`:

1. Build list `files_to_process` (vd tất cả services, patterns, contracts).
2. Set `step.files_processed = []`, `step.files_modified = []`, `step.current_file = files_to_process[0]`.
3. Loop:
   - Process file → quyết định modify/skip.
   - Update `files_processed[]`, append nếu modified.
   - Flush checkpoint mỗi 3 file (tránh write quá nhiều) HOẶC ngay sau mỗi file modified.
4. Khi xong list → mark `step.status = done`, `current_file = null`.

Nếu interrupted giữa loop → `current_file` giữ nguyên file đang xử lý → `--resume` bắt đầu lại từ file đó (re-process file đó, không skip vì có thể chưa flush sau modify).

### Inter-step blocker

Một sub-step có thể tạo follow-up question cần expert (vd Bước 2c phát hiện pattern conflict mà verified-facts chưa cover). Khi đó:
- Mark step `status = blocked`.
- Set `interrupted_reason = "expert_followup_required: q-XXX-followup"`.
- Set top-level `status = paused`.
- Generate follow-up question, push vào `qa/{id}/todo.json` + `pending-external.md` (nếu cần expert).
- STOP với hint: `/evidence-qa --resume --id {id}` để xử lý follow-up, sau đó `/evidence-apply --id {id} --mode {mode} --resume`.

## Bước 6 — Dry-run vs real

### `--dry-run`
- Print danh sách file sẽ sửa + diff dự kiến.
- KHÔNG ghi.
- KHÔNG transition state.
- In: `Dry-run done. Run without --dry-run to apply.`

### Real run
- Áp dụng các edit qua Edit tool.
- Track list file đã thực sự đổi.

## Bước 7 — Write manifest

> Checkpoint step: `write_manifest`.

Tạo `{ws}/evidence/applied/{id}/manifest.yaml` từ template `templates/evidence-manifest.yaml`:
- `evid_id`, `workspace`, `applied_at`, `applied_by`, `mode`
- `inputs` (paths đã dùng)
- `target_files[]` với `sections_changed` + `change_summary` (chỉ cho EDIT actions)
- `created_files[]` với `template_used` + `populated_from_facts: [F-XXX, ...]` (chỉ cho CREATE actions; áp dụng khi router classify thành CREATE — common cho code evidence ingest lần đầu)
- `citations[]` map mỗi target/created → q-id evidence
- `validator{}` results
- `deferred_questions[]` (P2/P3 deferred OK)
- `unresolved_blockers: []` (phải rỗng vì đã pass validator)

Ghi `applied/{id}/diff-summary.md` theo format Bước 8 báo cáo của [contextd-rebase.md](contextd-rebase.md):
```markdown
## Apply Report — workspace `{active}` — evidence `{id}` — {date}

### Mode
{update|rebase}

### Updated
- {file}: {what changed} (citation: q-XXX)

### Skipped (no actionable fact)
- ...

### Warnings
- ...
```

## Bước 8 — Transition state

> Checkpoint step: `transition_state`. Sau khi finish: top-level `status = completed`, `completed_at = now`, `current_step = null`.

1. Update `_index.md`: state → `applied`, `applied_to` = comma-separated target files (relative `{ws}/`).
2. Update `todo.json#state = applied`.
3. Update `checkpoint.json`: `status = completed`, `completed_at`. KHÔNG xóa file — giữ làm audit (cùng folder với `manifest.yaml`).

## Bước 9 — Confirm

In:
```
✅ Evidence applied — {id}
   Workspace : {active}
   Mode      : {update|rebase}
   Files     : {N} updated
   Citations : every change has q-id evidence trace
   Manifest  : {ws}/evidence/applied/{id}/manifest.yaml

Wiki diff:
  {summary of files changed}

Optional next:
  /evidence-archive --id {id}    → move to archive after some time
```

---

## Cross-workspace guard (I-2)

Triple-checked tại Bước 0, Bước 1.2, và mỗi `Affects:` path ở Bước 2. Vi phạm bất kỳ chỗ nào → STOP với:
```
CROSS-WORKSPACE VIOLATION
Evidence {id} ingested in `{X}`. Active = `{Y}`.
Refusing to apply. Switch via: /switch-workspace {X}
```

## Common errors

| Error                                       | Fix                                                            |
|---------------------------------------------|----------------------------------------------------------------|
| State ≠ qa_done                             | Resume Q&A flow                                                |
| P0/P1 awaiting_external                     | `/evidence-qa --resume --id {id}` after expert reply           |
| P0/P1 deferred                              | Resume Q&A or pass `--ignore-deferred` (not recommended)       |
| `Affects:` path escapes `{ws}/`             | Edit `verified-facts.md` to fix path; rerun                    |
| Contradiction `[INVESTIGATE]` not resolved  | Add follow-up question in Q&A or accept warning                |
| Workspace lock                              | Switch back to ingest workspace                                |
