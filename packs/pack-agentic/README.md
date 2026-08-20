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

- Agent loop có step/time/token/cost budget + termination condition rõ ràng
- Tool call có deadline/cancellation policy, error handling, idempotent khi possible
- Destructive tool (delete/drop/send) cần human confirm hoặc explicit confirmation parameter
- Context reserve tracked — compact kèm source IDs/hashes và reload plan
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

## When not to enable

- Task chỉ gọi một LLM API hoặc làm RAG nhưng không có agent loop/tool runtime; dùng `pack-ai-app`.
- Task chỉ phân công công việc cho coding agent, không xây orchestration trong sản phẩm.

## Retrieval behavior

Các signal cụ thể như `agent loop`, `tool call`, `MCP server`, hoặc `multi-agent handoff` mới kích hoạt component tương ứng. Pack không dùng từ đơn quá rộng như `agent` hay `tool`, nhằm tránh nạp guardrail runtime vào task không liên quan.

## Verification

```bash
contextd pack-validate --pack pack-agentic --format text
contextd context "Review bounded MCP tool loop" --preview --format json
python scripts/validate.py --file <agent-fixture> --workspace <workspace-with-pack>
```

Standards baseline được review ngày `2026-08-20`: [MCP specification 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) và [MCP TypeScript SDK v2](https://ts.sdk.modelcontextprotocol.io/v2/). Pin protocol/SDK version trong workspace contract thay vì giả định “latest”; đặc biệt không áp lifecycle/session assumptions của revision cũ lên protocol core mới.
