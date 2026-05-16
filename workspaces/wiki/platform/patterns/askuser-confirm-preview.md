# Pattern: askuser-confirm-preview

## Context

Apply cho mọi command có **side effects filesystem** (tạo evidence, edit wiki, scaffold workspace). User cần thấy preview của những gì sắp xảy ra TRƯỚC khi command commit irreversible state.

Pattern UX best practice: 4+ commands explicit follow (`/code-analyze`, `/evidence-ingest`, `/wiki-setup`, `/new-workspace`).

## Flow

```
Resolve inputs
  ↓
Build preview block (workspace + paths + key fields)
  ↓
List "Sẽ tạo:" — explicit file paths
  ↓
AskUserQuestion 3 options
  ↓        ↓        ↓
Continue  Edit   Cancel
  ↓        ↓        ↓
EXECUTE  back    STOP
         to step
         resolve
```

1. **Build preview block** — list MỌI field user cần verify: workspace, scope, evid-id, label, target paths, branch/sha (nếu code), variant (nếu áp dụng).
2. **List "Sẽ tạo:"** — explicit absolute paths của files sẽ thay đổi.
3. **AskUserQuestion** với 3 options điển hình:
   - `{primary action} (Recommended)` → continue
   - `edit-{detail}` → quay lại bước resolve
   - `cancel` → STOP
4. **Wait user**. Branch theo answer.
5. **On Continue**: execute irreversible action.

On failure: cancel BẮT BUỘC luôn có mặt — user luôn có exit lane.

## Default Config

```yaml
# Conventional defaults
preview_block_format: ascii_table_or_indented_list
ask_user_options_count: 3                     # primary + edit + cancel
recommended_marker: "(Recommended)" suffix on primary option
edit_back_to_step: "resolve_inputs"           # always loop to resolve
```

## Failure Strategy

| Scenario | Action |
|----------|--------|
| User chooses Cancel | STOP cleanly, no state change |
| User chooses Edit | Loop back to resolve step (do NOT execute side effects yet) |
| AskUserQuestion timeout / no response | Treat as Cancel |
| Preview missing critical field | Re-prompt với reminder, không execute |

## Implementation Rules

- Preview PHẢI hiển thị mọi "non-trivial-to-recompute" field — workspace lock, scope, file paths sẽ ghi.
- Cancel option BẮT BUỘC có mặt — không có lock-in path.
- Edit option đưa user back đến bước trước, KHÔNG qua step intermediate (skip).
- Sau confirm = irreversible (file sẽ được tạo) → preview là last line of defense.
- Preview KHÔNG được show secrets even nếu user pass `--allow-configs` — preview là user-facing display, secrets hide as `<REDACTED>` nếu lộ.

## Override Points

- `preview_block_format` — workspace có thể customize style (table/list/JSON).
- Số option có thể tăng (vd `/code-analyze` Bước 3 dùng 3 options: yes/edit-scope/cancel).

## Anti-patterns

- ❌ Skip preview cho command "trivial" — every irreversible op cần confirm.
- ❌ Default to Yes (auto-confirm) — defeat purpose of pattern.
- ❌ Hide cancel option behind "Other" → cancel must be top-level.
- ❌ Preview after side effect (vd "Đã tạo file. Tiếp tục?") — too late.

## Used By

- `/code-analyze` Bước 3 `(.claude/commands/code-analyze.md:L106-L182)`
- `/evidence-ingest` (preview confirm trước khi commit ingest)
- `/wiki-setup` (preview detected components trước khi tạo wiki.json)
- `/new-workspace` (preview workspace skeleton trước khi scaffold)

## Related

- Pattern: `secrets-blocklist-gate.md` (config guard — uses AskUser for opt-in per-file)
- Source: q-002, evidence `2026-05-08-engine-bootstrap-wiki-template`
