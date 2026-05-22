# pack-ui-ux — Top 10 Common Pitfalls

Anti-pattern lặp lại trong UI/UX documentation. Additive trên [constraints.md](constraints.md).

## P01 — Hardcode màu/spacing không qua token

- **NG**: component spec ghi `background: #3B5AFE; padding: 12px`.
- **OK**: `background: color-primary-default; padding: spacing-md`.
- **Why**: rebrand = sửa 1 file tokens.md thay vì tìm-thay toàn bộ spec.
- **Detect**: Layer-1 `pack-ui-ux-hardcoded-color` — regex `#[0-9a-fA-F]{3,6}` và `rgb\(` ngoài tokens.md.
- **Severity**: error

## P02 — Bỏ qua keyboard navigation

- **NG**: spec chỉ mô tả mouse interaction; dropdown không có keyboard dismiss.
- **OK**: mỗi interactive component có bảng keyboard: `Tab`, `Enter`, `Space`, `Escape`, `Arrow`.
- **Why**: 26% người dùng dùng keyboard-only hoặc assistive tech; WCAG 2.1.1 requirement.
- **Detect**: Layer-1 `pack-ui-ux-missing-a11y-note` — component spec thiếu blockquote `A11y:`.
- **Severity**: warn

## P03 — User flow chỉ có happy path

- **NG**: flow diagram từ Start → success, không có branch lỗi.
- **OK**: section "Edge & Error Paths" liệt kê: validation fail, empty state, timeout, permission denied.
- **Why**: dev implement theo flow → miss error handling → UX bị lỗ hổng lúc runtime.
- **Detect**: Layer-1 `pack-ui-ux-flow-no-error-path` — flow file thiếu heading `Error|Edge`.
- **Severity**: warn

## P04 — Contrast ratio dưới ngưỡng WCAG AA

- **NG**: text màu `color-grey-400` trên `color-grey-100` → ratio 2.1:1.
- **OK**: kiểm tra contrast khi define color pair; note ratio trong token hoặc component spec.
- **Why**: WCAG 1.4.3 requirement; fail audit; unreadable cho người low vision.
- **Detect**: Layer-1 `pack-ui-ux-contrast-unchecked` — component spec có color token nhưng không nêu contrast ratio.
- **Severity**: warn

## P05 — UX copy dùng technical error message

- **NG**: "Error 422: Unprocessable Entity — validation failed on field `user_email`".
- **OK**: "Your email address isn't valid. Please check and try again."
- **Why**: user không hiểu → abandon; support ticket tăng.
- **Detect**: Layer-2 — error message trong UX writing không chứa code/field name backend.
- **Severity**: error

## P06 — Design decision không có ADR

- **NG**: team đang dùng Material UI v4, không ai biết tại sao không upgrade v5.
- **OK**: `design/decisions/2025-03-01-keep-mui-v4.md` ghi lý do + consequences.
- **Why**: người mới join đoán hoặc re-litigate quyết định cũ; drift silent.
- **Detect**: Layer-2 — khi thay đổi component library/design system, phải có ADR file.
- **Severity**: warn

## P07 — ARIA label generic

- **NG**: `aria-label="button"`, `aria-label="link"`, `aria-label="icon"`.
- **OK**: `aria-label="Close dialog"`, `aria-label="View user profile — Jane Doe"`.
- **Why**: screen reader đọc "button button button" — vô nghĩa.
- **Detect**: Layer-2 — ARIA label spec không được phép là single generic word.
- **Severity**: error

## P08 — Flow không identify persona

- **NG**: "User clicks checkout" — không biết là guest, authenticated, hay admin.
- **OK**: Flow header ghi `Persona: Guest Shopper | Role: unauthenticated`.
- **Why**: authz logic miss; UX rẽ nhánh theo role không được spec.
- **Detect**: Layer-2 — flow file thiếu field Persona/Role.
- **Severity**: warn

## P09 — Component spec thiếu responsive breakpoint

- **NG**: chỉ spec desktop layout; mobile không được mention.
- **OK**: bảng breakpoint: `xs (<576px)`, `sm (576–768px)`, `md (768–992px)`, `lg (992px+)` với behavior từng breakpoint.
- **Why**: dev implement desktop-only → mobile UI vỡ.
- **Detect**: Layer-2 — component spec có layout/sizing nhưng không nêu breakpoint.
- **Severity**: warn

## P10 — Không spec empty state và loading state

- **NG**: component spec chỉ có "data loaded" state.
- **OK**: explicit section: Empty state (no data, first-time user) + Loading state (skeleton / spinner) + Error state.
- **Why**: dev tự làm → inconsistent across features; UX lỗ hổng.
- **Detect**: Layer-2 — component spec thiếu Empty/Loading/Error state section.
- **Severity**: warn

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 hardcode | `pack-ui-ux-hardcoded-color` | ✓ |
| P02 keyboard | `pack-ui-ux-missing-a11y-note` | ✓ |
| P03 happy-only | `pack-ui-ux-flow-no-error-path` | ✓ |
| P04 contrast | `pack-ui-ux-contrast-unchecked` | ✓ |
| P05 copy | — | ✓ |
| P06 ADR | — | ✓ |
| P07 aria | — | ✓ |
| P08 persona | — | ✓ |
| P09 responsive | — | ✓ |
| P10 empty/loading | — | ✓ |
