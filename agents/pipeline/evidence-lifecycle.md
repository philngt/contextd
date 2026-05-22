# Evidence State Rules

Reference cho `/evidence-{ingest,analyze,qa,apply,archive}`. State machine, transitions, invariants.

> **Note**: `/evidence-archive` is **planned — not yet implemented**. The `applied → archived` transition is part of the designed state machine but no command file exists yet under `.claude/commands/`. Until implemented, archival is manual (move folder to `archive/` by hand).

---

## State machine

```
                 /evidence-analyze              /evidence-qa
   ingested ───────────────────▶ analyzed ──────────────────▶ qa_in_progress
                                                                    │
                                                                    │ (all P0/P1 answered|skipped|deferred,
                                                                    │  no awaiting_external)
                                                                    ▼
                                              ┌─────────────── qa_done
                                              │     /evidence-apply       │
                                              │                           │
                       (any P0/P1 marked      │                           │
                        defer-to-expert)      │                           ▼
                                              │                       applied
                                              ▼                           │
                                    qa_awaiting_external                  │ /evidence-archive
                                              │                           ▼
                                              │ /evidence-qa --resume  archived
                                              │ (all external resolved)
                                              ▼
                                          qa_in_progress
```

State authoritative tại `{ws}/evidence/_index.md`.
Mirror chi tiết tại `{ws}/evidence/qa/{evid-id}/todo.json`.

---

## Transitions

| Transition                              | Actor                  | Pre-condition                                                 | Post-condition                                          |
|-----------------------------------------|------------------------|---------------------------------------------------------------|---------------------------------------------------------|
| `(none) → ingested`                     | `/evidence-ingest`     | Workspace check pass; sha256 unique                           | `sources/{id}/source.yaml` + `raw.{ext}` written        |
| `ingested → analyzed`                   | `/evidence-analyze`    | All 4 CORE files (01,02,04,08) exist + non-empty              | `_index.md` state updated                               |
| `analyzed → qa_in_progress`             | `/evidence-qa`         | `todo.json` created; batch 1 dispatched                       | state row updated                                       |
| `qa_in_progress → qa_awaiting_external` | `/evidence-qa`         | ≥1 question marked `awaiting_external`                        | `pending-external.md` generated                         |
| `qa_awaiting_external → qa_in_progress` | `/evidence-qa --resume`| ≥1 external resolved BUT others still pending                 | answer appended to `batch-N-answers.md`                 |
| `qa_in_progress → qa_done`              | `/evidence-qa`         | All P0/P1 status ∈ {answered, skipped, deferred}; NO awaiting_external | `verified-facts.md` written                       |
| `qa_awaiting_external → qa_done`        | `/evidence-qa --resume`| All external resolved + condition above                       | `verified-facts.md` written                             |
| `qa_done → applied`                     | `/evidence-apply`      | Validator gates pass; wiki edits done                         | `applied/{id}/manifest.yaml` written                    |
| `applied → archived`                    | `/evidence-archive` *(planned)* | User confirm OR `--older-than` policy                         | folder moved to `archive/`                              |

---

## Invariants (validator MUST enforce)

### I-1. Immutable sources
Sau khi state ≠ `ingested`:
- `sources/{id}/source.yaml` — read-only.
- `sources/{id}/raw.{ext}` — read-only.
- `sources/{id}/raw.normalized.md` — read-only.

Nếu cần re-ingest → STOP, yêu cầu user `/evidence-ingest` mới (evid-id mới).

**Note source_type=code**: `raw.md` là snapshot METADATA tại `git_sha` của HEAD lúc ingest. Codebase tiến hóa sau đó KHÔNG ảnh hưởng evidence cũ — `raw.md` đông cứng cùng `git_sha` để analysis cite reproducible. Muốn snapshot phiên bản mới → chạy `/code-analyze` lần nữa, ra evid-id mới.

### I-2. Workspace lock
`source.yaml#workspace_at_ingest` MUST khớp `<cwd>/.claude/wiki.json.workspace` (fallback `~/.claude/wiki-global.json.default_workspace`) tại mọi transition sau ingest.
Vi phạm = STOP với error:
```
CROSS-WORKSPACE VIOLATION
Evidence {evid-id} ingested in workspace `{X}`.
Current active workspace: `{Y}`.
Refusing to {action}. Switch back via /switch-workspace {X}.
```

### I-3. State monotonicity
Backward transitions chỉ cho phép:
- `qa_done → qa_in_progress` (user re-opens question)
- `qa_awaiting_external → qa_in_progress` (resume flow)

KHÔNG cho phép: `applied → qa_*` (sau khi apply, evidence "đông cứng"; nếu cần sửa wiki tiếp → ingest evidence mới).

### I-4. Apply gates
`/evidence-apply` STOP nếu:
- State ≠ `qa_done`
- Workspace check fail (I-2)
- Bất kỳ P0/P1 question nào status = `awaiting_external` (P0/P1 deferred cũng STOP nếu user không pass `--ignore-deferred`)
- `verified-facts.md` không tồn tại hoặc empty
- Một trong các target file trong `verified-facts.md#Affects` trỏ ra ngoài `{ws}/`
- Mâu thuẫn chưa giải quyết trong `02-contradiction.md` (status `INVESTIGATE` mà không có F-XXX trong verified-facts cover)

P2/P3 deferred → warning, không STOP.

### I-5. Citation requirement
Mọi entry trong `verified-facts.md` PHẢI có:
- `Source:` cite question id + answerer
- `Affects:` cite file wiki path (relative `{ws}/`)

