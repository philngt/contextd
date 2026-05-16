# Pattern: evidence-state-machine

> PAIR pattern của contract `../contracts/evidence-state-machine-transitions.md`. Pattern describes implementation skeleton; contract describes invariant rules.

## Context

Evidence pipeline (ingest → analyze → qa → apply) cần state tracking để:
- Resume sau interruption (Ctrl+C, crash, expert pause).
- Validate prerequisite trước transition (vd KHÔNG được apply trước khi qa_done).
- Audit trail (mỗi evidence có lifecycle traceable).

State machine reused mọi evidence command — universal pattern.

## Flow

```
(none)                                   ← evidence chưa tồn tại
  ↓ /evidence-ingest, /code-analyze, /obsidian-ingest
ingested                                 ← raw.md + source.yaml written
  ↓ /evidence-analyze (CORE set complete)
analyzed                                 ← analysis/{id}/*.md written
  ↓ /evidence-qa
qa_in_progress                           ← user trong batch loop
  ↕ (defer/resume)
qa_awaiting_external                     ← chờ expert reply
  ↓ /evidence-qa (verified-facts.md done)
qa_done                                  ← ready cho apply
  ↓ /evidence-apply
applied                                  ← wiki updated
  ↓ manual (after retention period)
archived                                 ← history only
```

1. **Storage**: state lưu duy nhất ở `{ws}/evidence/_index.md` Active table — single source of truth.
2. **Transition trigger**: command-specific (xem contract C-005 ownership table). Mỗi command BẮT BUỘC validate precondition trước transition.
3. **Precondition check**: vd `analyzed → qa_in_progress` cần đủ CORE set (text: 4 files; code variant=code: 6 files; code variant=agentic-engine: 6 files).
4. **Resume support**: mỗi command-cụ thể (vd `/evidence-apply`) ghi `checkpoint.json` để resume sau crash. State machine ở `_index.md` reflect outermost stage; checkpoint.json reflect intra-stage progress.
5. **Workspace lock (I-2)**: state transition CHỈ thực hiện khi active workspace = `source.yaml#workspace_at_ingest`.

On failure: precondition fail → STOP với hint correct prerequisite command. KHÔNG transition.

## Default Config

```yaml
# State machine definition
states: [ingested, analyzed, qa_in_progress, qa_awaiting_external, qa_done, applied, archived]
storage_file: "{ws}/evidence/_index.md"      # SINGLE source of truth
storage_format: markdown_table               # Active table + Archived table

# Transition validation
no_skip_dag: true                            # cấm skip stage
reverse_transitions_disabled: true           # cấm rollback (re-apply yêu cầu evidence mới)
manual_archive_marker: "(manual)"            # mark trên row trong _index.md nếu user edit thủ công

# Resume
checkpoint_file: "{ws}/evidence/applied/{id}/checkpoint.json"   # cho /evidence-apply
todo_file: "{ws}/evidence/qa/{id}/todo.json"                    # cho /evidence-qa
```

## Failure Strategy

| Scenario | Action |
|----------|--------|
| Command try transition outside ownership | STOP với error format `evidence-lifecycle.md` |
| Precondition không đủ (vd CORE set incomplete) | STOP, KHÔNG transition |
| Workspace lock mismatch (active ≠ workspace_at_ingest) | STOP với cross-workspace violation |
| Skip stage attempt (vd ingested → applied direct) | STOP, hint correct prerequisite |
| Reverse transition (vd applied → qa_done) | STOP, hint "re-apply yêu cầu evidence mới" |
| Manual edit `_index.md` không mark `(manual)` | Audit log warning |

## Implementation Rules

- State trong `_index.md` Active table = single source of truth. KHÔNG duplicate state ở `source.yaml`.
- Mỗi command BẮT BUỘC update `last_updated` cùng dòng khi transition.
- Manual edit `_index.md` PHẢI mark `(manual)` để audit.
- Re-apply yêu cầu ingest evidence mới (KHÔNG sửa state cũ về qa_done).
- `qa_awaiting_external` → `qa_in_progress` reversible (defer ↔ resume).

## Override Points

_(none — state machine engine-level invariant. Workspace KHÔNG được thêm/đổi states.)_

## Anti-patterns

- ❌ Lưu state ở `source.yaml#state` — duplicate source of truth.
- ❌ Skip precondition check để "fast-track" apply — defeat state machine purpose.
- ❌ Auto-archive sau N ngày — archived transition phải manual (I-3 retention).
- ❌ Re-apply by editing state qa_done → applied → qa_done — phải ingest mới.

## Used By

- `/evidence-ingest`, `/code-analyze`, `/obsidian-ingest` — owns transition `(none) → ingested`
- `/evidence-analyze` Bước 6 — owns `ingested → analyzed`
- `/evidence-qa` — owns `analyzed → qa_in_progress → qa_done`
- `/evidence-apply` Bước 8 — owns `qa_done → applied`
- Templates: `templates/evidence-index.md` (state legend + transition diagram)
- Engine spec: `agents/pipeline/evidence-lifecycle.md`

## Related

- Contract: `../contracts/evidence-state-machine-transitions.md` (PAIR — invariant rules)
- Contract: `../contracts/evidence-file-layout.md` (`_index.md` location)
- Source: q-005, evidence `2026-05-08-engine-bootstrap-wiki-template`
