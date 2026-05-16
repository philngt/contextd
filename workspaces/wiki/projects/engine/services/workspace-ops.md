# Service: workspace-ops

## Purpose

Bootstrap + navigate workspace state cho codebase đang dùng wiki engine. 5 commands tạo, validate, switch giữa workspaces.

## Input

User invocation. Mỗi command có signature riêng:
- `/wiki-setup` — interactive (no args)
- `/wiki-detect` — no args
- `/switch-workspace {name}` — positional
- `/new-workspace {name}` — positional
- `/list-workspaces` — no args

## Output

Filesystem changes (varies per command):
- `/wiki-setup`: creates `<cwd>/.claude/wiki.json` + workspace skeleton
- `/wiki-detect`: report only (no file changes)
- `/switch-workspace`: edits `.claude/wiki.json#workspace`
- `/new-workspace`: scaffolds `workspaces/{name}/`
- `/list-workspaces`: report only

## Flow

Applies platform patterns:
- → [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md) (Bước 0 in all 5)
- → [../../platform/patterns/askuser-confirm-preview.md](../../platform/patterns/askuser-confirm-preview.md) (`/wiki-setup`, `/new-workspace`)

```
User invoke
  ↓
Bước 0: workspace-resolve-step0
  ↓
Command-specific logic (read/edit wiki.json OR scaffold workspace)
  ↓
Optional: askuser-confirm-preview (irreversible ops)
  ↓
Output / Confirm
```

## Config

```yaml
# Per-command config
wiki_setup_interactive: true
new_workspace_template: "templates/workspace.md"
list_workspaces_format: table_with_active_marker
```

## Config Overrides

| Parameter | Platform Default | This Service | Reason |
|-----------|-----------------|--------------|--------|
| _(none — engine-level service, no service-specific overrides)_ | | | |

## Failure Handling

| Scenario | Action |
|----------|--------|
| `.claude/wiki.json` already exists trong `/wiki-setup` | AskUserQuestion: overwrite/cancel |
| `/switch-workspace` target không tồn tại | STOP, hint `/list-workspaces` |
| `/new-workspace` name conflict | STOP, hint different name |
| `wiki_root` resolution fail | Per pattern `workspace-resolve-step0.md` failure strategy |
| Workspace.md broken | STOP, hint recreate hoặc switch |

## Notes

- `/wiki-setup` là entry-point onboard codebase mới vào wiki — first-run interactive.
- `/wiki-detect` là sanity check sau setup hoặc khi `/use-wiki` lỗi resolve.
- 5 commands này KHÔNG depend vào evidence pipeline — pure workspace state ops.

## Related

- Pattern: [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md)
- Pattern: [../../platform/patterns/askuser-confirm-preview.md](../../platform/patterns/askuser-confirm-preview.md)
- Engine source: `.claude/commands/wiki-setup.md`, `wiki-detect.md`, `switch-workspace.md`, `new-workspace.md`, `list-workspaces.md`
- Source: F-017a, evidence `2026-05-08-engine-bootstrap-wiki-template`