Validator reject nếu thiếu.

### I-6. Append-only logs
- `batch-{n}-answers.md` — append-only. Update = thêm entry mới với `supersedes:` tag.
- `external-answers.md` — append-only.
- `_index.md` — chỉ command tự động cập nhật. User edit thủ công phải đánh `(manual)` ở cột `state`.

### I-7. Pending-external lifecycle
- Auto-created khi có ≥1 `awaiting_external`.
- Auto-deleted khi tất cả entry resolved (move sang `qa/{id}/external-answers.md`).
- KHÔNG được delete tay khi còn entry chưa resolved.

### I-8. Apply checkpoint lifecycle
- `applied/{id}/checkpoint.json` được ghi incrementally bởi `/evidence-apply`. Mỗi sub-step finish → flush ngay.
- File giữ vĩnh viễn cùng `manifest.yaml` làm audit trail (KHÔNG xóa khi `status = completed`).
- `--resume` invariants:
  - `evid_id` + `workspace` + `mode` trong checkpoint PHẢI khớp lệnh resume. Mismatch → STOP.
  - Step `done` trong `steps[]` KHÔNG re-execute.
  - Step `in_progress` re-execute từ `current_file` (nếu per-file granularity) hoặc từ đầu step (atomic).
  - Step `blocked` PHẢI có `interrupted_reason`. Resume sẽ check blocker đã giải quyết chưa (vd follow-up question đã answered).
- Nếu user chạy command MỚI (không `--resume`) khi đã có checkpoint `status ≠ completed` → MUST hỏi qua AskUserQuestion ["Resume", "Restart", "Cancel"]. Restart phải backup file cũ thành `checkpoint-{ts}.json.bak`.
- Concurrent invocation: 2 lần `/evidence-apply` cho cùng `evid-id` chạy song song KHÔNG được phép. Detect bằng cách check `last_updated_at` trong file ≤ 30s + `status = in_progress` → STOP với "another apply may be running, wait or check `--status`".

### I-8.1. Mid-step concurrency check (session_id)

I-8 chỉ check **tại bắt đầu** apply. Race window vẫn mở giữa các sub-step nếu Session B start sau 30s `last_updated_at` thresh của A. I-8.1 đóng window này:

- **Tại start**: command sinh `session_id = uuid.uuid4()` (string UUID4). Ghi vào checkpoint cùng với `pid` + `started_at` (xem `templates/evidence-apply-checkpoint.json`).
- **Trước MỖI sub-step flush**: re-read `checkpoint.json` ngay trước khi ghi. Nếu `checkpoint.session_id` ≠ session_id của process hiện tại → STOP:
  ```
  CHECKPOINT HIJACKED
  Evidence: {evid-id}
  My session: {my_session_id} (pid {my_pid})
  Checkpoint owned by: {other_session_id} (pid {other_pid}, since {other_started_at})
  Aborting to prevent data loss. Resolve manually:
    - Inspect both sessions' state.
    - Keep one checkpoint, delete the other, then /evidence-apply --id {id} --resume.
  ```
- **Backward compat**: checkpoint thiếu `session_id` (legacy file) → treat as legacy, log warn "checkpoint format legacy, upgrading on next flush" và inject `session_id` của process hiện tại lúc flush kế tiếp.
- **Filesystem-level protection**: dùng `with_advisory_lock` từ [`scripts/lib/atomic_write.py`](../../scripts/lib/atomic_write.py) cho mỗi read-modify-write của `checkpoint.json` để chặn race trong cùng tick.

---

## Validator checks (run at each transition)

| Check ID | When                   | Logic                                                                          |
|----------|------------------------|--------------------------------------------------------------------------------|
| V-01     | Before ingest          | sha256 không trùng với entry trong `_index.md`                                 |
| V-02     | After ingest           | I-1 setup (file ACL hoặc convention check); nếu `source_type=code` single-repo → `git_sha` non-null + length 40 (hoặc prefix `unmanaged-`); `code_scope` non-empty. Bundle mode: mỗi entry trong `code_repos[]` phải có `git_sha` non-null + length 40 (hoặc `unmanaged-` prefix); `code_repos` list non-empty |
| V-03     | Before analyze         | State = `ingested`; raw files exist                                            |
| V-04     | After analyze          | 4 CORE files non-empty; mỗi file có ≥1 entry với citation                      |
| V-05     | Before qa start        | State = `analyzed`; `04-questions.md` parseable                                |
| V-06     | After each qa batch    | I-2; `todo.json` valid JSON; new questions have q-id                           |
| V-07     | Before pending-external write | I-7 lifecycle check                                                     |
| V-08     | Before apply           | I-2, I-4, I-5 (full set)                                                       |
| V-09     | After apply            | manifest.yaml has citation cho mỗi target_file changed                         |
| V-10     | Before archive         | State = `applied`                                                              |
| V-11     | Before each apply sub-step | Checkpoint flushed (≤ 2s ago); `--resume` mismatch check (I-8); session_id match (I-8.1) |
| V-12     | After each apply sub-step  | Step entry status updated; `last_updated_at` refreshed; `resume_token` set  |

---

## Error format

Khi vi phạm invariant, command STOP và in:
```
EVIDENCE STATE ERROR
Invariant: I-{N} ({title})
Evidence: {evid-id}
Workspace: {active}
Detail: {what went wrong}
Fix: {actionable next step}
```

Không silent skip. Không workaround.
