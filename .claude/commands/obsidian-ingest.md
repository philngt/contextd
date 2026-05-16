# Obsidian Ingest

Batch promote Obsidian vault notes (RAW clip / personal notes) sang `{ws}/evidence/sources/` để chạy tiếp pipeline `analyze → qa → apply`.

> **Wrapper** quanh [`/evidence-ingest`](evidence-ingest.md) `--source paste`. Mỗi note Obsidian → 1 evid-id `paste`. KHÔNG tự viết logic ghi `source.yaml`/sha256/`_index.md` — delegate xuống `/evidence-ingest` Bước 3-6 để dùng chung convention.

> Step 1 trong pipeline (variant): obsidian-ingest → analyze → qa → apply.
> Reference: [evidence-ingest.md](evidence-ingest.md), [agents/pipeline/raw-storage-conventions.md](../../agents/pipeline/raw-storage-conventions.md), [agents/pipeline/evidence-lifecycle.md](../../agents/pipeline/evidence-lifecycle.md).

---

## Input

| Arg                | Required | Notes                                                              |
|--------------------|----------|--------------------------------------------------------------------|
| `--folder`         | optional | Sub-folder trong vault để scan. Default: `RAW` (hoặc `obsidian.raw_folder` từ config). Pass `.` hoặc `""` để scan toàn vault. |
| `--since`          | optional | Filter theo mtime: `7d` / `24h` / `2026-04-01`. Default: không filter (scan tất cả). |
| `--vault`          | optional | Override vault path (absolute). Default: đọc từ config. |
| `--dry-run`        | optional | Stop sau Bước 4 (summary), KHÔNG ingest. |
| `--include-assets` | optional | (v2 — chưa support) Copy image embeds. v1 luôn strip. |

Nếu user gọi `/obsidian-ingest` không có arg → dùng default `--folder RAW`, hỏi confirm batch trước Bước 5.

---

## Bước 0 — Workspace check

