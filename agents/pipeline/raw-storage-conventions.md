# Raw Storage Conventions

Hướng dẫn lưu trữ raw data trong `{ws}/evidence/sources/{evid-id}/`. Áp dụng cho mọi workspace, mọi nguồn (MCP / API / paste).

> Engine-level. Workspace có thể override bằng `{ws}/evidence/STORAGE.md`.

---

## 1. Naming convention

### evid-id format
```
{YYYY-MM-DD}-{src}-{slug}[-{n}]
```

| Token   | Required | Quy tắc                                                          |
|---------|----------|------------------------------------------------------------------|
| date    | yes      | ISO date theo timezone +07:00 (vd `2026-05-04`)                  |
| src     | yes      | `mcp` \| `api` \| `paste`                                        |
| slug    | yes      | Slugify từ `--label`: lowercase, kebab-case, ≤ 30 ký tự, ASCII only |
| n       | no       | Số đếm `-2`, `-3`, ... nếu trùng cùng ngày + cùng slug           |

> **Obsidian vault**: note ingest qua [`/obsidian-ingest`](../../.claude/commands/obsidian-ingest.md) vẫn dùng `src=paste` — Obsidian là một kênh nạp paste, KHÔNG phải `source_type` riêng. `label` resolve từ frontmatter `wiki-label` hoặc first H1.

**Auto-derive slug** nếu không có `--label`:
- `mcp` → tool name slugified
- `api` → `{hostname}-{path[0..1]}` slugified
- `paste` → 8 ký tự đầu của sha256

### File naming trong `sources/{evid-id}/`

```
sources/{evid-id}/
├── source.yaml          ← bắt buộc
├── raw.{ext}            ← bắt buộc — extension theo content-type
└── raw.normalized.md    ← optional — chỉ tạo khi raw không phải markdown HOẶC quá dài
```

Extension map (cho `raw.{ext}`):

| Content-type / file format         | ext       |
|------------------------------------|-----------|
| `application/json`                 | `.json`   |
| `application/yaml`, `text/yaml`    | `.yaml`   |
| `text/markdown`, `text/x-markdown` | `.md`     |
| `text/html`                        | `.html`   |
| `text/csv`                         | `.csv`    |
| `text/xml`, `application/xml`      | `.xml`    |
| `text/plain` không xác định        | `.txt`    |
| Binary (PDF, image, ...)           | giữ nguyên ext gốc, KHÔNG tự decode |

KHÔNG đặt tên khác (vd `data.json`, `payload.txt`). Ép luôn là `raw.<ext>` để consumer đoán được.

---

## 2. Khi nào cần `raw.normalized.md`

Tạo khi **bất kỳ điều kiện nào sau đây**:
- Raw không phải markdown/text (JSON, YAML, HTML, XML, CSV, binary)
- Raw markdown nhưng > 50KB (chunk theo header để analysis prompt đọc nhanh)
- Raw không có heading/structure rõ ràng (vd 1 chunk text 200 dòng)

**KHÔNG cần** khi:
- Raw đã là markdown ngắn (≤ 50KB) có structure heading

### Format normalized

```markdown
# Normalized — {evid-id}

> Source: `raw.{ext}` (sha256: {hash[..16]}…)
> Normalized at: {ISO timestamp}
> Original size: {N} bytes → Normalized: {M} bytes

## Section 1 — {auto-detected heading hoặc "Block 1"}

{content chunk, giữ formatting nếu có}

## Section 2 — {next heading}

...
```

**Anchor rules**: mỗi `## Section N` có anchor implicit `#section-N` cho analysis prompts cite.

### Normalize strategies theo loại

| Raw format    | Strategy                                                                  |
|---------------|---------------------------------------------------------------------------|
| JSON          | Pretty-print, mỗi top-level key 1 section (`## key1`, `## key2`)          |
| YAML          | Giữ nguyên, mỗi top-level key 1 section                                   |
| HTML          | Strip tags, giữ heading hierarchy → markdown                              |
| CSV           | Convert thành markdown table; nếu > 100 rows → 1 section/100-row chunk    |
| XML           | XPath-style flatten; mỗi top-level element 1 section                      |
| Long markdown | Chunk theo `##` heading; mỗi chunk ≤ 200 dòng                             |
| Plain text    | Chunk theo blank line groups; auto-heading từ dòng đầu mỗi chunk          |
| Binary        | KHÔNG normalize — chỉ ghi `raw.{ext}` + note trong source.yaml            |

---

## 3. Size limits

| Limit                          | Action                                                            |
|--------------------------------|-------------------------------------------------------------------|
| `raw.{ext}` ≤ 100 KB           | OK, không cảnh báo                                                |
| 100 KB < size ≤ 1 MB           | Warn user trước khi ingest, confirm tiếp                          |
| 1 MB < size ≤ 5 MB             | Bắt buộc `--source paste` với extract trước, không ingest full    |
| size > 5 MB                    | STOP — chunk trước, tách thành nhiều evid-id                      |

`raw.normalized.md` không có limit cứng nhưng nên ≤ 200 KB để analysis prompts xử lý gọn.

---

## 4. Sensitive data — redact TRƯỚC khi ingest

KHÔNG ingest:
- API keys, tokens, passwords
- Personal data (email, SĐT, CCCD) trừ khi cần thiết cho domain
- Internal URLs có credentials inline
- Database dumps có PII

**Redaction rule** trước khi paste/save:
- Token → `<REDACTED-TOKEN>`
- Email khách hàng → `<REDACTED-EMAIL>`
- IP/hostname production → `<REDACTED-HOST>` (trừ khi cần cho debugging)

