# pack-solo-builder — Prompt Overrides

## Self-Check append (cho mọi tool spec generation)

```
### Tool Spec (pack-solo-builder)
- Spec có đủ 4 section bắt buộc: Problem, System Map, Tech Stack (chosen + reasoning), Acceptance Criteria
- System Map luôn có plain text; diagram chỉ khi branch/integration làm nó hữu ích
- Tech Stack có rationale; so sánh alternative chỉ khi trade-off có thể đổi quyết định
- Recipe used được cite rõ với đường dẫn cụ thể
- Tool catalog đã scan — confirm không trùng spec đã có
- 1 tool = 1 mục đích — spec không mô tả > 1 mục đích chính
- Setup cover đúng target environments đã chốt; container chỉ khi có rationale và được test
- Acceptance Criteria testable (When X, then Y) — không dùng "hoạt động tốt"
- Mỗi jargon kỹ thuật có 1-line explain plain language ngay sau
- Domain term/rule có glossary + source/version/assumptions; gap chưa resolve giữ status `draft`
- High-impact decision có qualified review owner, verification fixtures và human checkpoint theo risk
- Status frontmatter set đúng: draft (còn Open Questions) hoặc specced (đầy đủ)
```

## Output style override

- **Audience**: assume reader là chuyên gia ngành khác (cơ khí, kế toán, y tế, ...) — KHÔNG có background dev. Họ thông minh, nhưng không biết jargon kỹ thuật.
- **Tone**: như đồng nghiệp helpful, không condescending. KHÔNG dùng "easy", "simply", "just" — vì độ dễ tuỳ background.
- **Vietnamese mặc định** (nếu workspace dùng VN). Tech term để nguyên tiếng Anh + 1 câu giải thích VN.
- **Concrete > abstract**: thay vì "data processing", viết "đọc file Excel, lọc dòng, ghi file mới".

## Discovery Question Pacing (cho `/tool-design`)

- Hỏi theo nhóm nhỏ, mặc định 1-2 câu/lần và điều chỉnh theo phản hồi.
- **Mỗi câu PHẢI có**:
  - Phrasing trực diện (không "có thể bạn vui lòng cho biết...")
  - Ví dụ cụ thể trong description (vd "Input là gì? Ví dụ: file Excel xuất từ phần mềm kế toán, hoặc nhập tay từng số")
  - Option "Tôi không chắc / Để Claude đề xuất" — Claude pick default, ghi `## Open Questions`
- Khi đã đủ input/process/output/audience/target, in mini system map preview; không dựa vào số thứ tự câu cố định.

## Recipe Selection Reasoning

Khi propose recipe, output format:

```
🔧 Recipe đề xuất: {recipe-name}

Vì sao: {1-2 câu plain language, link signals user trả lời ↔ recipe}

Material alternative considered (omit nếu không có trade-off đáng kể):
- {material alternative}: không chọn vì {reason}

Bạn OK với recipe này, hay muốn xem alternative?
```

User confirm → tiếp bước generate/write spec của command. Reject → quay lại discovery hoặc recipe shortlist theo lý do user nêu.

## Context Priority cho `/tool-design`

1. `packs/pack-solo-builder/recipes/README.md` — route bằng signal, sau đó chỉ load recipe được chọn và alternative cần so sánh
2. `{ws}/tools/README.md` — catalog index; chỉ load candidate specs, full scan khi index thiếu/stale/ambiguous
3. `{ws}/domains/{domain}/glossary.md` — chỉ domain liên quan; term reference phải giữ provenance
4. `templates/tool-spec.md` — output skeleton
5. Canonical resolved config + `{ws}/workspace.md` — workspace identity, effective packs và target environment

Không load `{ws}/platform/` hoặc `{ws}/projects/` mặc định. Chỉ route vào tài liệu
được active knowledge map/contract chỉ rõ khi tool thật sự phụ thuộc project hoặc
platform boundary; vẫn giữ workspace isolation và priority contract > pattern >
project > domain.

## Build Mode (sau khi spec specced, user gõ "implement spec ở ...")

Khi user explicit yêu cầu implement:

- Đọc spec đã `specced`
- Code follow đúng Tech Stack table — KHÔNG đổi library tự ý
- Write Build Log section vào spec sau mỗi milestone
- Acceptance Criteria checkbox chỉ tick khi có evidence từ automated test hoặc manual verification phù hợp criterion

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
