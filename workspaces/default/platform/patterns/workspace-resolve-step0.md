# Pattern: workspace-resolve-step0

## Context

Engine-level invariant pattern: mọi slash command WIKI-AWARE phải resolve active workspace trước khi làm bất cứ gì khác. Nếu không resolve, command có thể đọc/ghi sai workspace (cross-pollution knowledge giữa các sandbox độc lập).

Pattern này lặp lại 15/15 commands trong `.claude/commands/` ngoại trừ index README. Coverage near-universal → engine-level invariant.

## Flow

```
<cwd>
  ↓ scan up parent dirs
.contextd/config.json found (or legacy adapter)
  ↓ read JSON
workspace + knowledge_root
  ↓ resolve knowledge_root rule
{effective_knowledge_root}
  ↓
{ws} = {effective_knowledge_root}/workspaces/{workspace}/
  ↓ validate workspace.md exists
PROCEED
```

1. **Find `.contextd/config.json`**: từ `<cwd>` đi lên parent cho tới khi gặp file. Nếu thiếu, fallback legacy `.claude/wiki.json`, rồi `.Codex/wiki.json`. Lưu `config_dir`.
2. **Read + resolve `knowledge_root`** (`wiki_root` legacy alias) theo `agents/system-prompt.md` Resolution Rule:
   - Absolute path → dùng nguyên.
   - Relative (`"."`, `"./..."`) → resolve relative TỚI `project_root` (= parent của config dir), KHÔNG phải cwd.
   - `null`/empty → fallback global `.contextd`, rồi legacy globals.
3. **STOP** nếu config thiếu hoặc `.workspace` rỗng → guide user `contextd migrate-config`, `/switch-workspace`, hoặc `/contextd-setup`.
4. **Set context**: `workspace_active = .workspace`, `effective_knowledge_root = <resolved absolute>`, `{ws} = {effective_knowledge_root}/workspaces/{workspace_active}/`.
5. **Validate**: `{ws}/workspace.md` tồn tại. Nếu không → workspace bị broken, STOP.

On failure: STOP với hint specific (file thiếu / workspace empty / workspace.md missing).

## Default Config

```yaml
# Pattern là pure invariant — no config keys. Behavior mandated:
hard_stop_on_missing_config: true
hard_stop_on_empty_workspace_field: true
fallback_to_global_when_knowledge_root_null: true
```

## Failure Strategy

| Scenario | Action |
|----------|--------|
| `.contextd/config.json` and legacy adapters not found | STOP, hint `contextd migrate-config` hoặc `/contextd-setup` |
| `.workspace` field rỗng/null | STOP, hint `/switch-workspace {name}` |
| `knowledge_root: "."` resolved sai | STOP, hint check Resolution Rule |
| Global config thiếu khi root null | STOP, hint setup global config |
| `{ws}/workspace.md` missing | STOP, workspace broken — recreate hoặc switch |

## Implementation Rules

- KHÔNG đọc/copy knowledge từ workspace khác `{workspace_active}` (engine invariant — workspace sandboxing).
- KHÔNG guess workspace từ codebase markers — explicit `.contextd/config.json` hoặc legacy adapter là source of truth.
- KHÔNG bypass Bước 0 cho commands "fast" hay "simple" — invariant universal.
- Workspace override KHÔNG apply cho pattern này (engine-level invariant).

## Override Points

_(none — pattern là pure invariant, không có override points)_

## Anti-patterns

- ❌ Use cwd-relative knowledge_root resolution (vd `"./workspaces"` resolved tới `<cwd>/workspaces` thay vì project root).
- ❌ Skip workspace.md existence check (cho phép broken workspace lọt qua).
- ❌ Cache workspace resolution across commands without re-validation (workspace có thể đổi giữa runs).

## Used By

> 15+ commands engine implement Bước 0 này. Khi `/evidence-apply` tạo service mới, dòng link tương ứng được auto-append.

- All commands trong `.claude/commands/` ngoại trừ `README.md` (index).
- Engine spec: `agents/system-prompt.md` (Resolution Rule).

## Related

- Engine spec: `agents/system-prompt.md` (`knowledge_root` Resolution Rule)
- Contract: `../contracts/evidence-state-machine-transitions.md` (workspace lock invariant I-2)
- Source: q-001, evidence `2026-05-08-engine-bootstrap-wiki-template`
