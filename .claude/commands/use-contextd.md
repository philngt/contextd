# /use-contextd — Build Runtime-Neutral Task Context

Chạy command này trước khi viết code cần workspace knowledge. Trong migration window slash command vẫn sống dưới `.claude/commands`, nhưng **canonical engine** là CLI `contextd context`.

## Canonical Flow

1. Resolve workspace bằng shared resolver:
   `.contextd/config.json` → legacy `.claude/wiki.json` → legacy `.Codex/wiki.json` → `~/.contextd/config.json` → legacy globals.
2. Chạy:

```bash
contextd context "{user_task}" --format json
```

3. CLI materialize các artifact dưới project hiện tại:
   - `.contextd/context/current-task.json` — source of truth
   - `.contextd/context/current-task.md` — human/adapter render từ JSON
   - `.contextd/context/packs/{packKey}.md` — deterministic static context pack
4. Main agent đọc `.contextd/context/current-task.json` và chỉ dùng `referenced_docs`, `gaps`, `warnings`, `contextPack`, `retrieval_policy`, `source_hashes` từ artifact đó.

## Required Checks

- Nếu CLI báo thiếu config/workspace → STOP, hướng dẫn chạy `contextd migrate-config` hoặc `/contextd-setup`.
- Nếu `gaps[]` có blocking gap về contract/pattern/domain workflow → STOP, báo user cập nhật knowledge trước.
- Nếu `warnings[]` có legacy config conflict → dùng `.contextd/config.json` vì canonical config thắng.
- Không đọc knowledge ngoài active workspace, trừ engine docs và active pack baseline docs đã được artifact reference.

## Builder Output

Main agent trả lời theo format trong `agents/pipeline/prompt-template.md`:

```md
## Understanding
## Knowledge Mapping
## Design
## Implementation
## Edge Cases
## Assumptions
```

Mọi quyết định kỹ thuật phải reference được từ `referenced_docs` trong `current-task.json`. Nếu cần thông tin ngoài artifact → ghi là assumption hoặc knowledge gap, không đoán.

## Advisory Search

`contextd find "<query>"` chỉ là discovery/advisory. Kết quả search không được override contracts/patterns deterministic trong `current-task.json`.

## Legacy Notes

Các subagent cũ (`contextd-planner`, `contextd-context-selector`, `contextd-reviewer`) chỉ còn là compatibility/migration docs. Runtime adapters mới nên consume JSON artifact thay vì tự invent context rules từ markdown.
