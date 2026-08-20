# pack-frontend-react — Constraints

## Hooks Rules (non-negotiable) (`pack-frontend-react-hooks`)

- **Hooks at top level** of a component or another hook — never inside condition / loop / nested function. React enforces but agent must respect.
- **Stable order** of hook calls between renders.
- **Custom hook prefix** `use*` always.

## State (`pack-frontend-react-state`)

- **Never mutate state directly** — use setter (`setX`) hoặc `useReducer` dispatch. `state.foo = bar; setState(state)` là sai (no re-render).
- **Functional update** `setX(prev => ...)` khi new state phụ thuộc previous state.

## Effects (`pack-frontend-react-effects`)

- **Cleanup any subscription** trong `useEffect`: `addEventListener` → `removeEventListener`, `setInterval` → `clearInterval`, observer/socket → unsubscribe. Return cleanup function from effect.
- **Dependency array reflects all reactive values** — không diễn giải `[]` như guarantee “exactly once”; Effect setup/cleanup phải chịu được development checks và remount.
- **No side effect in render** — data fetching dùng framework data layer, Server Component, client cache, hoặc Effect khi thật sự synchronize với external system; request phải có cancellation/race strategy.

## Accessibility (WCAG 2.2 AA baseline) (`pack-frontend-react-accessibility`)

- **`<img>` MUST have `alt`** (empty `alt=""` for decorative).
- **`<button>` / interactive element MUST have accessible label** — text content, `aria-label`, hoặc `aria-labelledby`.
- **Form inputs MUST be labeled** — `<label htmlFor=>` hoặc `aria-labelledby`.
- **Color is not the sole indicator** — provide text/icon alongside.

## Server / Client Boundary (Next.js App Router) (`pack-frontend-react-nextjs-boundary`)

- **Trong App Router, chọn Server/Client boundary có chủ đích** — keep server-only data/secret off client; thêm `"use client"` ở boundary nhỏ nhất cần interactivity/browser API. Pages Router vẫn là supported mode và có contract riêng.
- **Server Components không dùng hook** (useState, useEffect, useReducer, etc.).
- **Don't import server-only code** từ client component (process.env secret, DB client, file system).

## Performance (`pack-frontend-react-performance`)

- **Profile before memoizing** — derived values nên tính trực tiếp khi rẻ; dùng memoization khi profiler/identity contract chứng minh cần thiết, và không xem `useMemo` như semantic guarantee.
- **Compiler/runtime-aware optimization** — follow the pinned React toolchain; không rải `useMemo`/`useCallback` theo checklist lỗi thời.
- **Stable keys for list items** — `key={item.id}`, KHÔNG `key={index}` trừ khi list immutable.

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
