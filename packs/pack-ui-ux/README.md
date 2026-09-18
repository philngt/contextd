# pack-ui-ux

UI/UX pack cho workspace có thiết kế sản phẩm: design system, accessibility (WCAG), user flows, và UX writing conventions.

## Khi nào bật

Enable khi workspace cần:
- Chuẩn hóa design token (color, typography, spacing, motion)
- Đảm bảo accessibility baseline WCAG 2.2 AA
- Document user flows / screen flows cho feature
- Thống nhất UX writing (microcopy, error messages, tone of voice)

```md
## Packs

- pack-ui-ux
```

## What it adds

- **Canonical knowledge** (`knowledge.md`) — inherited constraints, mechanisms,
  strategy choices, exceptions, failure signals, and evidence/stop conditions.
- **Manifest routing** (`pack.yaml#retrieval`) — Global Principles plus only the
  relevant design-system, accessibility, user-flows, or ux-writing section.
- **Deterministic checks** (`scripts/rules.py`) — the same four validator IDs and
  severities, with their actual scope and limitations documented in knowledge.
- **Compatibility adapters** (`agents/`) — existing v0.x filenames are retained;
  they must not become a competing source of rules or routing.

This v3 migration does not add product-strategy or framework implementation
scope. A strategy exception never relaxes an inherited hard constraint. Static
checks and a polished screenshot do not establish usability or WCAG conformance.

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
- `accessibility` — WCAG 2.2 AA compliance, ARIA, keyboard navigation
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

## When not to enable

- Task chỉ implement React component theo design đã chốt; dùng `pack-frontend-react`.
- Product strategy, roadmap hoặc persona research; dùng `pack-product`/`pack-ba`.

## Retrieval behavior

The `decision-first` profile keeps the selected Strategy/Judgment and all core
constraints/evidence, but defers Foundation and Procedure subsections. For
example, `--foundation pack-ui-ux/accessibility/semantics-basics` reloads a
concept and `--procedure pack-ui-ux/accessibility/document-accessibility`
loads the optional documentation recipe. `--context-detail full` includes all
support for the already-selected components. No mandatory skill is introduced.
See [decision-first context](../../docs/decision-context.md).


Manifest v3 loads Global Principles and only matched component sections from
`knowledge.md`; unselected component bodies and legacy static pack files are not
loaded. The four workspace routes are unchanged.

Design system, accessibility, user flow và UX writing route độc lập. Accessibility baseline dùng WCAG 2.2; workspace có thể siết thêm nhưng không hạ chuẩn bằng override.

## Verification

```bash
contextd pack-validate --pack pack-ui-ux --format text
contextd context "Review keyboard navigation and screen reader behavior" --preview --format json
python scripts/validate.py --file <design-fixture> --workspace <workspace-with-pack>
```

Standards baseline được review ngày `2026-08-20`: [W3C WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/). Workspace có thể thêm platform-specific guidance nhưng không được hạ requirement đã áp dụng.

Migration regression checks: `python scripts/test_pack_cognition.py`. These
verify routing, budgets, compatibility, and validator behavior, not model design
quality. See [the evaluation guide](../../docs/domain-cognition-packs.md).
