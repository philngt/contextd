# Liệt Kê Workspaces

In bảng tất cả workspace trong `{knowledge_root}/workspaces/` và đánh dấu workspace của codebase hiện tại.

## Bước 0 — Resolve `knowledge_root` và active

Theo [workspace-resolution.md Profile B](../../agents/pipeline/workspace-resolution.md#profile-b--knowledge-root-only-active-workspace-optional). Set: `config_dir` (có thể null), `effective_knowledge_root`, `workspace_active`.

Nếu cwd không có `.contextd/config.json` → fallback `~/.contextd/config.json#default_workspace` làm `workspace_active`.

## Bước 1 — Quét workspace folders

- Glob: `{knowledge_root}/workspaces/*/workspace.md`.
- Với mỗi file, parse Identity block để lấy: company, role, period.
- Nếu workspace folder tồn tại nhưng thiếu `workspace.md` → liệt kê với cờ `⚠ missing workspace.md`.

## Bước 2 — In bảng

```
Codebase: {cwd}
Active for this codebase: {active}    (source: .contextd/config.json | global default | none)

| Name              | Company           | Role               | Period           |
|-------------------|-------------------|--------------------|------------------|
| ▶ example-surgery | Example Hospital  | Backend Engineer   | 2026-01 → present |
|   company-b       | ACME Corp         | Senior Backend     | 2025-06 → 2025-12 |
|   ⚠ broken-folder | (no workspace.md) |                    |                  |
```

Workspace active có dấu `▶` ở đầu Name.

## Bước 3 — Hint

Cuối output, in:

```
Switch (this codebase): /switch-workspace {name}
Create new           : /new-workspace {name}
Setup full config    : /contextd-setup
```
