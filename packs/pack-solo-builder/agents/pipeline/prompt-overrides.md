# pack-solo-builder — Prompt Overrides

## Self-Check append (cho mọi tool spec generation)

```
### Tool Spec (pack-solo-builder)
- Spec có đủ 4 section bắt buộc: Problem, System Map, Tech Stack (chosen + reasoning), Acceptance Criteria
- System Map có cả plain text + mermaid (hoặc plain text + ASCII art nếu mermaid không hợp)
- Tech Stack table có 2 cột reasoning: "Vì sao chọn" + "Vì sao KHÔNG alternative"
- Recipe used được cite rõ với đường dẫn cụ thể
- Tool catalog đã scan — confirm không trùng spec đã có
- 1 tool = 1 mục đích — spec không mô tả > 1 mục đích chính
- Setup section có CẢ Linux + Windows (Docker recommend nếu deps phức tạp)
- Acceptance Criteria testable (When X, then Y) — không dùng "hoạt động tốt"
- Mỗi jargon kỹ thuật có 1-line explain plain language ngay sau
- Domain term có check glossary `{ws}/domains/*/glossary.md`
- Status frontmatter set đúng: draft (còn Open Questions) hoặc specced (đầy đủ)
```

## Output style override

- **Audience**: assume reader là chuyên gia ngành khác (cơ khí, kế toán, y tế, ...) — KHÔNG có background dev. Họ thông minh, nhưng không biết jargon kỹ thuật.
- **Tone**: như đồng nghiệp helpful, không condescending. KHÔNG dùng "easy", "simply", "just" — vì độ dễ tuỳ background.
- **Vietnamese mặc định** (nếu workspace dùng VN). Tech term để nguyên tiếng Anh + 1 câu giải thích VN.
- **Concrete > abstract**: thay vì "data processing", viết "đọc file Excel, lọc dòng, ghi file mới".

## Discovery Question Pacing (cho `/tool-design`)

- **Tối đa 2 câu/lần** trong AskUserQuestion. Non-tech dễ overload.
- **Mỗi câu PHẢI có**:
  - Phrasing trực diện (không "có thể bạn vui lòng cho biết...")
  - Ví dụ cụ thể trong description (vd "Input là gì? Ví dụ: file Excel xuất từ phần mềm kế toán, hoặc nhập tay từng số")
  - Option "Tôi không chắc / Để Claude đề xuất" — Claude pick default, ghi `## Open Questions`
- **Sau câu 4-5**, in mini system map preview để user thấy "đang đi đúng hướng" — tăng motivation tiếp.

## Recipe Selection Reasoning

Khi propose recipe, output format:

```
🔧 Recipe đề xuất: {recipe-name}

Vì sao: {1-2 câu plain language, link signals user trả lời ↔ recipe}

Alternative considered:
- {alt-1}: không chọn vì {reason}
- {alt-2}: không chọn vì {reason}

Bạn OK với recipe này, hay muốn xem alternative?
```

User confirm → tiếp Bước 4 (write spec). Reject → quay lại Bước 2 hỏi thêm.

## Context Priority cho `/tool-design`

1. `packs/pack-solo-builder/recipes/` — highest, mọi tech recommendation từ đây
2. `{ws}/tools/*.md` — catalog scan để dedup
3. `{ws}/domains/*/glossary.md` — term reference
4. `templates/tool-spec.md` — output skeleton
5. `{ws}/workspace.md` — biết workspace context (chuyên ngành gì, OS gì user thường dùng)

KHÔNG đọc `{ws}/platform/`, `{ws}/projects/` — đó là engineering scope, không relevant cho solo builder.

## Build Mode (sau khi spec specced, user gõ "implement spec ở ...")

Khi user explicit yêu cầu implement:

- Đọc spec đã `specced`
- Confirm với user: "Implement theo spec này, không deviate. OK?"
- Code follow đúng Tech Stack table — KHÔNG đổi library tự ý
- Write Build Log section vào spec sau mỗi milestone
- Acceptance Criteria checkbox tick từng cái khi pass test thủ công
