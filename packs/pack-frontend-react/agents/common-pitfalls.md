# pack-frontend-react — Top 10 Common Pitfalls

Anti-pattern lặp lại với React/Next.js. Additive trên [constraints.md](constraints.md).

## P01 — Direct state mutation
- **NG**: `state.items.push(x); setState(state)`.
- **OK**: `setState({...state, items: [...state.items, x]})` hoặc immer.
- **Why**: React so sánh reference → không re-render; bug khó tìm.
- **Detect**: Layer-1 `pack-frontend-react-direct-state-mutation` (heuristic).
- **Severity**: error

## P02 — useEffect thiếu cleanup
- **NG**: `useEffect(() => { setInterval(...) }, [])` không clear.
- **OK**: return cleanup `() => clearInterval(id)`.
- **Why**: memory leak, callback chạy sau unmount → set state on unmounted.
- **Detect**: Layer-1 `pack-frontend-react-effect-no-cleanup` (heuristic) + Effect lifecycle test.
- **Severity**: error

## P03 — Dependency array sai/thiếu
- **NG**: `useEffect(() => { fetch(url) }, [])` nhưng `url` thay đổi.
- **OK**: liệt kê đủ dep; dùng `eslint-plugin-react-hooks`.
- **Why**: stale closure, fetch sai data.
- **Detect**: ESLint `react-hooks/exhaustive-deps`; Layer-2.
- **Severity**: error

## P04 — `key={index}` trong dynamic list
- **NG**: `items.map((x, i) => <Row key={i} />)` khi list có reorder/insert/delete.
- **OK**: `key={x.id}` stable.
- **Why**: re-mount sai, mất focus/state input.
- **Detect**: Layer-1 `pack-frontend-react-list-no-key`; index-key correctness vẫn cần Layer-2 review.
- **Severity**: warn

## P05 — Fetch trong render body
- **NG**: `function X() { const data = fetch(...); }` ngoài effect.
- **OK**: `useEffect`/`useQuery`/server component.
- **Why**: fetch mỗi render, race condition, infinite loop.
- **Detect**: Layer-2 — fetch ngoài hook.
- **Severity**: error

## P06 — Thiếu a11y (alt, label, role)
- **NG**: `<img src=... />` không `alt`; button bằng `<div onClick>`.
- **OK**: `<img alt>`, `<button>`, `aria-label`.
- **Why**: screen reader broken, lint fail, lawsuit risk.
- **Detect**: Layer-1 `pack-frontend-react-img-no-alt` + accessibility tooling.
- **Severity**: warn

## P07 — State ownership không rõ
- **NG**: pass mutable state qua nhiều boundary không liên quan, hoặc đưa mọi state vào global store.
- **OK**: colocate state với owner; dùng composition/context/store khi nhiều consumer thực sự cần cùng lifecycle.
- **Why**: coupling và rerender khó đoán; global state thừa cũng tăng complexity.
- **Detect**: Layer-2 review ownership + React Profiler khi có performance claim.
- **Severity**: info

## P08 — Memoization không có evidence
- **NG**: rải `React.memo`, `useMemo`, `useCallback` theo checklist hoặc bỏ qua jank đã được profiler chứng minh.
- **OK**: profile interaction; sửa ownership/work split trước, memoize đúng hotspot/identity contract, đo lại.
- **Why**: memoization có maintenance cost và không thay thế semantic correctness.
- **Detect**: Layer-2 review kèm React Profiler before/after.
- **Severity**: warn

## P09 — useState cho derived value
- **NG**: `const [fullName, setFullName] = useState(first+last); useEffect(() => setFullName(...))`.
- **OK**: `const fullName = first + ' ' + last;` (tính trực tiếp).
- **Why**: double render, state drift.
- **Detect**: Layer-2 review.
- **Severity**: warn

## P10 — Suspense / error boundary thiếu
- **NG**: lazy component không bọc Suspense; throw làm white-screen toàn app.
- **OK**: `<Suspense fallback>`, `<ErrorBoundary>` ở route level.
- **Why**: UX vỡ khi 1 component lỗi.
- **Detect**: Layer-2 — root layout có boundary.
- **Severity**: warn

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 mutation | `pack-frontend-react-direct-state-mutation` | ✓ |
| P02 cleanup | `pack-frontend-react-effect-no-cleanup` | ✓ |
| P03 deps | — (ESLint) | ✓ |
| P04 key-index | `pack-frontend-react-list-no-key` (partial) | ✓ |
| P05 fetch-render | — | ✓ |
| P06 a11y-alt | `pack-frontend-react-img-no-alt` | ✓ |
| P07 drilling | — | ✓ |
| P08 memo | — | ✓ |
| P09 derived-state | — | ✓ |
| P10 boundary | — | ✓ |
