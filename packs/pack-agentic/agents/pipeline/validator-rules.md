# pack-agentic — Validator Rules

Layer-1 rule. Implement: [`scripts/rules.py`](../../scripts/rules.py). Prefix `pack-agentic-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-agentic-loop-no-max-steps`     | error | `while True:` / `while 1:` in a file that mentions `agent`/`tool`/`step`, without a `break` and without a `step` counter check. |
| `pack-agentic-tool-no-timeout`       | warn  | Tool handler function (decorated with `@tool` / declared via `tool(...)`) without a timeout in its body. |
| `pack-agentic-destructive-no-confirm`| error | Tool definition with name containing `delete|drop|destroy|kill|send|publish|deploy` (case-insensitive) and no `confirm` parameter in its input schema. |
| `pack-agentic-no-step-trace`         | warn  | Bounded agent loop (`for step in range(...)`) without any logging/trace call inside. |

## Layer-2 self-check

```md
### Agent (pack-agentic)
- Loop has explicit MAX_STEPS bound and termination condition
- Repeated-state detection (avoid cycles)
- Token budget tracked, context compaction strategy in place
- Every tool call has timeout
- Every tool has explicit input schema + structured error result
- Destructive tools require confirm parameter or human-in-the-loop checkpoint
- Per-step trace logged with step number, action, latency, status
- Subagent depth bounded
```

## Limitations

- Regex-only — agent loop disguised as recursion / event-driven flow not detected.
- `tool-no-timeout`: looks for `timeout`/`wait_for` keyword inside function — sophisticated wrappers may bypass.
- `destructive-no-confirm`: tool name heuristic — destructive op named `archive` (synonyms) missed.