Theo [workspace-resolution.md Profile A](../../agents/pipeline/workspace-resolution.md#profile-a--active-workspace-required). Set: `wiki_json_dir`, `workspace`, `effective_wiki_root`, `{ws}`.

---

## Bước 1 — Resolve vault config

Resolution order (first match wins):

1. CLI arg `--vault {path}`.
2. `<cwd>/.claude/wiki.json` field `obsidian.vault_path` (per-codebase override).
3. `~/.claude/wiki-global.json` field `obsidian.vault_path` (machine-wide).
4. STOP nếu không có cấu hình:
   ```
   ❌ Obsidian vault chưa cấu hình.
   Thêm vào ~/.claude/wiki-global.json:
     "obsidian": {
       "vault_path": "/abs/path/to/vault",
       "raw_folder": "RAW"          // optional, default "RAW"
     }
   Hoặc per-codebase trong <cwd>/.claude/wiki.json.
   Hoặc pass --vault {path} cho lần chạy này.
   ```

Resolve `vault_path` (expand `~`). Validate path tồn tại + là directory.

`folder = --folder` arg | config `obsidian.raw_folder` | `"RAW"`. Nếu `folder ∈ {".", ""}` → scan toàn vault.

---

## Bước 2 — Scan vault

1. List tất cả `*.md` trong `{vault_path}/{folder}/` (recursive). Bỏ qua `.obsidian/`, `.trash/`, file ẩn.
2. Filter `--since` nếu có (mtime ≥ threshold).
3. Nếu list rỗng → STOP với guide:
   ```
   ⚠️ Không có note nào trong {vault_path}/{folder}/ (filter --since={x}).
   ```

Output: `candidates: list[{path, mtime, size}]`.

---

## Bước 3 — Pre-scan từng candidate

Với mỗi file trong candidates:

### 3.1 Parse YAML frontmatter

Match `^---\n(.*?)\n---\n` ở đầu file. Extract:

| Frontmatter field        | Map sang                                  | Fallback nếu thiếu |
|--------------------------|-------------------------------------------|--------------------|
| `wiki-skip: true`        | Bỏ qua note (không tính vào count)        | n/a                |
| `wiki-label`             | `--label` cho `/evidence-ingest`          | First H1 (`# Title`) hoặc filename không ext |
| `wiki-related-files`     | `--related-files`                         | `[]` (auto-detect heuristic ở evidence-ingest sẽ chạy) |
| `wiki-related-domains`   | Ghi vào `source.yaml#related_domains`     | `[]` |
| `wiki-related-projects`  | Ghi vào `source.yaml#related_projects`    | `[]` |
| `wiki-workspace`         | Workspace hint — phải khớp `{workspace}`  | n/a (skip check)   |
| `wiki-evid-id`           | Marker đã ingest từ run trước             | n/a                |

### 3.2 Workspace mismatch check

Nếu frontmatter có `wiki-workspace: foo` mà active là `bar`:
```
❌ Workspace mismatch: note "{path}" yêu cầu workspace "foo", active là "bar".
Chạy /switch-workspace foo trước, hoặc xóa wiki-workspace khỏi frontmatter.
```
STOP toàn batch (không ingest gì).

### 3.3 Sha256 + dedup check

1. Compute sha256 của file content (toàn file, kể cả frontmatter).
2. Đọc `{ws}/evidence/_index.md`. Search sha256.
3. Nếu trùng → đánh dấu `status = "skip-dup"`, ghi nhận `existing_evid_id` từ index.

Note: nếu frontmatter có `wiki-evid-id` mà sha256 KHÔNG match index → user đã sửa note sau ingest cũ. Đánh dấu `status = "modified-since-ingest"`, ghi nhận cả `wiki-evid-id` cũ và sha256 mới. Quyết định ingest mới hay skip để ở Bước 4.

### 3.4 Redaction regex pre-check

Scan content cho pattern nguy hiểm:

| Pattern                                      | Tag             |
|----------------------------------------------|-----------------|
| `(sk|pk)-[A-Za-z0-9]{20,}`                   | api-key         |
| `(?i)(api[_-]?key|access[_-]?token|secret)\s*[:=]\s*["']?[A-Za-z0-9_\-]{16,}` | secret-assignment |
| `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b` (≥ 3 unique matches) | bulk-email      |
| `mongodb(\+srv)?://[^/\s]+:[^@\s]+@`         | db-credential   |
| `Bearer\s+[A-Za-z0-9\-_.]+`                  | bearer-token    |

Nếu match bất kỳ → `status = "need-review"`, ghi list pattern matched. KHÔNG ingest.

### 3.5 Size check

Áp dụng [raw-storage-conventions.md](../../agents/pipeline/raw-storage-conventions.md) Section 3:
- ≤ 100 KB: OK
- 100 KB – 1 MB: warn, confirm trong batch summary
- 1 MB – 5 MB: bắt buộc user split note trước → `status = "too-large"`
- > 5 MB: STOP cả batch

### 3.6 Set status

Mỗi candidate có 1 status final:
- `ready` — sẵn sàng ingest
- `skip-dup` — đã ingest (sha256 trùng), bỏ qua
- `modified-since-ingest` — note có `wiki-evid-id` cũ + sha256 khác → cần user quyết
- `need-review` — match redaction pattern, user phải redact tay
- `too-large` — vượt 1 MB, cần split

---

## Bước 4 — Hiển thị summary + confirm

In bảng:

```
Vault    : {vault_path}/{folder}/
Workspace: {workspace}
Found    : {N} candidates (filter: --since={x|none})

| # | Path                          | Status                | Size  | Label preview            |
|---|-------------------------------|-----------------------|-------|--------------------------|
| 1 | RAW/agentic-second-brain.md   | ready                 |  4KB  | "Agentic Second Brain..."|
| 2 | RAW/kafka-tuning.md           | skip-dup              |  2KB  | (existing: 2026-05-04-…) |
| 3 | RAW/obsidian-ingest-plan.md   | modified-since-ingest |  6KB  | (old id: 2026-05-04-…)   |
| 4 | inbox/with-token.md           | need-review (api-key) |  1KB  | "..."                    |

Summary: ready=1  skip-dup=1  modified=1  need-review=1  too-large=0
```

Nếu `--dry-run` → STOP tại đây.

Nếu có `modified-since-ingest` → AskUserQuestion per note:
- "Re-ingest as new evid-id (sha256 mới)" — proceed
- "Skip (giữ evid-id cũ, bỏ qua sửa đổi)"
- "Update Obsidian frontmatter only (xóa `wiki-evid-id` cũ → bridge tự bỏ qua lần sau)" — không ingest, chỉ cập nhật vault

Nếu `ready` count > 0 → AskUserQuestion confirm:
- "Ingest {ready} note vào workspace `{workspace}`?" Yes / No.

Note `need-review` và `too-large` KHÔNG bao giờ tự ingest. In hướng dẫn riêng:
```
⚠️ {K} note cần review tay:
  - inbox/with-token.md       (api-key)  → mở note, redact, rerun
  - inbox/huge-paste.md       (too-large >1MB) → split thành nhiều note nhỏ
```

---

## Bước 5 — Loop ingest

Với mỗi candidate `status=ready` (hoặc user chọn proceed cho `modified-since-ingest`):

Invoke nội bộ logic của `/evidence-ingest`:

```
/evidence-ingest \
  --source paste \
  --ref {abs path đến note} \
  --label {label đã resolve ở 3.1} \
  [--related-files {csv từ frontmatter}]
```

Cụ thể là chạy các Bước 1-6 của [evidence-ingest.md](evidence-ingest.md):
- Bước 1: generate evid-id (slug từ label, today date, src=`paste`).
- Bước 2: read raw từ file path.
- Bước 3: sha256 + dedup (đã pre-check ở 3.3, nhưng vẫn rerun để chống race).
- Bước 4: ghi `raw.md` + `source.yaml` (set `workspace_at_ingest`, `related_*` từ frontmatter, `notes` ghi `"Source: Obsidian vault {vault_path}/{rel-path}"`).
- Bước 5: append row `_index.md`.
- Bước 6: confirm message per evidence.

### Image embeds (v1 strip)

Trước khi ghi `raw.md`:
- Match `!\[\[([^\]]+)\]\]` (Obsidian wiki-style) và `!\[.*?\]\([^)]+\)` (markdown).
- Replace bằng `[image stripped: {original-ref}]`.
- Append vào `source.yaml#notes`:
  ```
  notes: |
    Source: Obsidian vault {vault_path}/{rel-path}
    {N} image embed(s) stripped (v1 không copy assets):
      - assets/foo.png
      - https://example.com/img.jpg
  ```

### Frontmatter handling trong raw.md

Giữ nguyên frontmatter trong `raw.md` (không strip) — nó có thể có context useful cho analyze. CHỈ strip mấy field bridge dùng (`wiki-*`) để tránh confuse pipeline downstream:

```yaml
---
title: ...           ← giữ
tags: [...]          ← giữ
created: ...         ← giữ
# wiki-label, wiki-related-files, wiki-skip, wiki-evid-id ← strip
---
```

---

## Bước 6 — Update Obsidian frontmatter (best-effort)

Sau khi ingest thành công 1 note, ghi ngược vào file Obsidian:

```yaml
---
{existing frontmatter}
wiki-evid-id: 2026-05-05-paste-agentic-second-brain
wiki-ingested-at: 2026-05-05T14:30:00+07:00
wiki-workspace: example-surgery
---
```

> Đây là ghi vào **vault Obsidian (ngoài wiki repo)** — KHÔNG vi phạm Invariant I-1 (immutability chỉ áp dụng cho file trong `{ws}/evidence/sources/`).

Nếu file vault read-only / không ghi được → log warning, không fail batch (note vẫn đã ingest thành công).

---

## Bước 7 — Final summary

```
✅ Obsidian batch ingest complete
   Workspace : {workspace}
   Vault     : {vault_path}/{folder}/

   Ingested      : {N} evid-id
     - 2026-05-05-paste-agentic-second-brain
     - 2026-05-05-paste-kafka-consumer-tuning
   Skipped (dup) : {M}
   Need review   : {K}  (xem warnings ở Bước 4)
   Too large     : {L}

Next:
  /evidence-analyze --id 2026-05-05-paste-agentic-second-brain   (per evid)
  hoặc /evidence-analyze --batch  (chạy lần lượt hết queue ingested)
```

---

## Khi nào nên chạy

- Hằng tuần: scan `RAW/` clip, promote những note đã chín vào wiki.
- Sau session brainstorm trên Obsidian, muốn đẩy 1-2 note vào pipeline.
- Trước `/update-wiki` lớn: chuyển hết note relevant thành evidence để có audit trail.

KHI KHÔNG NÊN:
- Note còn raw / chưa filter — promote sớm sẽ làm noise pipeline. Tự xem lại nội dung trước.
- Note có nhiều image cần thiết → đợi v2 `--include-assets` hoặc convert manual.

---

## Common errors

| Error                                       | Fix                                                            |
|---------------------------------------------|----------------------------------------------------------------|
| `Obsidian vault chưa cấu hình`              | Thêm `obsidian.vault_path` vào `wiki-global.json` hoặc pass `--vault` |
| Vault path không tồn tại                    | Check absolute path; expand `~` đúng OS                        |
| `Workspace mismatch` từ frontmatter         | `/switch-workspace {name}` trước hoặc sửa `wiki-workspace`     |
| Mọi candidate đều `skip-dup`                | Đã ingest hết — bình thường. Dùng `--since 7d` để chỉ scan note mới. |
| Note `need-review` không thoát được         | Phải redact tay trong Obsidian rồi rerun. Bridge KHÔNG auto-redact. |
| Vault file read-only khi update frontmatter | Bỏ qua step 6 cho note đó; ingest vẫn thành công.              |
| `modified-since-ingest`                     | User chọn re-ingest (tạo evid-id mới) hoặc skip. Raw cũ vẫn immutable. |

---

## Out of scope (v1)

- Watch mode (auto-ingest khi vault thay đổi). Có thể thêm `Stop`/cron hook ở `settings.json` sau.
- Two-way sync: bridge KHÔNG đẩy ngược kiến thức từ wiki → Obsidian.
- Image / PDF assets: v1 strip, v2 sẽ có `--include-assets`.
- Auto-promote sang `domains/`: vẫn cần `/evidence-analyze` → `/evidence-qa` → `/evidence-apply`. Bridge dừng ở state `ingested`.
