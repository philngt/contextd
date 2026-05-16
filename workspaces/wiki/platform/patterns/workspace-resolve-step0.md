# Pattern: workspace-resolve-step0

## Context

Engine-level invariant pattern: mọi slash command WIKI-AWARE phải resolve active workspace trước khi làm bất cứ gì khác. Nếu không resolve, command có thể đọc/ghi sai workspace (cross-pollution knowledge giữa các sandbox độc lập).

Pattern này lặp lại 15/15 commands trong `.claude/commands/` ngoại trừ index README. Coverage near-universal → engine-level invariant.

## Flow

```
<cwd>
  ↓ scan up parent dirs
.claude/wiki.json found
  ↓ read JSON
workspace + wiki_root
  ↓ resolve wiki_root rule
{effective_wiki_root}
  ↓
{ws} = {effective_wiki_root}/workspaces/{workspace}/
  ↓ validate workspace.md exists
PROCEED
```

1. **Find `.claude/wiki.json`**: từ `<cwd>` đi lên parent cho tới khi gặp file. Lưu `wiki_json_dir`.
2. **Read + resolve `wiki_root`** theo `agents/system-prompt.md` Resolution Rule:
   - Absolute path → dùng nguyên.
   - Relative (`"."`, `"./..."`) → resolve relative TỚI `project_root` (= parent của `.claude/`), KHÔNG phải `.claude/` literal, KHÔNG phải cwd.
   - `null`/empty → fallback `~/.claude/wiki-global.json#wiki_root`.
3. **STOP** nếu file thiếu hoặc `.workspace` rỗng → guide user `/switch-workspace` hoặc `/wiki-setup`.
4. **Set context**: `workspace_active = .workspace`, `effective_wiki_root = <resolved absolute>`, `{ws} = {effective_wiki_root}/workspaces/{workspace_active}/`.
5. **Validate**: `{ws}/workspace.md` tồn tại. Nếu không → workspace bị broken, STOP.

On failure: STOP với hint specific (file thiếu / workspace empty / workspace.md missing).

## Default Config

```yaml
# Pattern là pure invariant — no config keys. Behavior mandated:
hard_stop_on_missing_wiki_json: true
hard_stop_on_empty_workspace_field: true
fallback_to_global_when_wiki_root_null: true
```

## Failure Strategy

| Scenario | Action |
|----------|--------|
| `.claude/wiki.json` not found | STOP, hint `/wiki-setup` |
| `.workspace` field rỗng/null | STOP, hint `/switch-workspace {name}` |
| `wiki_root: "."` resolved sai (vd resolved tới `.claude/` literal) | STOP, hint check Resolution Rule |
| `~/.claude/wiki-global.json` thiếu khi `wiki_root` null | STOP, hint setup global config |
| `{ws}/workspace.md` missing | STOP, workspace broken — recreate hoặc switch |

## Implementation Rules

- KHÔNG đọc/copy knowledge từ workspace khác `{workspace_active}` (engine invariant — workspace sandboxing).
- KHÔNG guess workspace từ codebase markers — explicit `.claude/wiki.json` là source of truth.
- KHÔNG bypass Bước 0 cho commands "fast" hay "simple" — invariant universal.
- Workspace override KHÔNG apply cho pattern này (engine-level invariant).

## Override Points

_(none — pattern là pure invariant, không có override points)_

## Anti-patterns

- ❌ Use cwd-relative wiki_root resolution (vd `"./workspaces"` resolved tới `<cwd>/workspaces` thay vì `<wiki_json_dir>/workspaces`).
- ❌ Skip workspace.md existence check (cho phép broken workspace lọt qua).
- ❌ Cache workspace resolution across commands without re-validation (workspace có thể đổi giữa runs).

## Used By

> 15+ commands engine implement Bước 0 này. Khi `/evidence-apply` tạo service mới, dòng link tương ứng được auto-append.

- All commands trong `.claude/commands/` ngoại trừ `README.md` (index).
- Engine spec: `agents/system-prompt.md` (Resolution Rule).

## Related

- Engine spec: `agents/system-prompt.md` (`wiki_root` Resolution Rule)
- Contract: `../contracts/evidence-state-machine-transitions.md` (workspace lock invariant I-2)
- Source: q-001, evidence `2026-05-08-engine-bootstrap-wiki-template`
