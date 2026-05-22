# Workspace Resolution — canonical Bước 0

Single source of truth cho **Bước 0** của mọi slash command. Trước đây mỗi command lặp đoạn này 20-30 dòng — giờ command chỉ link tới profile phù hợp và liệt kê variable nó set.

> **`wiki_root` Resolution Rule** vẫn ở canonical position: [agents/system-prompt.md#wiki_root-resolution-rule](../system-prompt.md). Doc này chỉ orchestrate quanh rule đó.

---

## Profile A — Active workspace required

Dùng bởi: `code-analyze`, `evidence-ingest`, `evidence-analyze`, `evidence-qa`, `evidence-apply`, `obsidian-ingest`, `update-contextd`, `use-contextd`, `contextd-eval`, `rebase-contextd`.

**Procedure:**

1. Tìm `.claude/wiki.json`: từ `<cwd>` đi lên parent cho tới khi gặp file. Lưu `wiki_json_dir`.
2. Đọc file → `workspace` + `wiki_root` resolve theo [system-prompt.md `wiki_root` Resolution Rule](../system-prompt.md):
   - Absolute path → dùng nguyên.
   - Relative (`"."`, `"./..."`) → resolve relative TỚI `project_root` (= parent của `.claude/`), KHÔNG phải `.claude/` literal, KHÔNG phải cwd.
   - `null`/empty → fallback `~/.claude/wiki-global.json#wiki_root`.
3. STOP nếu file thiếu HOẶC `.workspace` rỗng → guide user:
   ```
   ✗ Chưa có active workspace cho codebase này.
     Chọn workspace đã có: /switch-workspace
     Hoặc setup mới:       /contextd-setup
   ```
4. Set:
   - `workspace_active = .workspace`
   - `effective_wiki_root = <resolved absolute path>`
   - `{ws} = {effective_wiki_root}/workspaces/{workspace_active}/`
5. Validate `{ws}/workspace.md` tồn tại. Nếu thiếu → STOP, yêu cầu user kiểm tra `wiki.json#workspace` hoặc chạy `/list-workspaces` để xem danh sách.

**Variables set:** `wiki_json_dir`, `workspace_active`, `effective_wiki_root`, `{ws}`.

**Hard rule:** mọi knowledge retrieval của command phải scope CHỈ trong `{ws}/`. KHÔNG đọc/copy/tham chiếu workspace khác.

---

## Profile B — Wiki root only (active workspace optional)

Dùng bởi: `new-workspace`, `switch-workspace`, `list-workspaces`, `contextd-setup`. Đây là setup/management commands — có thể chưa có active workspace.

**Procedure:**

1. Tìm `.claude/wiki.json` (nếu có): từ `<cwd>` đi lên parent. Lưu `wiki_json_dir`.
2. Resolve `wiki_root` theo [system-prompt.md Resolution Rule](../system-prompt.md):
   - Absolute path → dùng nguyên.
   - Relative → resolve relative TỚI `project_root` (parent của `.claude/`).
   - `null`/empty → fallback `~/.claude/wiki-global.json#wiki_root`.
3. Nếu cả `wiki.json#wiki_root` lẫn `~/.claude/wiki-global.json#wiki_root` đều thiếu → STOP:
   ```
   ✗ Không xác định được wiki_root.
     Cách nhanh: bash {wiki-template}/scripts/install-to-claude.sh
     Cách thủ công: /contextd-setup
   ```
4. (Optional) Đọc `.workspace` để biết active hiện tại — KHÔNG STOP nếu thiếu (command này có thể đang dùng để SET active lần đầu).

**Variables set:** `wiki_json_dir` (có thể null), `effective_wiki_root`, `workspace_active` (có thể null).

---

## Profile C — Project dir only (no workspace lock)

Dùng bởi: `contextd-trace`, `contextd-viz`. Mục tiêu chỉ là tìm `.claude/runs/` để đọc trace.

**Procedure:**

1. Tìm `.claude/wiki.json` từ `<cwd>` đi lên parent. Lưu `project_dir = parent của .claude/`.
2. Set `runs_dir = {project_dir}/.claude/runs/`.
3. (Optional) Đọc `.workspace` để filter trace theo workspace — KHÔNG STOP nếu thiếu (viewer best-effort).

**Variables set:** `project_dir`, `runs_dir`, `workspace_active` (có thể null).

---

## Implementation note

`project_root = wiki_json_path.parent.parent` (vì `wiki_json_path` luôn là `<root>/.claude/wiki.json`).

Ví dụ: file `D:/myrepo/.claude/wiki.json` có `"wiki_root": "."` → `project_root = D:/myrepo`, `effective_wiki_root = D:/myrepo`. Agent chạy lệnh từ `D:/myrepo/src/utils/` vẫn resolve đúng vì gốc là project root, không phải cwd.

---

## Effective Packs Resolution

**Resolve order** (sau khi đã resolve workspace + wiki_root):

```
local_packs    = wiki.json#packs           (per-codebase override, có thể null/array)
workspace_packs = workspace.md ## Packs    (workspace-wide default, list pack name)

effective_packs = local_packs   IF local_packs is array (kể cả empty array [])
                  workspace_packs OTHERWISE
```

**Replace semantics, KHÔNG additive**: nếu `wiki.json#packs` là array → dùng đúng list đó, ignore `workspace.md` cho codebase này. Nếu null/undefined → fallback workspace.md.

**Empty array `[]` ≠ null**:
- `null` (hoặc field không tồn tại) = "follow workspace default"
- `[]` (empty array) = "không bật pack nào cho codebase này, kể cả workspace có default" (rare nhưng có ý nghĩa rõ ràng)

**Use case**:
- 1 workspace `acme-corp` có `workspace.md ## Packs: [pack-event-driven, pack-web-api]`
- Codebase `acme-frontend` (Next.js) ghi `wiki.json#packs: [pack-frontend-react, pack-web-api]` → effective = frontend + web-api
- Codebase `acme-backend` (không override) → effective = workspace default
- Codebase `acme-mobile` ghi `wiki.json#packs: [pack-product]` (PM dùng để track briefs) → effective = product only

**Quản lý qua `/contextd-setup` Bước 4.5**: UI checkbox để user pick packs cho codebase. Nếu chọn khớp workspace default → không ghi `packs` field (giữ null). Nếu khác → ghi vào `wiki.json`.

**Đồng bộ workspace default**: `/contextd-setup` Bước 4.5.6 cho phép user "Update workspace default" — edit `workspace.md ## Packs` áp dụng mọi codebase.

**Implementation cho commands cần check pack**:

```python
def get_effective_packs(wiki_json: dict, workspace_md_path: Path) -> list[str]:
    local = wiki_json.get("packs")
    if isinstance(local, list):
        return local
    # fallback to workspace.md ## Packs
    return parse_packs_section(workspace_md_path)
```

Commands cần dùng effective_packs (không đọc workspace.md trực tiếp): `/evidence-analyze`, `/evidence-qa`, `/use-contextd` planner, mọi pipeline retrieval-map resolution.
