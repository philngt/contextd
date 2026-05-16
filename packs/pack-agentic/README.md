# pack-agentic

Agent loop / tool use / multi-agent orchestration / MCP server patterns.

## Khi nào bật

- Build agent autonomous loop (ReAct, planner-executor, critic-actor)
- LLM tool use / function calling intensive
- Multi-agent system (subagent handoff, supervisor)
- MCP server provider/consumer
- Human-in-the-loop checkpoint flow

## Components

- `agent`: agent loop control, state, termination
- `tool`: tool definition, schema, execution
- `mcp`: MCP server / client patterns
- `orchestration`: multi-agent coordination

## Constraints highlights

- Agent loop có max steps + termination condition rõ ràng
- Tool call có timeout, error handling, idempotent khi possible
- Destructive tool (delete/drop/send) cần human confirm hoặc explicit confirmation parameter
- Context window budget tracked — compact khi gần giới hạn
- Trace mỗi agent step để observable + debuggable
- Tool result format structured (JSON), không free-form text

## Validator rules

| Rule | Severity |
|------|----------|
| `pack-agentic-loop-no-max-steps` | error |
| `pack-agentic-tool-no-timeout` | warn |
| `pack-agentic-destructive-no-confirm` | error |
| `pack-agentic-no-step-trace` | warn |

## Bật pack

```md
## Packs

- pack-agentic
```

Thường dùng kết hợp với `pack-ai-app` (LLM SDK base).
