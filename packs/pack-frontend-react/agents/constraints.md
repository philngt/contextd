# pack-frontend-react — Constraints

## Hooks Rules (non-negotiable)

- **Hooks at top level** of a component or another hook — never inside condition / loop / nested function. React enforces but agent must respect.
- **Stable order** of hook calls between renders.
- **Custom hook prefix** `use*` always.

## State

- **Never mutate state directly** — use setter (`setX`) hoặc `useReducer` dispatch. `state.foo = bar; setState(state)` là sai (no re-render).
- **Functional update** `setX(prev => ...)` khi new state phụ thuộc previous state.

## Effects

- **Cleanup any subscription** trong `useEffect`: `addEventListener` → `removeEventListener`, `setInterval` → `clearInterval`, observer/socket → unsubscribe. Return cleanup function from effect.
- **Dependency array reflects all closure captures** — empty `[]` means "run once and never again", verify intent.
- **No fetch in render body** — fetch trong `useEffect` (with cleanup/cancel), Server Component, hoặc data-fetching library (TanStack Query, SWR).

## Accessibility (WCAG AA baseline)

- **`<img>` MUST have `alt`** (empty `alt=""` for decorative).
- **`<button>` / interactive element MUST have accessible label** — text content, `aria-label`, hoặc `aria-labelledby`.
- **Form inputs MUST be labeled** — `<label htmlFor=>` hoặc `aria-labelledby`.
- **Color is not the sole indicator** — provide text/icon alongside.

## Server / Client Boundary (Next.js App Router)

- **Server Components by default** — chỉ thêm `"use client"` khi cần interactivity, browser-only API, hoặc state.
- **Server Components không dùng hook** (useState, useEffect, useReducer, etc.).
- **Don't import server-only code** từ client component (process.env secret, DB client, file system).

## Performance

- **No expensive computation in render body** — `useMemo` cho derived state đắt, `useCallback` cho callback truyền xuống memoized component.
- **Don't over-memoize** — `useMemo` trên scalar/cheap value tệ hơn không có.
- **Stable keys for list items** — `key={item.id}`, KHÔNG `key={index}` trừ khi list immutable.
