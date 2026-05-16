# pack-frontend-react — Prompt Overrides

## Self-Check append

```
### React (pack-frontend-react)
- Hooks called at top level only (no condition/loop)
- No direct state mutation — use setter / functional update
- All effects with subscription/listener/timer have cleanup
- All <img> have alt attribute, interactive elements have accessible label
- List items have stable key (not array index unless list is immutable)
- Server vs Client boundary respected (Next.js: "use client" only when needed)
- No expensive computation in render body without useMemo
```
