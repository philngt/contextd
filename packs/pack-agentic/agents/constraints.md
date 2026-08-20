# pack-agentic — Constraints

## Agent Loop Safety (`pack-agentic-loop-safety`)

- **Loop budget bounded** — every autonomous loop has an explicit step/time/token budget chosen from task risk and runtime SLO. Khi chạm bất kỳ budget nào → checkpoint, escalate hoặc terminate; KHÔNG tight-loop forever.
- **Termination condition explicit** — clear exit criteria (task done, repeated state, error threshold). KHÔNG dựa duy nhất vào LLM tự dừng.
- **Repeated-state detection** — track recent (state hash) để break out of cycles.
- **Context reserve enforced** — track cumulative input/output tokens and reserve enough capacity for tool results, recovery, and final output. Compaction threshold comes from runtime config and measured workload, không hardcode một phần trăm chung.

## Tool Use (`pack-agentic-tool-use`)

- **Tool schema explicit** — name, description, input_schema, output_schema. Không generate schema runtime.
- **Tool execution has deadline** — every tool call receives a configured deadline/cancellation policy based on side effects and upstream SLO; timeout không phải một literal chung cho mọi tool.
- **Tool errors structured** — return `{error: {code, message}}`, không throw raw exception lên agent loop.
- **Idempotent tools when possible** — agent có thể retry safely. Document side-effect tools explicitly.

## Destructive Actions (`pack-agentic-destructive-actions`)

- **Effectful tools declare risk metadata** — destructive/irreversible/external actions require an approval policy or human checkpoint. Tool-name matching chỉ là static hint, không phải security boundary.
- **Confirmation default = false** — agent phải explicitly opt-in.
- **Bulk effects are bounded** — batch size, blast radius, dry-run support, and rollback/compensation follow configured policy for the target system.

## Multi-Agent Orchestration (`pack-agentic-orchestration`)

- **Subagent role explicit** — system prompt, tool subset, exit criteria documented.
- **Handoff protocol** — what data passes giữa agents, format chuẩn (vd JSON với schema).
- **Supervisor doesn't loop subagents indefinitely** — supervisor cũng có max-handoff limit.

## MCP Server (`pack-agentic-mcp-server`)

- **Protocol revision/SDK compatibility is explicit** — pin the supported MCP revision and migration tests. For the reviewed `2026-07-28` core, do not depend on legacy connection-session state; requests carry/derive the routing, capability and authorization context they need.
- **Extensions are opt-in capabilities** — Tasks, Skills, Apps or other extensions require explicit client/server support and fallback behavior; core support does not imply extension support.
- **Host-visible tool identity is collision-safe** — preserve the MCP tool name and apply host/server namespace where the client adapter requires it.
- **Resources có URI scheme rõ** — `{server}://{path}` consistent.
- **Server doesn't trust client** — validate input từ MCP client như public API.

## Observability (`pack-agentic-observability`)

- **Per-step trace required** — log each step's index, action class, latency, status, budget delta, and artifact references; redact prompt/tool payloads theo data policy.
- **Trace ID propagated** xuyên subagent handoff.
- **Cost per task tracked** — total tokens + tool latency aggregated.

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
