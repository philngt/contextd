# pack-agentic — Constraints

## Agent Loop Safety

- **Max steps bounded** — every autonomous loop has an explicit step limit (vd `MAX_STEPS = 50`). Khi đạt limit → escalate hoặc terminate, KHÔNG tight-loop forever.
- **Termination condition explicit** — clear exit criteria (task done, repeated state, error threshold). KHÔNG dựa duy nhất vào LLM tự dừng.
- **Repeated-state detection** — track recent (state hash) để break out of cycles.
- **Token budget enforced** — track cumulative input + output tokens; compact context khi vượt threshold (typically 70% context window).

## Tool Use

- **Tool schema explicit** — name, description, input_schema, output_schema. Không generate schema runtime.
- **Tool execution has timeout** — every tool call wrapped trong timeout (vd 30s default, override per tool).
- **Tool errors structured** — return `{error: {code, message}}`, không throw raw exception lên agent loop.
- **Idempotent tools when possible** — agent có thể retry safely. Document side-effect tools explicitly.

## Destructive Actions

- **Destructive tools require confirmation** — tool name chứa `delete|drop|destroy|send|publish|deploy|kill` MUST have `confirm: bool` param hoặc human-in-the-loop checkpoint.
- **Confirmation default = false** — agent phải explicitly opt-in.
- **No mass destructive ops** — batch delete/send giới hạn N items per tool call.

## Multi-Agent Orchestration

- **Subagent role explicit** — system prompt, tool subset, exit criteria documented.
- **Handoff protocol** — what data passes giữa agents, format chuẩn (vd JSON với schema).
- **Supervisor doesn't loop subagents indefinitely** — supervisor cũng có max-handoff limit.

## MCP Server

- **Tool name namespaced** — prefix `{server-name}__{tool}` để tránh collision.
- **Resources có URI scheme rõ** — `{server}://{path}` consistent.
- **Server doesn't trust client** — validate input từ MCP client như public API.

## Observability

- **Per-step trace required** — log mỗi agent step: step_n, action (tool call / message), latency, status. Persist tới structured store.
- **Trace ID propagated** xuyên subagent handoff.
- **Cost per task tracked** — total tokens + tool latency aggregated.
