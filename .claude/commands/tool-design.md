# Tool Design

Coach **non-tech expert** thiết kế 1 tool từ ý tưởng mơ hồ → spec rõ ràng có thể implement. Hỏi từng câu, vẽ system map, match recipe, recommend tech stack — TẤT CẢ bằng plain language.

> KHÔNG sinh code trong slash này — chỉ ghi spec. Khi spec đã `specced`, user có thể giao task implementation tiếp theo trong cùng conversation hoặc session khác.
> Reference: [pack-solo-builder constraints](../../packs/pack-solo-builder/agents/constraints.md), [recipe library](../../packs/pack-solo-builder/recipes/README.md), [tool-spec template](../../templates/tool-spec.md).

---

## Input

| Arg | Required | Notes |
|---|---|---|
| `"{ý tưởng}"` | optional | Ý tưởng thô bằng plain language. Nếu không có, wizard sẽ hỏi đầu tiên. Vd: `"tool tổng hợp nhiều file Excel thành báo cáo"`. |
| `--resume {slug}` | optional | Resume spec đang `draft` — đọc spec hiện có, hỏi tiếp Open Questions. |

---

## Bước 0 — Workspace & pack check

1. Resolve workspace theo [system-prompt.md](../../agents/system-prompt.md). Set `{ws}`.
2. STOP nếu workspace chưa init → guide `/new-workspace` hoặc `/contextd-setup`.
3. Resolve `effective_packs` theo [workspace-resolution.md](../../agents/pipeline/workspace-resolution.md#effective-packs-resolution): per-codebase `.contextd/config.json#packs` có replace semantics; chỉ fallback `workspace.md ## Packs` khi không có array override. Nếu KHÔNG có `pack-solo-builder`:
   - Hỏi (AskUserQuestion): "Codebase chưa bật `pack-solo-builder`. Bật cho codebase này hay workspace default?" — Codebase / Workspace / Cancel.
   - Codebase → update canonical `.contextd/config.json#packs`, giữ các effective packs khác mà user chọn.
   - Workspace → update `workspace.md ## Packs` và nhắc nếu per-codebase override hiện tại sẽ che default.
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

Chỉ hỏi dữ liệu material còn thiếu; bỏ qua câu đã có bằng chứng từ input/spec. Một
lần hỏi tối đa 2 câu để user dễ trả lời.

**Nhóm 1** (nếu chưa có ý tưởng từ arg):
- "Bạn muốn build tool gì? Mô tả ngắn (1-2 câu)." (text input)

**Nhóm 2** (nếu chưa rõ problem/outcome):
- "Vấn đề bạn đang gặp là gì? Hiện tại làm tay/Excel mất bao lâu?"
- Có ví dụ: `Vd: "Mỗi sáng tôi mất 30 phút copy số liệu từ 5 file Excel sang 1 file tổng"`.

**Nhóm 3** (nếu chưa rõ boundary dữ liệu):
- "Input là gì?" — options: `File (Excel/CSV/PDF/khác)` / `Nhập tay từng số` / `Pull từ API/website` / `Tôi không chắc — Claude đề xuất`
- "Output đi đâu?" — options: `File (Excel/CSV/PDF)` / `Màn hình terminal` / `Dashboard browser` / `Email` / `Database lưu lại` / `Tôi không chắc`

**Nhóm 4** (nếu chưa rõ vận hành/audience):
- "Tool này dùng tần suất nào?" — options: `1 lần thử nghiệm` / `Thi thoảng (vài lần/tháng)` / `Hằng ngày` / `Tự động chạy định kỳ`
- "Chỉ bạn dùng, hay share đồng nghiệp?" — options: `Chỉ tôi` / `Một vài đồng nghiệp` / `Team/organization` / `Chưa biết`

**Nhóm 5** (nếu chưa rõ target/interaction; preview system map sau khi đủ dữ liệu):
- "OS bạn chạy?" — options: `Linux/macOS` / `Windows` / `Cả hai`
- "Bạn quen Python/script chưa?" — options: `Có, chạy command terminal OK` / `Không, muốn tránh terminal` / `Không quan tâm, miễn là dùng được`

**Khi đủ dữ liệu material**: in mini system map preview cho user xem:

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

1. Đọc `{ws}/tools/README.md` catalog trước và shortlist theo normalized title, core outcome/entity, input/output.
2. Chỉ đọc candidate specs. Nếu catalog thiếu, stale hoặc ambiguous thì fallback glob `{ws}/tools/*-spec.md` (loại trừ README.md).
3. Compare semantic purpose + input/output; fuzzy/keyword score chỉ để rank candidate, không dùng threshold chung làm quyết định.

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

1. Đọc `packs/pack-solo-builder/recipes/README.md` và bảng signal trong retrieval-map.
2. Shortlist từ câu trả lời, rồi chỉ đọc recipe owner candidate và alternative có trade-off material.
3. Chọn một owner recipe cho core purpose; mix khi từng recipe sở hữu một phần rõ. Không tạo quota alternative.

4. Output recommendation theo format trong [prompt-overrides.md Recipe Selection Reasoning](../../packs/pack-solo-builder/agents/pipeline/prompt-overrides.md#recipe-selection-reasoning):

```
🔧 Recipe đề xuất: {recipe-name}

Vì sao: {1-2 câu plain language, link signals user trả lời ↔ recipe}

Material alternative considered (omit section nếu không có trade-off đáng kể):
- {alternative}: không chọn vì {reason cho target hiện tại}

Bạn OK với recipe này, hay muốn xem alternative?
```

5. User accept → Bước 5. Reject → AskUserQuestion list alternatives với detail. Pick lại → Bước 5.

6. **Không match recipe nào** → STOP:
   ```
   ⚠ Không tìm thấy recipe phù hợp trong library hiện tại.

   Options:
   1. Làm rõ requirement còn thiếu (back to Bước 2)
   2. Tạo/review recipe mới từ templates/tool-recipe.md
   3. Cancel
   ```

## Bước 5 — Tạo slug + validate

- `slug = kebab_case(strip_diacritics(title))`; giữ ngắn và tuân host/path limit.
- Nếu `{ws}/tools/{slug}-spec.md` đã tồn tại → STOP và hỏi `extend existing` / `choose distinct slug` / `cancel`; không tự sinh suffix `-2`, `-3` khó phân biệt.

## Bước 6 — Generate spec từ template

1. Đọc `templates/tool-spec.md`.
2. Replace placeholders:
   - `{tool-slug}`, `{Tool title}` → từ Bước 5
   - `## Problem` → từ problem/outcome đã xác nhận ở Bước 2
   - `## System Map` → vẽ từ Input/Process/Output đã xác nhận ở Bước 2
   - `## Tech Stack` → table dựa recipe đã chọn Bước 4. Mỗi cột reasoning lấy từ "Trade-offs" section của recipe.
   - `## Setup` → lấy setup cho đúng target environments đã chọn. Chỉ include container khi recipe nêu rationale + verification; chọn nhiều OS không đồng nghĩa phải có Docker.
   - `## Acceptance Criteria` → checkbox dạng "When X, then Y" đủ cover core purpose và state/risk relevant; không quota số lượng.
   - Domain formula/regulation/high-impact decision → cite source/version/jurisdiction + units/assumptions + qualified review owner + verification fixtures. Thiếu bất kỳ phần material nào thì status phải là `draft`.
   - `## Open Questions` → list câu user trả lời "Tôi không chắc" + edge cases Claude nghĩ ra.
   - Frontmatter: `status: draft` nếu có Open Questions, `specced` nếu không. `recipe_used: packs/pack-solo-builder/recipes/{recipe}.md`. `os: {chosen}`.

3. Ghi `{ws}/tools/{slug}-spec.md`.

## Bước 7 — Validate sau khi ghi

Chạy validator pack-solo-builder trên file vừa tạo (in-memory check):

- `pack-solo-builder-spec-missing-*` (problem, system-map, stack, acceptance, setup) — fail nếu thiếu.
- `pack-solo-builder-recipe-not-in-library` — confirm recipe path hợp lệ.
- `pack-solo-builder-vague-acceptance` — confirm acceptance criteria testable.
- `pack-solo-builder-multi-purpose-tool` — confirm 1 tool 1 purpose.

Nếu có structural `error`, giữ status `draft`, ghi Open Question/fix cần thiết và
không đưa implementation next-step. Warning được report cùng limitation để user
review; warning không tự block `specced` trừ khi nó làm lộ knowledge/safety gap.

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
- **"Tôi không chắc" option** có ở câu mà user có thể chưa biết; default được đề xuất phải ghi assumption/Open Question, không silently chốt.
- **KHÔNG sinh code trong chính slash command này** — giải thích `/tool-design` chỉ làm spec; sau khi command hoàn tất và spec đã `specced`, user có thể giao task implementation tiếp theo.
- **Workspace isolation**: chỉ ghi vào `{ws}/`, không động workspace khác.
