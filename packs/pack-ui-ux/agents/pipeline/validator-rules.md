# pack-ui-ux — Validator Rules

Layer-1 rules. Prefix `pack-ui-ux-`.

| Rule ID | Severity | Check |
|---|---|---|
| `pack-ui-ux-hardcoded-color` | error | File design (ngoài `tokens.md`) chứa color literal: `#[0-9a-fA-F]{3,6}`, `rgb(`, `hsl(` |
| `pack-ui-ux-missing-a11y-note` | warn | Component spec file trong `platform/design/design-system.md` thiếu blockquote chứa `A11y:` |
| `pack-ui-ux-flow-no-error-path` | warn | User flow file trong `domains/*/flows/*.md` thiếu heading `Error` hoặc `Edge` |
| `pack-ui-ux-contrast-unchecked` | warn | Component spec đề cập color token nhưng không có chuỗi `contrast` hoặc ratio `x.x:1` |

## Layer-2 self-check

```md
### UI/UX (pack-ui-ux)
- Color/spacing dùng token name, không hardcode literal
- Component spec có A11y blockquote (keyboard nav + ARIA note)
- User flow cover state/error/recovery paths relevant với requirement; không quota case cố định
- Contrast ratio được note tại color pair relevant
- Error message actionable + safe; reason chỉ nêu khi known, không leak stack trace/field name
- CTA/accessibility name làm rõ action trong surrounding context
- Design decision lớn (library, system, token scale) có ADR
- Flow file identify persona/role
- Component spec cover states thực sự áp dụng theo state matrix
- Responsive breakpoints được note nếu layout phụ thuộc viewport
```

## Related

- Implementation: [`scripts/rules.py`](../../scripts/rules.py)
- Engine validator pipeline: [`agents/pipeline/validator-rules.md`](../../../../agents/pipeline/validator-rules.md)