Note vào `source.yaml#notes`: `"Redacted: tokens, customer emails"`.

Nếu phát hiện sensitive data đã ingest → STOP, xóa cả folder `sources/{evid-id}/` (đây là exception duy nhất cho I-1 immutability), audit log.

---

## 5. Gitignore policy

Đề xuất `.gitignore` cho repo wiki:

```
# Raw evidence > 5KB nên gitignore (commit metadata + analysis only)
workspaces/*/evidence/sources/*/raw.{json,html,xml,csv,bin,pdf,png,jpg}

# Nhưng GIỮ:
!workspaces/*/evidence/sources/*/source.yaml
!workspaces/*/evidence/sources/*/raw.md
!workspaces/*/evidence/sources/*/raw.normalized.md
```

Lý do: `raw.{ext}` có thể chứa sensitive hoặc rất lớn. `source.yaml` có sha256 đã đủ audit. `raw.normalized.md` (đã redact + chunked) đủ cho analyze rerun.

**Workspace có thể override** trong `{ws}/.gitignore` nếu muốn commit raw (vd compliance requirement).

---

## 6. Retention policy

| Folder                              | Retention default | Action sau retention                              |
|-------------------------------------|-------------------|---------------------------------------------------|
| `sources/{evid-id}/`                | Forever (audit)   | Move sang `archive/` sau apply, sau 90 ngày xóa raw nhưng giữ source.yaml |
| `analysis/{evid-id}/`               | Forever           | Same as sources                                   |
| `qa/{evid-id}/`                     | Forever           | Same                                              |
| `applied/{evid-id}/`                | Forever           | KHÔNG xóa — audit trail vĩnh viễn                |
| `archive/{evid-id}/`                | 1 năm             | Sau 1 năm: giữ chỉ `manifest.yaml` + `source.yaml`, xóa raw + analysis |

`/evidence-archive --older-than 90d` để batch archive.
`/evidence-archive --purge-raw --older-than 365d` để gột raw trong archive.

---

## 7. Multi-evidence cho 1 nguồn dài

Nếu nguồn (vd 1 file 50MB hoặc 1 changelog 500 commits) quá lớn:

**KHÔNG** ingest trong 1 evid-id duy nhất.

**Cách chia**:
- Theo topic: 1 evid-id cho mỗi sub-topic.
- Theo time range: 1 evid-id cho mỗi quarter/release.
- Theo source section: 1 evid-id cho mỗi heading top-level.

`source.yaml#notes` cross-reference: `"part 2/5 of release-2025-q4-changelog"`.

Để liên kết các evid-id thành 1 nhóm logic:
- Mỗi evid-id chạy `/evidence-analyze` riêng → mỗi cái có `analysis/{id}/0X-*.md` riêng.
- `/evidence-qa` và `/evidence-apply` xử lý từng evid-id riêng biệt (không có cơ chế merge tự động).
- Nếu cần "gộp" insight từ nhiều evid-id → user tự dùng `--prompt 10` (Final Report Generator) trên evid-id đại diện, manually cite `analysis/{id-other}/...` trong prompt.

---

## 8. Source-type specific notes

### `--source code`
- Dùng cho codebase có sẵn (entry point: `/code-analyze` — không gọi `/evidence-ingest --source code` trực tiếp trừ khi tự build snapshot).
- `source.yaml#origin` format: `code:{repo-name}@{sha7}` (vd `code:surgery-service@a1b2c3d`).
- `raw_filename` LUÔN = `raw.md` (markdown structured per [`code-snapshot-conventions.md`](code-snapshot-conventions.md)). KHÔNG phải `.json`/`.html`.
- Required extra fields trong source.yaml: `git_sha` (full 40-char SHA), `git_branch`, `code_scope` (paths/globs).
- KHÔNG copy source code thật vào `raw.md` — chỉ structured metadata extracts (project info, deps, configs, endpoints, consumers, services, schemas, public APIs, git summary). Source code đã ở git, trace ngược qua `git_sha`.
- Redact nghiêm ngặt: secrets trong configs, contributor emails (giữ tên), credential URLs. Xem code-snapshot-conventions.md Section 6.
- Gitignore: `raw.md` GIỮ trong git (đã redact, ngắn). KHÔNG cần thêm pattern gitignore mới — `!raw.md` đã trong allowlist Section 5.

### `--source mcp`
- `source.yaml#origin` format: `{server-name}.{tool-name}` (vd `linear.search_issues`)
- Ghi thêm `mcp_args` field vào source.yaml (JSON inline) để reproducible
- Nếu MCP tool trả streaming/binary → save raw bytes, normalize riêng

### `--source api`
- `source.yaml#origin` = full URL
- Ghi `http_status`, `response_headers` (filter Set-Cookie, Authorization) vào source.yaml
- Nếu API yêu cầu auth → user phải pre-fetch và `--source paste` (không lưu credential trong wiki)

### `--source paste`
- `source.yaml#origin` = `"user_paste"` hoặc `"file:{relative-path}"` nếu paste từ file
- Nếu user paste 1 chunk dài → ưu tiên hỏi user "đây là 1 nguồn hay nhiều nguồn?" trước khi gộp

---

## 9. Quick checklist trước khi ingest

```
[ ] Đã redact sensitive data?
[ ] Size < 1MB? (>1MB cần extract phần liên quan)
[ ] Có label rõ ràng để slugify?
[ ] Workspace active đúng? (check `<cwd>/.claude/wiki.json.workspace`)
[ ] Related files (nếu biết) thuộc {ws}/?
[ ] Nếu MCP/API: tool/URL đã confirm?
```

Nếu mọi mục check → ingest an toàn.
