# Product Brief

Wizard tạo product brief mới trong `{ws}/product/briefs/{slug}.md`. Dành cho **người non-tech** (PM, business, product owner) — không cần biết code.

> Brief = artifact giải thích **vấn đề user + cách đo thành công**, KHÔNG phải spec implementation.
> Reference: [templates/product-brief.md](../../templates/product-brief.md), [pack-product constraints](../../packs/pack-product/agents/constraints.md).

---

## Input

| Arg | Required | Notes |
|---|---|---|
| `{title}` | optional | Tên brief. Nếu không có, wizard sẽ hỏi. Slug auto-generate từ title (kebab-case). |
| `--persona {slug}` | optional | Pre-fill persona link. Nếu không có, wizard hỏi và list personas có sẵn trong `{ws}/product/personas/`. |
| `--out {path}` | optional | Override output path. Default: `{ws}/product/briefs/{slug}.md`. |

---

## Bước 0 — Workspace & pack check

1. Resolve workspace theo [system-prompt.md `knowledge_root` Resolution Rule](../../agents/system-prompt.md). Set `{ws}`.
2. STOP nếu workspace chưa init → guide `/new-workspace` hoặc `/contextd-setup`.
3. Đọc `{ws}/workspace.md` section `## Packs`. Nếu KHÔNG có `pack-product`:
   - Hỏi user (AskUserQuestion): "Workspace này chưa bật `pack-product`. Bật bây giờ?" — Yes / No / Cancel.
   - Yes → append `- pack-product` vào section `## Packs`.
   - No → tiếp tục nhưng warn user rằng validator/constraint của pack-product sẽ không apply.
   - Cancel → STOP.

## Bước 1 — Tạo folder structure (idempotent)

Đảm bảo các folder sau tồn tại trong `{ws}/product/`:

```
product/
├── briefs/
├── okrs/
├── personas/
├── journeys/
└── (files: roadmap.md, metrics.md — sẽ scaffold ở slash command khác)
```

Dùng `mkdir -p`. KHÔNG ghi đè file đã có.

## Bước 2 — Thu thập metadata

Hỏi user theo thứ tự (AskUserQuestion từng câu để giảm cognitive load — non-tech user dễ bỏ cuộc nếu hỏi 1 lần quá nhiều):

| # | Question | Field |
|---|----------|-------|
| 1 | "Brief title (1 dòng, action-oriented — vd 'Reduce signup friction for mobile users')" | `title` |
| 2 | "Vấn đề user đang gặp là gì? (1-2 câu, có số càng tốt — vd '30% user bỏ cuộc ở bước OTP')" | `problem` |
| 3 | "Target persona — chọn 1 hoặc nhiều" | `personas` (multiSelect, list từ `{ws}/product/personas/*.md`; option "Tạo persona sau") |
| 4 | "Success metric chính (vd 'Signup completion rate', 'D7 retention')" | `metric_name` |
| 5 | "Baseline hiện tại của metric đó (số hoặc 'chưa biết')" | `metric_baseline` |
| 6 | "Target value mong muốn (số + thời điểm)" | `metric_target` |
| 7 | "Target ship quarter (vd '2026-Q2', 'TBD')" | `target_release` |
| 8 | "Owner brief này (tên hoặc role)" | `owner` |

**Quy tắc hỏi**:
- Mỗi câu PHẢI có ví dụ cụ thể trong description.
- Cho phép "skip" / "TBD" — đánh dấu trong file để PM fill sau.
- KHÔNG hỏi câu kỹ thuật (database, API, framework) — đó là việc engineering.

## Bước 3 — Tạo slug + validate

- `slug = kebab_case(title)`, max 60 chars, strip vowel marks (Vietnamese → ASCII).
- Nếu `{ws}/product/briefs/{slug}.md` đã tồn tại → suffix `-2`, `-3`, ... tới khi unique.
- Nếu user pass `{title}` arg trùng existing → STOP, hỏi "Update existing brief or create new?".

## Bước 4 — Generate brief từ template

1. Đọc `templates/product-brief.md`.
2. Replace placeholders bằng metadata Bước 2.
3. Section `## Acceptance Criteria` để trống với 3 checkbox stub:
   ```
   - [ ] {User can {action} when {condition}} — TODO PM fill
   - [ ] {When {event}, system shows {response}} — TODO PM fill
   - [ ] {Edge case: ...} — TODO PM fill
   ```
4. Section `## Technical reference` để trống với placeholder `> Engineering fill khi pickup brief.`.
5. Section `## Out of Scope`, `## Constraints`, `## Open Questions` để trống với hint comment.
6. Ghi ra `{ws}/product/briefs/{slug}.md`.

## Bước 5 — Validate ngay sau khi ghi

Chạy validator pack-product trên file vừa tạo (in-memory check, không fail-block):

- `pack-product-brief-missing-problem` — nếu user skip Bước 2.2.
- `pack-product-brief-missing-metric` — nếu user skip Bước 2.4-6.
- `pack-product-brief-missing-acceptance` — luôn warn vì stub TODO.
- `pack-product-brief-dictates-impl` — scan body cho impl keywords.

In warning với màu vàng + dòng "→ Mở file và fill TODO trước khi đưa engineering".

## Bước 6 — Update roadmap (optional)

Hỏi user: "Add brief này vào roadmap quarter `{target_release}`?"
- Yes → mở `{ws}/product/roadmap.md` (tạo từ `templates/product-roadmap.md` nếu chưa có), append vào section `### Exploring` của quarter tương ứng:
  ```
  | {title} | [link](briefs/{slug}.md) | {owner} | TBD |
  ```
- No → skip.

## Bước 7 — Confirm

In bảng tóm tắt:

```
✓ Brief created: {ws}/product/briefs/{slug}.md
  - Problem:  {first 60 chars of problem}...
  - Persona:  {list}
  - Metric:   {metric_name} ({baseline} → {target})
  - Target:   {target_release}
  - Owner:    {owner}

⚠ TODOs (PM fill before handing to engineering):
  - Acceptance criteria (3 stub items)
  - Out of scope
  - Constraints (latency/cost/compliance)
  - Open questions

Next steps:
  1. Open file và fill TODO sections.
  2. Khi ready: change `status: draft` → `status: review` trong frontmatter.
  3. Engineering pickup → fill section `## Technical reference`.
```

---

## Notes

- **Non-tech friendly**: command này KHÔNG hỏi về tech stack, database, framework. Mọi câu hỏi đều business-level.
- **Idempotent**: chạy lại với title cũ → hỏi update or new, không ghi đè im lặng.
- **Workspace isolation**: chỉ ghi vào `{ws}/`, không động tới workspace khác.
