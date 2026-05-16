# Contract: evidence-state-machine-transitions

> PAIR contract của pattern `../patterns/evidence-state-machine.md`. Pattern describes implementation skeleton; contract describes invariant rules.

## Rule

Evidence state machine là DAG chặt với 7 states + transition ownership. KHÔNG có command nào được transition ngoài bảng dưới.

```
ingested → analyzed → qa_in_progress ⇄ qa_awaiting_external → qa_done → applied → archived
```

## Transition ownership

| Transition | Owning command | Precondition |
|------------|----------------|--------------|
| `(none) → ingested` | `/evidence-ingest`, `/code-analyze`, `/obsidian-ingest` | source.yaml valid + raw.{ext} written + sha256 dedup pass |
| `ingested → analyzed` | `/evidence-analyze` | đủ CORE set (text: 4 files; code variant=code: 6 files; code variant=agentic-engine: 6 files) |
| `analyzed → qa_in_progress` | `/evidence-qa` | recommendations.md generated (nếu source_type=code) HOẶC todo.json populated |
| `qa_in_progress ⇄ qa_awaiting_external` | `/evidence-qa` | có ≥ 1 P0/P1 deferred to expert |
| `qa_in_progress → qa_done` | `/evidence-qa` | verified-facts.md complete + mọi P0/P1 không awaiting_external |
| `qa_done → applied` | `/evidence-apply` | dry-run review pass + manifest write success |
| `applied → archived` | manual (mark `(manual)` row) | retention period passed |

## Invariants

- **No skip**: KHÔNG được apply trước khi qa_done. KHÔNG được analyzed trực tiếp từ (none).
- **`_index.md` là single source of truth** — KHÔNG lưu state ở `source.yaml` hay file khác. Manual edit phải mark `(manual)`.
- **Workspace lock (I-2)**: state transition CHỈ thực hiện khi active workspace = `source.yaml#workspace_at_ingest`. Cross-workspace = STOP.
- **Reverse transitions cấm**: vd `applied → qa_done` invalid. Re-apply yêu cầu ingest evidence mới.

## Observed evidence

- ✅ State legend: `(templates/evidence-index.md:L23-L36)`
- ✅ Diagram: `(templates/evidence-index.md:L33-L37)`
- ✅ Workspace `wiki` `_index.md`: `(workspaces/wiki/evidence/_index.md:L21-L34)`
- ✅ `/evidence-analyze` Bước 6: `(.claude/commands/evidence-analyze.md)` — count check before transition
- ✅ Reference engine doc: `(agents/pipeline/evidence-lifecycle.md:L1)`

## Counter-examples

_(none detected — model consistent across docs)_

## Validator behavior

- Command try transition outside ownership → STOP với error format trong `evidence-lifecycle.md`.
- State skip detected → STOP, hint correct prerequisite command.
- Workspace mismatch → STOP với cross-workspace violation message.

## Related

- Pattern: `../patterns/evidence-state-machine.md` (PAIR — implementation skeleton)
- Contract: `evid-id-format.md` (state machine consumes evid-id as row key)
- Contract: `evidence-file-layout.md` (`_index.md` location)
- Source: q-005, evidence `2026-05-08-engine-bootstrap-wiki-template`
