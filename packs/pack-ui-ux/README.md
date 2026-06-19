# pack-ui-ux

UI/UX pack cho workspace có thiết kế sản phẩm: design system, accessibility (WCAG), user flows, và UX writing conventions.

## Khi nào bật

Enable khi workspace cần:
- Chuẩn hóa design token (color, typography, spacing, motion)
- Đảm bảo accessibility baseline WCAG 2.1 AA
- Document user flows / screen flows cho feature
- Thống nhất UX writing (microcopy, error messages, tone of voice)

```md
## Packs

- pack-ui-ux
```

## What it adds

- **Constraints** (`agents/constraints.md`) — hard rules về token usage, WCAG, keyboard nav, flow coverage
- **Working rules** (`agents/coding-rules.md`, compatibility filename) — conventions đặt tên token, cấu trúc flow file, accessibility note format
- **Common pitfalls** (`agents/common-pitfalls.md`) — Top 10 anti-pattern UX/design với detect và severity
- **Validator rules** (`agents/pipeline/validator-rules.md`) — Layer-1 gates: hardcoded color, missing a11y, flow no error path
- **Retrieval map** (`agents/pipeline/retrieval-map.md`) — component → workspace doc mapping
- **Prompt overrides** (`agents/pipeline/prompt-overrides.md`) — self-check bổ sung cho UX tasks

## Workspace paths mới (convention pack này thiết lập)

```
{ws}/platform/design/
  design-system.md     — component catalog, token table, usage rules
  tokens.md            — design tokens (color, typography, spacing, motion)
  a11y.md              — accessibility guidelines + WCAG checklist
  ux-writing.md        — tone of voice, microcopy patterns, error messages
{ws}/domains/{app}/flows/
  *.md                 — user flow / screen flow per feature
{ws}/design/decisions/
  *.md                 — design ADRs (component library choice, design system version…)
```

## Components declared

- `design-system` — component catalog, design token, figma/storybook integration
- `accessibility` — WCAG 2.1 AA compliance, ARIA, keyboard navigation
- `user-flows` — screen flows, interaction spec, happy path + edge cases
- `ux-writing` — microcopy, tone of voice, error message guidelines

## Conflicts with

(none)

## Composition với các pack khác

| Pack kết hợp | Ghi chú |
|---|---|
| `pack-frontend-react` | pack-ui-ux cover design doc, pack-frontend-react cover code implementation — không overlap |
| `pack-ba` | pack-ba cover requirements/persona, pack-ui-ux cover flows/design — bổ sung nhau |
| `pack-product` | pack-product cover OKR/roadmap/persona, pack-ui-ux cover interaction detail — complementary |

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)
- Report injection: [`agents/pipeline/report-prompts.md`](../../agents/pipeline/report-prompts.md) — "pack-ui-ux → Architecture"
