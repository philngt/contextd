# Tool Design

Coach **non-tech expert** thiết kế 1 tool từ ý tưởng mơ hồ → spec rõ ràng có thể implement. Hỏi từng câu, vẽ system map, match recipe, recommend tech stack — TẤT CẢ bằng plain language.

> KHÔNG sinh code trong slash này — chỉ ghi spec. Code là việc của session khác (user gõ "implement spec ở `{ws}/tools/{slug}-spec.md`").
> Reference: [pack-solo-builder constraints](../../packs/pack-solo-builder/agents/constraints.md), [recipe library](../../packs/pack-solo-builder/recipes/README.md), [tool-spec template](../../templates/tool-spec.md).

---

## Input

| Arg | Required | Notes |
|---|---|---|
| `"{ý tưởng}"` | optional | Ý tưởng thô bằng plain language. Nếu không có, wizard sẽ hỏi đầu tiên. Vd: `"tool tính moment uốn cho dầm thép"`. |
| `--resume {slug}` | optional | Resume spec đang `draft` — đọc spec hiện có, hỏi tiếp Open Questions. |

---

## Bước 0 — Workspace & pack check

1. Resolve workspace theo [system-prompt.md](../../agents/system-prompt.md). Set `{ws}`.
2. STOP nếu workspace chưa init → guide `/new-workspace` hoặc `/wiki-setup`.
3. Đọc `{ws}/workspace.md` section `## Packs`. Nếu KHÔNG có `pack-solo-builder`:
   - Hỏi (AskUserQuestion): "Workspace chưa bật `pack-solo-builder`. Bật giúp bạn không?" — Yes / No / Cancel.
   - Yes → append `- pack-solo-builder` vào section `## Packs`.
   - No → tiếp tục nhưng warn validator/constraint sẽ không apply.
   - Cancel → STOP.

## Bước 1 — Setup folder

Đảm bảo `{ws}/tools/` tồn tại. `mkdir -p`. Nếu chưa có `{ws}/tools/README.md` → tạo từ stub:

```md
# Tools — toolbox của workspace

Toolbox của bạn (như ngăn kéo dụng cụ). Mỗi file `{slug}-spec.md` = 1 tool.

Quản lý:
- `/tool-design "ý tưởng"` — thiết kế tool mới
- `/tool-list` — xem toàn bộ toolbox
- `/tool-extend {slug}` — thêm/sửa tính năng tool đã có
```

## Bước 2 — Discovery questions (max 2 câu/lần)

