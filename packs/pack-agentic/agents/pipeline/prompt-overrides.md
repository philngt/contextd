# pack-agentic — Prompt Overrides

## Self-Check append

```
### Agent (pack-agentic)
- Loop has MAX_STEPS bound + explicit termination condition
- Repeated-state detection in place
- Every tool call wrapped in timeout
- Tool input has schema validation; tool error returned structured
- Destructive tools require confirm param or human approval checkpoint
- Per-step trace logged (step_n, action, latency, status)
- Token budget tracked; context compaction strategy explicit
- Subagent handoff has clear protocol + bounded depth
```
