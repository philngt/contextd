# Evidence Ingest

Pull raw data từ MCP / API / paste vào `{ws}/evidence/sources/{evid-id}/` để phục vụ `/update-contextd` hoặc `/rebase-contextd`.
Raw data **CHỈ** dùng cho wiki — KHÔNG đi vào codebase dự án.

> Step 1 trong pipeline: ingest → analyze → qa → apply.
> Reference: `agents/pipeline/critical-analysis-prompts.md`, `agents/pipeline/evidence-lifecycle.md`.

---

## Input

| Arg                | Required | Notes                                                              |
|--------------------|----------|--------------------------------------------------------------------|
| `--source`         | yes      | `mcp` \| `api` \| `paste` \| `code`                                |
| `--ref`            | yes      | mcp: `{server}.{tool}` + args; api: full URL; paste: text/file path; code: repo path (default `<cwd>`) |
| `--label`          | optional | Mô tả ngắn (≤ 80 ký tự) để hiển thị trong `_index.md`              |
| `--related-files`  | optional | Comma-separated wiki paths dự đoán bị ảnh hưởng (relative `{ws}/`) |
| `--scope`          | optional | (code only) Comma-separated paths/globs included trong snapshot. Default: heuristic (`src/**`, `pom.xml`/`package.json`/`build.gradle`, `application.*`). |

Nếu user gọi `/evidence-ingest` không có arg → hỏi qua AskUserQuestion: source type → ref → label.

> **`--source code`**: thông thường gọi qua `/code-analyze` (wraps ingest + analyze). Trực tiếp `/evidence-ingest --source code` chỉ dành cho power-user muốn build snapshot riêng. Xem [code-snapshot-conventions.md](../../agents/pipeline/code-snapshot-conventions.md).

---

## Bước 0 — Workspace check

