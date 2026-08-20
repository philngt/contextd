# pack-agentic — Prompt Overrides

## Self-Check append

```
### Agent (pack-agentic)
- Loop has explicit step/time/token/cost/deadline budget + termination/checkpoint behavior
- Repeated-state detection in place
- Tool calls have configured deadline/cancellation policy appropriate to effects/SLO
- Tool input has schema validation; tool error returned structured
- Effect metadata drives approval/dry-run/compensation for destructive or irreversible tools
- Per-step trace records action class, latency, status, budget delta and redacted artifact refs
- Runtime vs long-term memory boundary + provenance/lifecycle/replacement behavior explicit
- Compaction preserves constraints/decisions/source IDs/hashes and reload plan
- Subagent handoff has schema, tool subset, exit criteria and shared remaining budget
- MCP protocol revision/extensions/transport compatibility pinned when MCP is in scope
```

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
