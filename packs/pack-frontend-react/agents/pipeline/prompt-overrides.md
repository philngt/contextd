# pack-frontend-react — Prompt Overrides

## Self-Check append

```
### React (pack-frontend-react)
- Hooks called at top level only (no condition/loop)
- No direct state mutation — use setter / functional update
- All effects with subscription/listener/timer have cleanup
- All <img> have alt attribute, interactive elements have accessible label
- List items have stable key (not array index unless list is immutable)
- Server/client/rendering boundary follows pinned framework/router; `use client` guidance only when that runtime supports it
- Memoization follows profiler/identity contract and compiler/toolchain behavior; `useMemo` is not a semantic requirement
- Effects synchronize external systems only; dependencies include reactive values and setup/cleanup tolerates remount checks
- Reachable loading/error/empty/stale states and recovery behavior follow data contract
```

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