Theo [workspace-resolution.md Profile A](../../agents/pipeline/workspace-resolution.md#profile-a--active-workspace-required). Set: `wiki_json_dir`, `workspace`, `effective_wiki_root`, `{ws}`.

---

## Bước 1 — Generate evid-id

Format: `{YYYY-MM-DD}-{src}-{slug}`
- `YYYY-MM-DD` = today (ISO date, timezone +07:00).
- `src` = `mcp` | `api` | `paste`.
- `slug` = từ `--label` slugify (lowercase, kebab-case, ≤ 30 ký tự). Nếu không có label → dùng:
  - mcp: tool name slugified
  - api: hostname + path[0..2] slugified
  - paste: hash 8 ký tự đầu của sha256

Đảm bảo unique. Nếu trùng entry trong `_index.md` → append `-{n}`.

---

## Bước 2 — Fetch raw

Tùy `--source`:

### `paste`
- Nếu `--ref` là file path local → đọc file.
- Nếu `--ref` là inline text → dùng nguyên text.
- Nếu user không cung cấp text → hỏi qua AskUserQuestion (option "Other" để paste long text).
- Lưu nguyên bản, ext suy từ content (json/yaml/xml/md/txt).

### `api`
- Confirm URL với user trước khi gọi (AskUserQuestion: "Fetch URL `{url}`? Yes/No").
- Gọi `WebFetch` với URL.
- Header customize không hỗ trợ trong v1 (nếu cần auth, user phải pre-fetch và `--source paste`).
- Ext = từ Content-Type response (`application/json` → `.json`, `text/html` → `.html`, ...).

### `mcp`
- Parse `--ref` thành `{server}.{tool}` + args (JSON inline).
- KIỂM TRA: tool có nằm trong list MCP tool active không? (search current MCP tool catalog).
- Nếu không → STOP, hướng dẫn user enable MCP trước hoặc fallback `--source paste` với output đã copy.
- Nếu có → invoke tool với args, lưu response.

### `code`
- `--ref` = repo root (default `<cwd>` của codebase, KHÔNG phải `wiki_json_dir`). Validate path tồn tại + có `.git/` hoặc `pom.xml` / `package.json` / `build.gradle` / `Cargo.toml` / `go.mod`.
- Confirm với user repo path + scope trước khi snapshot (AskUserQuestion).
- Resolve `git_sha` (full 40-char) + `git_branch` qua `git rev-parse HEAD` + `git rev-parse --abbrev-ref HEAD`. Nếu repo không phải git → set `git_sha = "unmanaged-{sha256-of-tree-manifest}"`.
- Build snapshot `raw.md` theo template [`templates/code-snapshot.md`](../../templates/code-snapshot.md) với 10 section (xem [code-snapshot-conventions.md](../../agents/pipeline/code-snapshot-conventions.md) Section 4):
  1. Project metadata — đọc `pom.xml`/`package.json`/`build.gradle`/...
  2. Dependencies — parse production/test/build
  3. Configs — đọc `application.yaml`/`application.properties`/`.env.example`. **Redact secrets** trước khi ghi (xem code-snapshot-conventions.md Section 6).
  4. REST endpoints — Grep theo markers per [Section 9](../../agents/pipeline/code-snapshot-conventions.md) (workspace có thể bổ sung markers qua `{ws}/evidence/STORAGE.md`).
  5. Message consumers — Grep `@KafkaListener`, MQTT subs, ...
  6. Services & components — Grep stereotypes.
  7. DB schema — Grep `@Entity`, repos, migration files.
  8. Public APIs — class signatures package public.
  9. Git summary — `git log --oneline -50`, `git shortlog -sn --since=1.year`, grep notable commits.
  10. Notes — observations.
- Mọi entry phải kèm citation `({path}:L<start>-L<end>)` (relative tới repo root).
- Ext = `.md`. `raw_filename = "raw.md"`.
- Nếu raw.md > 50KB → tạo thêm `raw.normalized.md` chunked theo Section heading.
- Nếu raw.md > 200KB → STOP, yêu cầu user thu hẹp `--scope`.

**Trong mọi trường hợp**: nếu raw > 100KB → cảnh báo size, hỏi user confirm tiếp.

---

## Bước 3 — Tính sha256 + dedupe

1. SHA256 của raw bytes.
2. Đọc `{ws}/evidence/_index.md` (nếu chưa tồn tại → tạo từ template `templates/evidence-index.md`).
3. Search sha256 trong index.
4. Nếu trùng → STOP, in:
   ```
   ⚠️  Duplicate detected.
   Existing evidence: {old-evid-id} (state: {state}, created: {date})
   Reuse it via /evidence-analyze --id {old-evid-id} or skip ingest.
   ```

---

## Bước 4 — Ghi files

Tạo folder `{ws}/evidence/sources/{evid-id}/`. Trong đó:

1. **`raw.{ext}`** — payload nguyên bản, byte-for-byte.
2. **`source.yaml`** — fill template `templates/evidence-source.yaml` với:
   - `evid_id`, `source_type`, `origin`, `label`, `fetched_at`, `fetched_by` (từ git config user.email hoặc env)
   - `sha256`, `raw_filename`, `raw_size_bytes`
   - `workspace_at_ingest = {active}`  ← CRITICAL
   - `related_files`, `related_projects`, `related_domains` từ `--related-files` arg (hoặc heuristic detect: scan raw cho tên service/topic có trong `{ws}/projects/` hoặc `{ws}/platform/contracts/`).
   - **Khi `source_type=code`** (bổ sung): `git_sha` (full 40-char), `git_branch`, `code_scope` (paths/globs), `code_repo_path`. Validator V-02 reject nếu thiếu/null.
3. **`raw.normalized.md`** — TẠO khi:
   - Raw không phải markdown/text (vd JSON/YAML/HTML/binary)
   - Raw quá dài (> 50KB markdown) — chunk thành sections theo header

   Format normalized:
   ```markdown
   # Normalized — {evid-id}

   > Source: `raw.{ext}` (sha256: {hash})
   > Normalized at: {timestamp}

   ## Section 1 — {auto-detected heading}
   {content chunk}

   ## Section 2 — ...
   ```

   Mỗi section có anchor `#section-N` để analysis prompt cite được.

4. Set file permissions / convention: KHÔNG sửa `raw.*` và `source.yaml` sau bước này (Invariant I-1).

---

## Bước 5 — Update _index.md

Append row vào bảng "Active":
```markdown
| {evid-id} | {source} | {label} | ingested | {date} | {date} | — | — |
```

Nếu `_index.md` chưa có → tạo từ template, giữ legend ở cuối.

---

## Bước 6 — Confirm

In:
```
✅ Evidence ingested
   ID         : {evid-id}
   Workspace  : {active}
   Source     : {source} ({origin})
   Label      : {label}
   Raw file   : {ws}/evidence/sources/{evid-id}/raw.{ext} ({size})
   Normalized : {yes|no}
   State      : ingested

Next:
  /evidence-analyze --id {evid-id}    → run CORE 4 critical-analysis prompts
```

---

## Khi nào nên chạy

- Trước khi cập nhật wiki dựa trên một nguồn external (changelog, ticket, incident report, expert paste).
- Khi muốn audit trail rõ ràng từ "data source" → "wiki change".
- KHI KHÔNG NÊN: nếu chỉ cập nhật wiki từ git diff/code changes → dùng `/update-contextd` trực tiếp, không cần evidence flow.

---

## Common errors

| Error                          | Fix                                                            |
|--------------------------------|----------------------------------------------------------------|
| `.claude/wiki.json missing`     | `/switch-workspace {name}` hoặc `/contextd-setup`                  |
| Duplicate sha256               | Skip ingest, dùng evid-id cũ                                   |
| MCP tool not active            | Enable MCP server hoặc fallback `--source paste`               |
| Raw size > 1MB                 | Chunk trước khi ingest hoặc `--source paste` với extract phần liên quan |
| `related_files` ngoài `{ws}/`  | STOP — vi phạm workspace isolation                             |
| `code` source: not a repo      | Path không có `.git/` và không có file build tool — pass đúng repo path qua `--ref` |
| `code` source: raw.md > 200KB  | Thu hẹp `--scope` (ignore `target/`, `node_modules/`, generated code) |
| `code` source: secrets phát hiện trong raw.md | STOP, xóa folder evid-id (exception I-1), redact rồi ingest lại với evid-id mới |
