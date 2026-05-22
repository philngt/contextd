# pack-ui-ux — Coding Rules

Conventions cho UI/UX documentation. Less strict than constraints — đây là idioms, không phải hard gates.

## Design Token Format (tokens.md)

- Naming pattern: `{category}-{variant}-{state}` — vd `color-primary-default`, `color-primary-hover`, `spacing-md`, `font-size-body`.
- Categories chuẩn: `color`, `spacing`, `font-size`, `font-weight`, `line-height`, `border-radius`, `shadow`, `motion-duration`, `motion-easing`.
- Mỗi token entry: name + value + usage note (1 dòng) + alias nếu có.
- Group token theo category với heading `## {Category}`.
- Deprecated token: gạch tên + note `(deprecated — dùng {replacement})`, giữ ít nhất 1 version trước khi xóa.

## Component Spec Format (design-system.md)

- Mỗi component: Anatomy (tên các part) → Variants → States → Do/Don't → A11y note → Token usage.
- **A11y note** dùng blockquote: `> **A11y**: ...` — đặt cuối component spec, trước Token usage.
- Variant table: columns `Variant | When to use | Token override (nếu có)`.
- State coverage: default, hover, focus, active, disabled, error, loading (chỉ những state component hỗ trợ).

## User Flow Format

- File naming: `{feature}-{persona}-flow.md` — vd `checkout-guest-flow.md`, `onboarding-new-user-flow.md`.
- Mỗi flow file: Context (1 đoạn) → Persona + Role → Preconditions → Flow diagram → Edge/Error paths → Exit states.
- **Diagram**: Mermaid `stateDiagram-v2` hoặc `flowchart TD` — ưu tiên stateDiagram cho screen-to-screen. Fallback sang numbered list nếu tool không render Mermaid.
- Decision point dạng câu hỏi: `Is user authenticated?` — branch `Yes →` / `No →`.
- Edge path heading: `## Edge & Error Paths` — liệt kê từng case với state + user feedback.

## Accessibility Doc Format (a11y.md)

- Structure: WCAG principles (Perceivable, Operable, Understandable, Robust) → Checklist per principle → Component-specific notes.
- Checklist item: `- [ ] {criterion}` với link WCAG Success Criterion số (vd `1.4.3`).
- Testing method ghi ngay sau criterion: `(test: axe-core / manual keyboard / screen reader VoiceOver)`.

## UX Writing Format (ux-writing.md)

- Structure per pattern: **Intent** (1 câu) → **Examples** (✅ OK / ❌ Avoid) → **Rationale** (1-2 câu).
- Sections: Tone of Voice → Error Messages → Empty States → Loading States → CTAs → Tooltips → Notifications.
- Error message template: `[What happened]. [Why — nếu useful]. [What to do next].`
- Empty state template: `[No {item} yet]. [Action to create first one].`

## Design Decision (ADR) Format

- File naming: `{YYYY-MM-DD}-{slug}.md` — vd `2026-05-22-choose-component-library.md`.
- Structure: Status → Context → Decision → Options considered → Rationale → Consequences.
- Status: `Proposed | Accepted | Deprecated | Superseded by {file}`.
