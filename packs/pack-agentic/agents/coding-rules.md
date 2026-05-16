# pack-agentic — Coding Rules

## Loop Structure

- Use bounded loop (`for step in range(MAX_STEPS):`) thay vì `while True:`. Easier to reason about + harder to forget exit.
- State machine pattern khi flow phức tạp: `PLAN → EXECUTE → CRITIQUE → FINALIZE`.
- Idempotent step — replay step n từ checkpoint không phá state.

## Tool Definition

- One file per tool group; co-locate schema + handler.
- Pydantic / Zod schema cho input validation tại boundary.
- Tool handler signature: `(input: ValidatedInput, context: AgentContext) -> ToolResult`. Inject context, không global.

## Tool Execution

- Wrap tool call trong timeout: `asyncio.wait_for(tool(input), timeout=TOOL_TIMEOUT)`.
- Catch + log + return structured error — never let exception escape into agent loop unstructured.
- Tool result size limited (vd 10KB) — truncate với indicator nếu lớn hơn.

## Memory & Context

- Short-term memory: conversation history, capped (sliding window hoặc summary).
- Long-term memory: vector store / DB, có TTL hoặc archive.
- Compaction strategy explicit: keep system + last K turns + summary of dropped turns.

## Subagent Pattern

- Spawn subagent qua dedicated `spawn_subagent(role, task, tools)` API — không pass parent's full context.
- Subagent returns structured result tới parent; parent decides next step.
- No nested subagent infinite recursion — track depth, max 3 levels typical.

## Human-in-the-Loop

- Checkpoint trước destructive ops: `await request_approval(action)`. Block agent loop cho đến khi human respond.
- Timeout cho approval — fall back tới safe default (cancel) nếu không respond.
- Audit log mỗi approval/rejection với actor + timestamp.

## Error Handling

- Tool failure → log + retry (idempotent only) up to N times → escalate.
- Loop crash (unhandled exception) → save state + error, allow resume.
- LLM provider down → fallback model hoặc graceful degrade.

## Testing

- Mock LLM với scripted responses cho deterministic unit test.
- Replay test: record real loop trace, assert behavior consistent on replay.
- Eval golden tasks: agent solves predefined task within step+cost budget.
