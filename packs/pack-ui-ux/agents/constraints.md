# pack-ui-ux — Constraints

Hard rules cho UI/UX design documentation. Additive trên engine constraints. Strict-only direction.

## Design Token (`pack-ui-ux-design-token`)

- **KHÔNG hardcode color/spacing/font literal** trong component spec, flow doc, hoặc UX writing doc — mọi giá trị phải tham chiếu token name (vd `color-primary-default`, không `#3B5AFE`). Ngoại lệ duy nhất: file `tokens.md` nơi token được định nghĩa.
- **Token name PHẢI thuộc token catalog** trong `{ws}/platform/design/tokens.md` — KHÔNG tự sáng tạo token name ngoài catalog.
- **Xóa/đổi tên token hiện có** PHẢI có migration note trong `tokens.md` + thông báo consumer bị ảnh hưởng.

## Accessibility (WCAG 2.2 AA) (`pack-ui-ux-accessibility`)

- **Contrast ratio PHẢI ≥ 4.5:1** cho text thông thường, **≥ 3:1** cho large text (≥ 18pt hoặc 14pt bold) và UI component (border, icon).
- **Mọi interactive element** (button, link, input, custom control) PHẢI có spec keyboard navigation (Tab/Enter/Space/Escape/Arrow) và visible focus indicator.
- **Mọi image/icon có nghĩa** PHẢI có alt text spec; icon decorative PHẢI có `aria-hidden` note.
- **Form element** PHẢI có label association spec — KHÔNG chỉ placeholder làm label.
- **ARIA role/label** khi dùng PHẢI match ARIA Authoring Practices Guide — KHÔNG dùng ARIA để patch non-semantic HTML.

## User Flows (`pack-ui-ux-user-flows`)

- **Mỗi user flow PHẢI cover relevant states** từ requirement/state matrix: success, loading/empty, validation, permission, timeout/recovery theo rủi ro thực tế; không dùng quota edge-case cố định.
- **Flow PHẢI identify persona/role** thực hiện — KHÔNG generic "user".
- **Decision point PHẢI có tất cả branch** được label — KHÔNG để branch ngầm.
- **Screen flow KHÔNG thay thế wireframe/prototype** — nếu interaction phức tạp, link tới Figma/prototype trong flow doc.

## UX Writing (`pack-ui-ux-writing`)

- **Copy dành cho end-user KHÔNG dùng jargon kỹ thuật** (stack trace, error code, field name backend) — translate sang ngôn ngữ người dùng.
- **Error message PHẢI actionable và an toàn** — nói điều xảy ra và next step phù hợp; chỉ nêu nguyên nhân khi biết chắc và không leak sensitive detail.
- **CTA PHẢI mô tả action/outcome trong context**; generic label chỉ hợp lệ khi surrounding semantics làm accessible name rõ ràng.

## Design Decisions (`pack-ui-ux-decisions`)

- **Quyết định chọn component library, design system, hoặc thay đổi token scale PHẢI có ADR** trong `{ws}/design/decisions/`.
- **Design ADR PHẢI nêu** options considered + rationale + consequences.

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
