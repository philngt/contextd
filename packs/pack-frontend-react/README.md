# pack-frontend-react

React + Next.js frontend patterns. Bật khi codebase có React component (`.jsx` / `.tsx`).

## Khi nào bật

- React codebase following the current Rules of React
- Next.js Pages Router hoặc App Router (không giả định migration chỉ vì App Router mới hơn)
- React Native (sub-pack riêng — `pack-mobile-react-native`)

## Components

- `react`: component patterns, hooks
- `hooks`: rules of hooks (gọi cùng cấp, không trong condition/loop)
- `jsx`: JSX/TSX render rules
- `nextjs`: App Router, Server Components, server actions

## Constraints highlights

- A11y baseline: `<img>` có `alt`, button có label, form có `<label htmlFor>`
- Hooks rules: gọi top-level component, không trong condition/loop
- Effect cleanup khi subscribe / addEventListener / setInterval
- Không mutate state trực tiếp — `setState`/`set...` only
- Server vs Client component boundary rõ (Next.js App Router)

## Validator rules

| Rule | Severity |
|------|----------|
| `pack-frontend-react-img-no-alt` | error |
| `pack-frontend-react-list-no-key` | warn |
| `pack-frontend-react-direct-state-mutation` | error |
| `pack-frontend-react-effect-no-cleanup` | warn |

## Bật pack

```md
## Packs

- pack-frontend-react
```

## When not to enable

- UI/design artifact không triển khai React/Next.js; dùng `pack-ui-ux`.
- React Native/mobile-specific implementation; dùng mobile pack tương ứng khi có.

## Retrieval behavior

Routing tách React component, Hooks, JSX/a11y và Next.js. Keyword không dùng các từ chung như `component`, `render`, `element`, nên task backend không vô tình kéo frontend context.

## Verification

```bash
contextd pack-validate --pack pack-frontend-react --format text
contextd context "Review Next.js client boundary and effect cleanup" --preview --format json
python scripts/validate.py --file <component-fixture> --workspace <workspace-with-pack>
```

Standards baseline được review ngày `2026-08-20`: [React Rules](https://react.dev/reference/rules), [React Hooks](https://react.dev/reference/react/hooks), và [Next.js documentation](https://nextjs.org/docs). Workspace phải pin framework version/router và đọc migration guide tương ứng trước khi áp guidance mới.
