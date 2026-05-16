# pack-frontend-react — Validator Rules

Layer-1 rule. Implement: [`scripts/rules.py`](../../scripts/rules.py). Prefix `pack-frontend-react-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-frontend-react-img-no-alt`            | error | `<img ...` JSX without `alt=` attribute. |
| `pack-frontend-react-list-no-key`           | warn  | `.map(...=> <Element>)` JSX where the JSX element has no `key=` attribute. |
| `pack-frontend-react-direct-state-mutation` | error | After a `useState` declaration, code mutates the state variable directly (e.g. `state.foo =`, `state.push(`). |
| `pack-frontend-react-effect-no-cleanup`     | warn  | `useEffect(() => { addEventListener / setInterval / setTimeout / subscribe })` without a `return () => ...` cleanup. |

## Layer-2 self-check

```md
### React (pack-frontend-react)
- All <img> have alt attribute (empty alt for decorative)
- All list items have stable key (not array index, unless list is truly immutable)
- No direct state mutation — use setter / functional update
- Effects with subscriptions/listeners/timers have cleanup
- Server vs Client component boundary respected (Next.js)
- Hooks called at top level (no condition/loop)
```

## Limitations

- Regex-only — JSX parsing is naive. Prop spread `{...props}` may hide `alt`/`key`.
- `direct-state-mutation` only catches simple `varName.x = ` patterns.
- `effect-no-cleanup` doesn't recognize cleanups in extracted helper functions.
