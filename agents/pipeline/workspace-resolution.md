# Workspace Resolution — canonical Bước 0

Single source of truth cho **Bước 0** của mọi slash command. Trước đây mỗi command lặp đoạn này 20-30 dòng — giờ command chỉ link tới profile phù hợp và liệt kê variable nó set.

> **Root resolution rule** dùng canonical `knowledge_root`. Legacy aliases are documented in the Compatibility section.

---

## Profile A — Active workspace required

Dùng bởi: `code-analyze`, `evidence-ingest`, `evidence-analyze`, `evidence-qa`, `evidence-apply`, `obsidian-ingest`, `update-contextd`, `use-contextd`, `contextd-eval`, `rebase-contextd`.

**Procedure:**

1. Tìm `.contextd/config.json`: từ `<cwd>` đi lên parent cho tới khi gặp file. Nếu thiếu, fallback legacy adapters (xem Compatibility). Lưu `config_dir`.
2. Đọc file → `workspace` + `knowledge_root`, resolve theo [system-prompt.md Resolution Rule](../system-prompt.md):
   - Absolute path → dùng nguyên.
   - Relative (`"."`, `"./..."`) → resolve relative TỚI `project_root` (= parent của config dir), KHÔNG phải cwd.
   - `null`/empty → fallback `~/.contextd/config.json#knowledge_root`, rồi legacy globals.
3. STOP nếu file thiếu HOẶC `.workspace` rỗng → guide user:
   ```
   ✗ Chưa có active workspace cho codebase này.
     Chọn workspace đã có: /switch-workspace
     Hoặc setup mới:       /contextd-setup
   ```
4. Set:
   - `workspace_active = .workspace`
   - `effective_knowledge_root = <resolved absolute path>`
   - `{ws} = {effective_knowledge_root}/workspaces/{workspace_active}/`
5. Validate `{ws}/workspace.md` tồn tại. Nếu thiếu → STOP, yêu cầu user kiểm tra `config.json#workspace` hoặc chạy `/list-workspaces` để xem danh sách.

**Variables set:** `config_dir`, `workspace_active`, `effective_knowledge_root`, `{ws}`.

**Hard rule:** mọi knowledge retrieval của command phải scope CHỈ trong `{ws}/`. KHÔNG đọc/copy/tham chiếu workspace khác.

---

## Profile B — Knowledge root only (active workspace optional)

Dùng bởi: `new-workspace`, `switch-workspace`, `list-workspaces`, `contextd-setup`. Đây là setup/management commands — có thể chưa có active workspace.

**Procedure:**

1. Tìm `.contextd/config.json` (nếu có), rồi legacy adapters. Lưu `config_dir`.
2. Resolve `knowledge_root` theo [system-prompt.md Resolution Rule](../system-prompt.md):
   - Absolute path → dùng nguyên.
   - Relative → resolve relative TỚI `project_root` (parent của config dir).
   - `null`/empty → fallback global configs.
3. Nếu cả project config lẫn global config đều thiếu root → STOP:
   ```
    ✗ Không xác định được knowledge_root.
     Cách nhanh: bash {contextd-root}/scripts/install-to-claude.sh
     Cách thủ công: /contextd-setup
   ```
4. (Optional) Đọc `.workspace` để biết active hiện tại — KHÔNG STOP nếu thiếu (command này có thể đang dùng để SET active lần đầu).

**Variables set:** `config_dir` (có thể null), `effective_knowledge_root`, `workspace_active` (có thể null).

---

## Profile C — Project dir only (no workspace lock)

Dùng bởi: `contextd-trace`, `contextd-viz`. Mục tiêu chỉ là tìm `.contextd/runs/` để đọc trace.

**Procedure:**

1. Tìm `.contextd/config.json` từ `<cwd>` đi lên parent, fallback legacy adapters. Lưu `project_dir = parent của config dir`.
2. Set `runs_dir = {project_dir}/.contextd/runs/`.
3. (Optional) Đọc `.workspace` để filter trace theo workspace — KHÔNG STOP nếu thiếu (viewer best-effort).

**Variables set:** `project_dir`, `runs_dir`, `workspace_active` (có thể null).

---

## Implementation note

`project_root = config_path.parent.parent` (vì canonical config path là `<root>/.contextd/config.json`; legacy adapter paths cũng nằm dưới `<root>/.claude/` hoặc `<root>/.Codex/`).

Ví dụ: file `D:/myrepo/.contextd/config.json` có `"knowledge_root": "."` → `project_root = D:/myrepo`, `effective_knowledge_root = D:/myrepo`. Agent chạy lệnh từ `D:/myrepo/src/utils/` vẫn resolve đúng vì gốc là project root, không phải cwd.

## Logical paths, canonical containment, and provenance

Contextd uses four related path forms. They are intentionally not interchangeable:

| Form | Meaning | Used for |
|---|---|---|
| Logical path | The spelling supplied by config, CLI, MCP, or a retrieval map, such as `.` or a symlink alias. | User intent, diagnostics, and resolving a path relative to the correct config/project root. |
| Canonical path | The absolute, symlink-resolved filesystem target. | Existence checks and containment decisions only. |
| Named root | A canonical trust boundary with a role: `knowledge_root`, `workspaces/`, the active workspace, `packs/`, or one active pack. | Deciding which descendants a resolver is allowed to read. |
| Source provenance path | A normalized POSIX path relative to `knowledge_root`, such as `workspaces/default/workspace.md`. | `referenced_docs`, static/context-pack sources, policy sources, and source-hash keys. |
| Generated artifact reference | A normalized POSIX path relative to `project_dir`, such as `.contextd/context/current-task.json`. | Context-pack refs and materialized JSON/Markdown/pack locations. |

