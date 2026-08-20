# pack-ui-ux — Prompt Overrides

Section bổ sung vào self-check khi pack active.

## System prompt addition

Nếu task liên quan UI/UX, ưu tiên: (1) design token consistency — không hardcode literal; (2) accessibility completeness — keyboard nav + contrast + ARIA; (3) flow coverage — happy path không đủ, phải có edge/error; (4) copy clarity — ngôn ngữ người dùng, không jargon backend.

## Self-Check Constraints (append vào `Constraints to check`)

```
### Design System (pack-ui-ux)
- Color/spacing/font reference token name từ tokens.md, không literal
- Token name tồn tại trong catalog (không tự sáng tạo)
- Component spec cover anatomy/variants/states/a11y/token concerns relevant với component contract; không tạo section rỗng

### Accessibility (pack-ui-ux)
- Interactive element có keyboard behavior theo native semantic/APG pattern; chỉ liệt kê keys thực sự áp dụng
- Visible focus indicator được đề cập
- Contrast ratio ≥ 4.5:1 text, ≥ 3:1 UI component — có note tại color pair
- Meaningful image/icon có accessible alternative; decorative asset bị bỏ khỏi accessibility tree bằng mechanism phù hợp
- Form label association rõ — không chỉ placeholder

### User Flows (pack-ui-ux)
- Flow identify persona/role ở header
- Cover các state relevant từ requirement/state matrix (success, loading/empty, validation, permission, timeout/recovery)
- Mọi decision point có tất cả branch được label
- Chọn diagram hoặc numbered state/step list theo độ phức tạp; format không quan trọng bằng branch/state completeness

### UX Writing (pack-ui-ux)
- Error message actionable và an toàn: điều xảy ra + next step; chỉ nêu nguyên nhân khi biết chắc
- CTA mô tả action/outcome trong context; generic label chỉ dùng khi surrounding semantics làm intent rõ
- Empty state hướng dẫn bước tiếp theo khi user có thể hành động
- Copy không chứa field name / technical term backend

### Design Decisions (pack-ui-ux)
- Thay đổi component library / design system / token scale → ADR trong design/decisions/
- ADR có Options considered + Rationale + Consequences
```

## Layer-2 LLM self-check (append vào validator-rules Layer 2)

```md
### UI/UX
- Token usage: không có color/spacing literal ngoài tokens.md
- A11y: keyboard nav spec + focus indicator + contrast note
- Flow: relevant states/branches covered, persona/role identified
- Copy: actionable safe error, contextual CTA, no backend jargon
- Design decision lớn: ADR file tồn tại
```

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS (pack-ui-ux-*)
- Pitfall design-only: tick từng item ở Layer-2 self-check
```

## Inclusion logic

Pack loader (`scripts/pack_loader.py`) merge nội dung file này vào prompt context khi build `current-task.md` cho `/use-contextd`.
