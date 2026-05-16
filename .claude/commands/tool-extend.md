# Tool Extend

Đề xuất update spec cho tool đã có trong toolbox. KHÔNG sinh code — chỉ propose update spec, code là session khác.

> Khác `/tool-design` (tạo spec mới) — `/tool-extend` sửa spec đã có. Khác implement (Claude code follow spec) — extend chỉ ở stage spec.
> Reference: [pack-solo-builder constraints](../../packs/pack-solo-builder/agents/constraints.md).

---

## Input

| Arg | Required | Notes |
|---|---|---|
| `{slug}` | required | Slug của tool muốn extend. Vd: `moment-uon`. Nếu không nhớ slug → gõ `/tool-list` trước. |

---

## Bước 0 — Workspace check

Resolve workspace. Set `{ws}`. STOP nếu chưa init.

## Bước 1 — Locate tool

1. Tìm file `{ws}/tools/{slug}-spec.md`.
2. Nếu không tồn tại → STOP:
   ```
   ❌ Không tìm thấy tool '{slug}' trong toolbox.

   Gõ /tool-list để xem các tool đã có.
   Gõ /tool-design "{ý tưởng}" để tạo tool mới.
   ```

3. Đọc spec full → parse vào in-memory:
   - frontmatter
   - sections: Problem, System Map, Tech Stack, Setup, Acceptance Criteria, Open Questions, Build Log

## Bước 2 — Show current spec summary

```
🔧 Tool: {title}
  Slug:    {slug}
  Status:  {status}
  Recipe:  {recipe_used}
  OS:      {os}

📋 Current scope:
  Problem:  {first 100 chars of Problem section}
  Input:    {extracted from System Map}
  Output:   {extracted from System Map}

✓ Acceptance ({n}): {first 2 acceptance items}
⚠ Open Questions ({n}): {list nếu có}
```

## Bước 3 — Hỏi user muốn thay đổi gì

AskUserQuestion (single-select):

```
Bạn muốn extend tool này như thế nào?

1. Thêm tính năng mới (new acceptance criteria + có thể đổi system map)
2. Đổi input/output (đổi format hoặc add input source)
3. Đổi tech stack (vd từ CLI sang web app — mix recipe khác)
4. Sửa scope hiện tại (refine acceptance criteria, fix bug logic)
5. Mark done / shelved (cập nhật status)
6. Cancel
```

## Bước 4 — Theo nhánh

### Nhánh 1: Thêm tính năng

- Hỏi: "Mô tả tính năng muốn thêm? (1-2 câu, có ví dụ concrete)"
- Hỏi: "Khi tính năng này xong, làm sao biết nó hoạt động? (testable acceptance)"
- Update spec:
  - Append acceptance items vào `## Acceptance Criteria`
  - Update `## System Map` nếu flow đổi (Claude tự update mermaid)
  - Add entry vào `## Build Log`: `YYYY-MM-DD: Extended scope — added {feature}`
  - Frontmatter: change `status` về `specced` nếu đang `done` (vì cần build thêm)

### Nhánh 2: Đổi input/output

- Hỏi: "Input mới là gì?" / "Output mới đi đâu?"
- Update System Map (cả plain text + mermaid)
- Update Acceptance Criteria liên quan
- Re-check recipe — nếu input/output đổi nhiều có thể recipe không còn match → warn user, suggest re-run `/tool-design` từ đầu nếu drift quá lớn

### Nhánh 3: Đổi tech stack

- Re-run recipe match logic (đọc `packs/pack-solo-builder/recipes/`).
- Show top-3 alternatives dựa input/output hiện tại.
- User pick → update Tech Stack table, Setup section, recipe_used frontmatter.
- Add Build Log: `YYYY-MM-DD: Changed stack from {old recipe} to {new recipe} because {reason}`

### Nhánh 4: Refine scope

- Hỏi: "Acceptance nào cần sửa?" (list current items, user pick)
- User edit nội dung mới.
- Update spec, add Build Log entry.

### Nhánh 5: Mark status

- AskUserQuestion: `done` / `shelved`
- Nếu `shelved`: hỏi "Lý do shelved? (1 câu)" → ghi vào Build Log.
- Update frontmatter `status`.

## Bước 5 — Validate sau update

Chạy pack-solo-builder validators:
- Spec vẫn có 4 section bắt buộc
- `pack-solo-builder-multi-purpose-tool` — extend có thể vô tình tăng scope quá → warn nếu detect
- `pack-solo-builder-vague-acceptance` — check acceptance vừa thêm

## Bước 6 — Show diff & confirm write

In diff dạng `--- old / +++ new` cho từng section đổi (truncate nếu dài):

```
📝 Changes preview:

## Acceptance Criteria
+ - [ ] When user adds --batch flag, tool processes all .xlsx in input dir
+ - [ ] Summary shows per-file row count + total across files

## Build Log
+ - 2026-05-15: Extended scope — added batch processing flag

Confirm write? (Y/N)
```

User Y → ghi file. N → STOP, không thay đổi.

## Bước 7 — Update catalog index

Update entry trong `{ws}/tools/README.md` nếu status đổi (vd `specced` → `building`, hoặc `done`).

## Bước 8 — Confirm

```
✓ Spec updated: {ws}/tools/{slug}-spec.md
  - Status:    {old} → {new}
  - Sections changed: {list}
  - Build log entry added

⚠ Validator warnings ({n}): {list nếu có}

Next steps:
  - Implement update: gõ "implement update theo {ws}/tools/{slug}-spec.md mới (xem Build Log entry mới nhất)"
  - Hoặc continue extend: /tool-extend {slug}
```

---

## Notes

- **KHÔNG sinh code** trong slash này. Refuse nếu user request.
- **Always show diff** trước khi ghi — non-tech sợ thay đổi không kiểm soát.
- **Build Log là single source of truth** cho lịch sử thay đổi spec — mọi extend/refine PHẢI ghi entry.
- **Workspace isolation** — chỉ đụng `{ws}/tools/{slug}-spec.md` và `{ws}/tools/README.md`.
