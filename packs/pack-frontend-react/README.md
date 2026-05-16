# pack-frontend-react

React + Next.js frontend patterns. Bật khi codebase có React component (`.jsx` / `.tsx`).

## Khi nào bật

- React 17+, React 18 (Suspense, Server Components)
- Next.js (Pages Router hoặc App Router)
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
