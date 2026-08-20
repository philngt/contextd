# pack-agentic — Coding Rules

## Loop Structure

- Use a budget object (`steps`, `deadline`, `tokens`, `cost`) and explicit termination checks. A bounded `for` loop is one implementation, không phải contract duy nhất.
- State machine pattern khi flow phức tạp: `PLAN → EXECUTE → CRITIQUE → FINALIZE`.
- Idempotent step — replay step n từ checkpoint không phá state.

## Tool Definition

- One file per tool group; co-locate schema + handler.
- Pydantic / Zod schema cho input validation tại boundary.
- Tool handler signature: `(input: ValidatedInput, context: AgentContext) -> ToolResult`. Inject context, không global.

## Tool Execution

- Wrap tool call trong timeout: `asyncio.wait_for(tool(input), timeout=TOOL_TIMEOUT)`.
- Catch + log + return structured error — never let exception escape into agent loop unstructured.
- Tool result size follows a configured context budget; preserve a content hash/artifact reference when truncating so the agent can retrieve the full result intentionally.

## MCP Compatibility

- Record protocol revision, SDK/package version and transport in the workspace contract and compatibility fixtures.
- Keep request handling stateless unless the pinned protocol/extension explicitly introduces a durable handle; never hide correctness-critical state only in one process connection.
- Treat capability/extension negotiation, authorization and user consent as request-boundary behavior with negative tests.

## Memory & Context

- Runtime memory: current task state, recent turns, pending approvals, and tool-result references; bounded by the task budget.
- Long-term memory: canonical knowledge/artifacts with provenance, lifecycle state, and replacement links. Stale nodes remain addressable for history but are penalized or excluded from normal retrieval.
- Compaction strategy explicit: preserve constraints, decisions, unresolved work, source IDs/hashes, and a reload plan; do not rely on a lossy prose summary alone.

## Subagent Pattern

- Spawn subagent qua dedicated `spawn_subagent(role, task, tools)` API — không pass parent's full context.
- Subagent returns structured result tới parent; parent decides next step.
- No unbounded nested delegation — track depth, handoff count, and remaining budget; limits come from orchestration policy.

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
