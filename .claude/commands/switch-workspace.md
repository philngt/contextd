# Đổi Active Workspace

Đổi workspace cho **codebase hiện tại** bằng cách cập nhật field `workspace` trong `<cwd>/.contextd/config.json`.

> Active workspace là per-codebase. Mỗi project repo tự khai báo workspace của nó trong `.contextd/config.json`. Command này chỉ tác động lên cwd hiện tại — KHÔNG có file pointer global trong knowledge repo.

## Argument syntax

```
/switch-workspace [--global] [--dry-run] [{name}]
```

Parsing rule:
- Token bắt đầu bằng `--` → flag (`--global`, `--dry-run`).
- Token còn lại đầu tiên không phải flag → `{name}`.
- Nếu không có `{name}` → vào AskUserQuestion ở Bước 1 để user chọn từ danh sách.

## Bước 0 — Resolve `knowledge_root`

Theo [workspace-resolution.md Profile B](../../agents/pipeline/workspace-resolution.md#profile-b--knowledge-root-only-active-workspace-optional). Set: `config_dir` (có thể null), `effective_knowledge_root`, `workspace_active` (có thể null).

## Bước 1 — Lấy target name

- Nếu `{name}` đã được pass qua argument → dùng luôn.
- Nếu không:
  - Glob `{knowledge_root}/workspaces/*/workspace.md`. Nếu danh sách rỗng → STOP:
    ```
    ✗ {knowledge_root}/workspaces/ chưa có workspace nào.
      Tạo mới: /new-workspace {name}
    ```
  - Hỏi user chọn (AskUserQuestion) từ danh sách parse được.

## Bước 2 — Validate

1. Regex name: `^[a-z0-9-]+$` (đồng bộ với `/new-workspace` Bước 2). Vi phạm → STOP, báo lỗi.
2. `{knowledge_root}/workspaces/{name}/` phải tồn tại và là directory.
3. `{knowledge_root}/workspaces/{name}/workspace.md` phải tồn tại.

Nếu (2) hoặc (3) fail → STOP:

```
✗ Workspace "{name}" không tồn tại hoặc thiếu workspace.md.
  Có sẵn: {liệt kê tên workspace từ glob}
  Tạo mới: /new-workspace {name}
```

KHÔNG ghi gì khi validate fail.

4. Parse `## Packs` trong `{knowledge_root}/workspaces/{name}/workspace.md` → `target_packs[]`. Với mỗi pack verify `{knowledge_root}/packs/{pack}/pack.yaml` tồn tại. Pack thiếu → đánh dấu `missing` trong output Bước 4 (KHÔNG block switch — đồng bộ với behaviour của `/new-workspace` Bước 4 và `/use-contextd` Bước 0.7).

## Bước 3 — Cập nhật `<cwd>/.contextd/config.json`

Hai trường hợp:

### 3a. File đã tồn tại

Dùng Edit để partial update field `workspace = "{name}"`, giữ nguyên các field còn lại. Nếu `.workspace` cũ ≠ `{name}` → in dòng `Previous: {old} → {name}`.

Nếu flag `--dry-run` → in nội dung sẽ ghi (diff field `workspace`) và stop, KHÔNG Edit.

### 3b. File chưa tồn tại

Tạo `<cwd>/.contextd/config.json` minimal:

```json
{
  "project": "{cwd basename}",
  "workspace": "{name}",
  "knowledge_root": null
}
```

In cảnh báo nổi bật và **chặn flow `/use-contextd`** cho tới khi user chạy `/contextd-setup`:

```
⚠ Đã tạo .contextd/config.json minimal. Pipeline /use-contextd sẽ KHÔNG hoạt động đúng cho tới khi
  các field knowledge_map / domain được fill.

  Bước tiếp theo BẮT BUỘC: /contextd-setup
```

Chỉ chuyển sang Bước 4 sau khi in cảnh báo này.

## Bước 4 — Confirm

Đọc `{knowledge_root}/workspaces/{name}/workspace.md`, parse Identity block + `## Packs`. Với mỗi field thiếu → in `(unknown)`, KHÔNG fail.

```
✓ Active workspace cho codebase này: {name}
  Company: {company | (unknown)}
  Role:    {role    | (unknown)}
  Period:  {period  | (unknown)}
  Packs:   {p1, p2, …}  hoặc "(none)"
           {⚠ liệt kê pack missing nếu có}

Pipeline scope: {knowledge_root}/workspaces/{name}/
Config file:    <cwd>/.contextd/config.json
```

## Bước 5 — Reset task context (optional)

Nếu file `<cwd>/.contextd/context/current-task.json` tồn tại, regenerate-warn nếu **bất kỳ** điều kiện đúng:

1. Field `Workspace:` của file ≠ `{name}` (do `contextd-context-selector` ghi — xem [.claude/agents/contextd-context-selector.md](../agents/contextd-context-selector.md))
2. Field `Packs:` của file ≠ `target_packs` (set so sánh — order-insensitive)
3. mtime của `current-task.json` < mtime của `{knowledge_root}/workspaces/{name}/workspace.md`

Khi cần regenerate:

```
⚠ .contextd/context/current-task.json đang ghi context cho workspace/pack set cũ.
  Chạy /use-contextd để regenerate trước khi tiếp tục code.
```

## Bước 6 — (Optional) Set global default

Trường hợp:

- `--global` được pass explicit → ghi luôn `default_workspace = {name}` vào `~/.contextd/config.json`, không hỏi.
- `~/.contextd/config.json` không tồn tại → SKIP Bước 6, hint user `bash {contextd-root}/scripts/install-to-claude.sh` để tạo file global trước.
- File global tồn tại VÀ field `default_workspace` là `null`/empty → hỏi:

  > "Set `default_workspace = {name}` trong `~/.contextd/config.json` để các codebase mới mặc định dùng workspace này?"

  Yes → cập nhật field; No → bỏ qua.

- File global tồn tại VÀ `default_workspace` đã có giá trị (≠ `{name}`) VÀ user KHÔNG pass `--global` → KHÔNG hỏi (tránh lặp). User muốn đổi global default phải pass `--global` explicit.

## Compatibility

Nếu codebase chỉ có legacy `.claude/wiki.json` hoặc `.Codex/wiki.json`, command có thể đọc nó để lấy workspace hiện tại nhưng khi ghi phải ưu tiên tạo/cập nhật `.contextd/config.json`. Legacy files chỉ mirror nếu cần migration adapter.