`project_dir` and `knowledge_root` in runtime JSON are explicitly absolute diagnostic fields. Their absolute values do not relax the rule that source provenance and generated artifact references use their respective relative roots.

### Named-root symlink policy

The configured `knowledge_root` itself may be a symlink or platform alias. Contextd resolves that logical name once; its canonical target becomes the trusted `knowledge_root`.

After that boundary is established:

1. Resolve `workspaces/`, `workspaces/{workspace}`, `packs/`, and `packs/{pack}` as named children.
2. Compare canonical paths for containment, including symlink targets.
3. Reject `workspaces/`, `packs/`, and each named workspace/pack root when that named root is itself a symlink or junction alias. This preserves workspace/pack identity even when an alias points to a sibling under the same parent.
4. A descendant read symlink may be accepted only when its canonical target remains inside the exact named workspace/pack root and both logical and canonical paths pass secret/raw-evidence policy. Write and dynamic-import targets reject aliases.
5. Reject any directory, glob result, or file symlink that escapes its named root. Do not fall back to the raw path and do not read it before the check.
6. Convert an accepted canonical path back to knowledge-root-relative POSIX provenance. A failed relative conversion is a boundary failure, not permission to emit an absolute source path.

This makes `/var/...` and `/private/var/...`, or a checked-out root and its symlink alias, equivalent for security checks without leaking machine-specific canonical paths into deterministic provenance.

### Fail-closed workspace and pack identifiers

Workspace and pack identifiers are path segments, not free-form paths. A valid identifier:

- is a string matching `^[A-Za-z0-9_][A-Za-z0-9._-]*$`;
- is not empty, `.` or `..`, and does not contain `..`;
- contains no `/`, `\\`, `:`, drive prefix, URI prefix, or NUL byte;
- does not end with `.` or use a Windows reserved device basename such as `CON`, `NUL`, `COM1`, or `LPT1`.

An invalid active workspace stops resolution because no safe workspace scope exists. Any invalid or unknown active pack stops effective-state resolution before retrieval; it is not silently dropped, because continuing without its constraints would be a fail-open behavior. No adapter may silently reinterpret either value as a filesystem path.

CLI commands and MCP tools use the same resolver and validation semantics. Transport-specific error formatting may differ, but the selected workspace, effective packs, canonical containment decision, and provenance paths must agree.

---

## Effective Packs Resolution

**Resolve order** (sau khi đã resolve workspace + knowledge_root):

```
local_packs    = config.json#packs         (per-codebase override, có thể null/array)
workspace_packs = workspace.md ## Packs    (workspace-wide default, list pack name)

effective_packs = local_packs   IF local_packs is array (kể cả empty array [])
                  workspace_packs OTHERWISE
```

**Replace semantics, KHÔNG additive**: nếu `config.json#packs` là array → dùng đúng list đó, ignore `workspace.md` cho codebase này. Nếu null/undefined → fallback workspace.md.

**Validation before use**: resolve the raw list first, then validate every pack identifier before joining it under `packs/`. Any invalid or missing selected pack makes the effective state invalid; it never becomes a partial path, fallback name, or silently reduced pack list.

**Empty array `[]` ≠ null**:
- `null` (hoặc field không tồn tại) = "follow workspace default"
- `[]` (empty array) = "không bật pack nào cho codebase này, kể cả workspace có default" (rare nhưng có ý nghĩa rõ ràng)

**Use case**:
- 1 workspace `acme-corp` có `workspace.md ## Packs: [pack-event-driven, pack-web-api]`
- Codebase `acme-frontend` (Next.js) ghi `config.json#packs: [pack-frontend-react, pack-web-api]` → effective = frontend + web-api
- Codebase `acme-backend` (không override) → effective = workspace default
- Codebase `acme-mobile` ghi `config.json#packs: [pack-product]` (PM dùng để track briefs) → effective = product only

**Quản lý qua `/contextd-setup` Bước 4.5**: UI checkbox để user pick packs cho codebase. Nếu chọn khớp workspace default → không ghi `packs` field (giữ null). Nếu khác → ghi vào `.contextd/config.json` (legacy adapters may mirror).

**Đồng bộ workspace default**: `/contextd-setup` Bước 4.5.6 cho phép user "Update workspace default" — edit `workspace.md ## Packs` áp dụng mọi codebase.

**Implementation cho commands cần check pack**:

```python
# Pseudocode: selection and validation are separate steps.
raw_packs = config["packs"] if isinstance(config.get("packs"), list) \
    else parse_packs_section(workspace_md_path)
effective_packs = validate_pack_identifiers(raw_packs)  # raise if any value is invalid
```

Commands cần dùng effective_packs (không đọc workspace.md trực tiếp): `/evidence-analyze`, `/evidence-qa`, `/use-contextd` planner, mọi pipeline retrieval-map resolution.

## Compatibility

During the migration window, the resolver may read legacy `.claude/wiki.json`, `.Codex/wiki.json`, `~/.claude/wiki-global.json`, and `~/.Codex/wiki-global.json`. In those files only, `wiki_root` is treated as an alias for canonical `knowledge_root`. Canonical `.contextd/config.json` always wins when multiple configs exist.
