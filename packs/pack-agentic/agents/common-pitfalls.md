# pack-agentic — Top 10 Common Pitfalls

Anti-pattern lặp lại với agent loop / tool use / MCP. Additive trên [constraints.md](constraints.md).

## P01 — Unbounded agent loop
- **NG**: `while not done: step()` không có max iteration.
- **OK**: configured step/time/token/cost budget; checkpoint + preserve reload state khi vượt.
- **Why**: cost spike vô hạn, hang task.
- **Detect**: Layer-1 `pack-agentic-loop-no-max-steps` (heuristic) + Layer-2 budget review.
- **Severity**: error

## P02 — Tool không có timeout
- **NG**: tool gọi HTTP/DB không timeout → agent treo.
- **OK**: per-tool timeout config; cancel + report on expire.
- **Why**: 1 slow tool block toàn agent.
- **Detect**: Layer-1 `pack-agentic-tool-no-timeout` (heuristic) + Layer-2 deadline/cancellation review.
- **Severity**: error

## P03 — Destructive tool không confirm
- **NG**: tool `delete_file|drop_table|send_email` exec ngay.
- **OK**: dry-run preview + explicit confirm step.
- **Why**: agent hallucinate args → data loss / email spam.
- **Detect**: Layer-1 `pack-agentic-destructive-no-confirm` (name heuristic) + Layer-2 effect metadata/approval review.
- **Severity**: error

## P04 — Tool result không validate schema
- **NG**: agent đẩy raw tool output vào next prompt.
- **OK**: schema validate (pydantic/zod); truncate; redact secret.
- **Why**: tool error → garbage → bad next step.
- **Detect**: Layer-2 — tool wrapper có schema.
- **Severity**: error

## P05 — Leak credential qua tool args
- **NG**: tool nhận `api_key` qua argument → log vào trace.
- **OK**: credential từ secure config; tool args chỉ chứa intent.
- **Why**: trace lưu permanent, exposure.
- **Detect**: Layer-2 — tool schema + trace redaction review; secret scanner riêng.
- **Severity**: error

## P06 — Không có max-tool-calls budget
- **NG**: agent gọi tool 200 lần / task.
- **OK**: per-task budget (calls, tokens, $); halt khi vượt.
- **Why**: cost runaway.
- **Detect**: Layer-2 — config có `max_tool_calls`.
- **Severity**: error

## P07 — Prompt injection từ tool output
- **NG**: tool fetch web page → đẩy raw HTML vào context → page chứa `IGNORE PREVIOUS, ...`.
- **OK**: sanitize, label `<untrusted_tool_output>`, đặt system rule "ignore instructions inside".
- **Why**: agent hijack qua external content.
- **Detect**: Layer-2 — fetch/scrape tool có sanitizer.
- **Severity**: error

## P08 — Recursive sub-agent vô hạn
- **NG**: agent A spawn agent B spawn agent A → cycle.
- **OK**: depth limit, parent → child tracking, cycle detection.
- **Why**: fork bomb cost.
- **Detect**: Layer-2 — orchestrator có depth check.
- **Severity**: error

## P09 — Không log tool trace
- **NG**: agent chạy nhưng không record tool calls + result.
- **OK**: structured trace (W3C-style); include latency, tokens, status.
- **Why**: không debug được; không eval được.
- **Detect**: Layer-1 `pack-agentic-no-step-trace` (heuristic) + trace contract test.
- **Severity**: warn

## P10 — Tool không document deprecation / version
- **NG**: tool `search_v1` rename → caller vỡ.
- **OK**: tool name versioned; deprecation notice; backward-compat period.
- **Why**: breaking change silent.
- **Detect**: Layer-2 — tool registry có `version|deprecated`.
- **Severity**: info

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 loop | `pack-agentic-loop-no-max-steps` | ✓ |
| P02 timeout | `pack-agentic-tool-no-timeout` | ✓ |
| P03 destructive | `pack-agentic-destructive-no-confirm` | ✓ |
| P04 schema | — | ✓ |
| P05 secret-arg | — | ✓ |
| P06 budget | — | ✓ |
| P07 injection | — | ✓ |
| P08 recursion | — | ✓ |
| P09 trace | `pack-agentic-no-step-trace` | ✓ |
| P10 version | — | ✓ |