> Áp dụng [pack-solo-builder coding-rules.md Discovery Question Style](../../packs/pack-solo-builder/agents/coding-rules.md#discovery-question-style).

Nếu user đã pass `"{ý tưởng}"` arg, ghi nhận làm câu trả lời cho câu 1.

Hỏi tuần tự (dùng AskUserQuestion, mỗi lần ≤ 2 câu):

**Lần 1** (nếu chưa có ý tưởng từ arg):
- "Bạn muốn build tool gì? Mô tả ngắn (1-2 câu)." (text input)

**Lần 2**:
- "Vấn đề bạn đang gặp là gì? Hiện tại làm tay/Excel mất bao lâu?"
- Có ví dụ: `Vd: "Mỗi sáng tôi mất 30 phút copy số liệu từ 5 file Excel sang 1 file tổng"`.

**Lần 3**:
- "Input là gì?" — options: `File (Excel/CSV/PDF/khác)` / `Nhập tay từng số` / `Pull từ API/website` / `Tôi không chắc — Claude đề xuất`
- "Output đi đâu?" — options: `File (Excel/CSV/PDF)` / `Màn hình terminal` / `Dashboard browser` / `Email` / `Database lưu lại` / `Tôi không chắc`

**Lần 4**:
- "Tool này dùng tần suất nào?" — options: `1 lần thử nghiệm` / `Thi thoảng (vài lần/tháng)` / `Hằng ngày` / `Tự động chạy định kỳ`
- "Chỉ bạn dùng, hay share đồng nghiệp?" — options: `Chỉ tôi` / `Share 2-5 đồng nghiệp` / `Share team lớn (10+)` / `Chưa biết`

**Lần 5** (preview system map sau bước này):
- "OS bạn chạy?" — options: `Linux/macOS` / `Windows` / `Cả hai`
- "Bạn quen Python/script chưa?" — options: `Có, chạy command terminal OK` / `Không, muốn tránh terminal` / `Không quan tâm, miễn là dùng được`

**Sau câu 5**: in mini system map preview cho user xem:

```
📋 Tóm tắt hiểu của Claude:

  Input:    {input đã trả lời}
  Process:  {derived từ vấn đề}
  Output:   {output đã trả lời}
  Tần suất: {frequency}
  Audience: {chỉ tôi / share team}
  OS:       {os}

Đúng không? Hay cần sửa gì?
```

Confirm → Bước 3. Sửa → quay lại câu liên quan.

## Bước 3 — Tool catalog scan (dedup check)

> Áp dụng [pack-solo-builder retrieval-map.md Tool Catalog Scan](../../packs/pack-solo-builder/agents/pipeline/retrieval-map.md#tool-catalog-scan).

1. Glob `{ws}/tools/*-spec.md` (loại trừ README.md).
2. Đọc title + Problem section từng spec.
3. Compare với ý tưởng user:
   - Title fuzzy match ≥ 70% (case-insensitive, strip diacritics)
   - Hoặc Problem keyword overlap ≥ 3 từ chính
   - Hoặc Input/Output type giống

4. **Nếu match** → STOP, hỏi:
   ```
   ⚠ Có vẻ giống tool đã có:
   - {slug-1}: {title}
   - {slug-2}: {title}

   Bạn muốn:
   1. Extend tool đã có (chuyển sang /tool-extend {slug})
   2. Tạo tool mới (force, có lý do khác biệt)
   3. Cancel
   ```

5. Match → 1 hoặc 3 → handle accordingly. Match → 2 → tiếp Bước 4 nhưng note "duplicated-with: {slug}" trong spec.

6. Không match → tiếp Bước 4.

## Bước 4 — Recipe match & recommend

> Áp dụng [pack-solo-builder retrieval-map.md Recipe Match Algorithm](../../packs/pack-solo-builder/agents/pipeline/retrieval-map.md#recipe-match-algorithm-cho-tool-design).

1. Đọc tất cả files trong `packs/pack-solo-builder/recipes/*.md` (trừ README).
2. Match signal user trả lời ↔ recipe theo bảng signal trong retrieval-map.
3. Nhiều match → pick top-1 chính + list top-3 alternatives.

4. Output recommendation theo format trong [prompt-overrides.md Recipe Selection Reasoning](../../packs/pack-solo-builder/agents/pipeline/prompt-overrides.md#recipe-selection-reasoning):

```
🔧 Recipe đề xuất: {recipe-name}

Vì sao: {1-2 câu plain language, link signals user trả lời ↔ recipe}

Alternative considered:
- {alt-1}: không chọn vì {reason}
- {alt-2}: không chọn vì {reason}

Bạn OK với recipe này, hay muốn xem alternative?
```

5. User accept → Bước 5. Reject → AskUserQuestion list alternatives với detail. Pick lại → Bước 5.

6. **Không match recipe nào** → STOP:
   ```
   ⚠ Không tìm thấy recipe phù hợp trong library hiện tại.

   Options:
   1. Mô tả lại task bằng từ khoá khác (back to Bước 2)
   2. Add recipe mới vào pack-solo-builder/recipes/ (dùng templates/tool-recipe.md)
   3. Cancel
   ```

## Bước 5 — Tạo slug + validate

- `slug = kebab_case(strip_diacritics(title))`, max 60 chars.
- Nếu `{ws}/tools/{slug}-spec.md` đã tồn tại → suffix `-2`, `-3` cho tới unique.

## Bước 6 — Generate spec từ template

1. Đọc `templates/tool-spec.md`.
2. Replace placeholders:
   - `{tool-slug}`, `{Tool title}` → từ Bước 5
   - `## Problem` → từ câu trả lời Bước 2 lần 2
   - `## System Map` → vẽ từ Input/Process/Output đã confirm Bước 2 lần 5
   - `## Tech Stack` → table dựa recipe đã chọn Bước 4. Mỗi cột reasoning lấy từ "Trade-offs" section của recipe.
   - `## Setup` → copy nguyên các code block setup từ recipe (theo OS user đã chọn). Nếu user chọn "Cả hai OS" → include cả 2 + Docker.
   - `## Acceptance Criteria` → 3 checkbox stub dạng "When X, then Y" — Claude generate dựa trên Input/Output. Phải testable, không vague.
   - `## Open Questions` → list câu user trả lời "Tôi không chắc" + edge cases Claude nghĩ ra.
   - Frontmatter: `status: draft` nếu có Open Questions, `specced` nếu không. `recipe_used: packs/pack-solo-builder/recipes/{recipe}.md`. `os: {chosen}`.

3. Ghi `{ws}/tools/{slug}-spec.md`.

## Bước 7 — Validate sau khi ghi

Chạy validator pack-solo-builder trên file vừa tạo (in-memory check):

- `pack-solo-builder-spec-missing-*` (problem, system-map, stack, acceptance, setup) — fail nếu thiếu.
- `pack-solo-builder-recipe-not-in-library` — confirm recipe path hợp lệ.
- `pack-solo-builder-vague-acceptance` — confirm acceptance criteria testable.
- `pack-solo-builder-multi-purpose-tool` — confirm 1 tool 1 purpose.

In warning nếu có. KHÔNG block — chỉ flag.

## Bước 8 — Update catalog index

Append entry vào `{ws}/tools/README.md` table (nếu chưa có):

```md
## Catalog

| Tool | Status | Recipe | Purpose |
|------|--------|--------|---------|
| [{slug}]({slug}-spec.md) | {status} | {recipe-name} | {1-line problem summary} |
```

## Bước 9 — Confirm

```
✓ Spec created: {ws}/tools/{slug}-spec.md
  - Title:     {title}
  - Recipe:    {recipe-name}
  - OS:        {os}
  - Status:    {draft | specced}

⚠ Open Questions ({N}): {list nếu có}
⚠ Validator warnings ({N}): {list nếu có}

Next steps:
  1. Mở spec, fill Open Questions nếu còn.
  2. Khi spec đầy đủ: change `status: draft` → `status: specced` trong frontmatter.
  3. Implement: gõ "implement spec ở {ws}/tools/{slug}-spec.md" — Claude code follow spec, không deviate.
  4. Mở rộng sau: /tool-extend {slug}
```

---

## Resume mode (`--resume {slug}`)

Nếu user gõ `/tool-design --resume {slug}`:

1. Đọc spec `{ws}/tools/{slug}-spec.md`.
2. Verify status = `draft` (nếu `specced` → STOP, "Spec đã hoàn thiện, dùng /tool-extend nếu muốn sửa").
3. Đọc `## Open Questions` section.
4. Hỏi user từng câu (AskUserQuestion, max 2/lần).
5. User trả lời → update spec section liên quan + xoá entry trong Open Questions.
6. Khi Open Questions empty → đề xuất change status → `specced`.

---

## Notes

- **Plain Vietnamese mặc định**. Tech term để tiếng Anh + 1 câu giải thích VN.
- **Mỗi câu hỏi PHẢI có ví dụ cụ thể** trong description AskUserQuestion.
- **"Tôi không chắc" option** PHẢI có ở mọi câu — Claude pick default + ghi Open Questions.
- **KHÔNG sinh code** ngay cả khi user request — refuse + giải thích "tool-design chỉ làm spec, code là session khác".
- **Workspace isolation**: chỉ ghi vào `{ws}/`, không động workspace khác.
