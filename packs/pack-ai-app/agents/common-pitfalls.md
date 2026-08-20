# pack-ai-app — Top 10 Common Pitfalls

Anti-pattern lặp lại với LLM app. Additive trên [constraints.md](constraints.md).

## P01 — Log raw prompt / user input
- **NG**: `logger.info(f"prompt={prompt}")`.
- **OK**: log `len(prompt)`, hash, request_id; raw body chỉ vào secure store.
- **Why**: PII leak, secret exposure, compliance fail.
- **Detect**: Layer-1 `pack-ai-app-log-raw-prompt` (regex heuristic).
- **Severity**: error

## P02 — Hardcoded model ID
- **NG**: `model="claude-3-5-sonnet-20240620"` rải khắp code.
- **OK**: `model=config.LLM_MODEL`, version qua env.
- **Why**: model deprecation/snapshot change becomes a repo-wide edit and cannot be evaluated or rolled back centrally.
- **Detect**: Layer-1 `pack-ai-app-hardcoded-model-id` (regex heuristic).
- **Severity**: warn

## P03 — Unbounded `max_tokens`
- **NG**: gọi API không set `max_tokens` → response 4k token mặc định.
- **OK**: set explicit dựa trên use case; alert nếu vượt.
- **Why**: cost spike, timeout.
- **Detect**: Layer-1 `pack-ai-app-no-max-tokens` accepts current max-output parameter variants; Layer-2 checks external generation config.
- **Severity**: warn

## P04 — Không có provider-aware cache policy
- **NG**: long static context luôn gửi lại, hoặc cache content thay đổi/nhạy cảm mà không xét provider eligibility và retention policy.
- **OK**: version stable blocks, check current provider/model eligibility, track cache metrics, và disable cache khi data policy yêu cầu.
- **Why**: cache behavior, minimums, retention, pricing và data controls khác nhau theo provider/model/endpoint.
- **Detect**: Layer-1 `pack-ai-app-missing-prompt-cache` only for long Anthropic literals; Layer-2 verifies provider contract, invalidation, telemetry và data policy.
- **Severity**: warn

## P05 — Regex parse structured output
- **NG**: `re.search(r"answer: (.*)", llm_out)`.
- **OK**: tool_use / response_format JSON + schema validate.
- **Why**: format drift, hallucination → parse fail.
- **Detect**: Layer-2 — output JSON dùng `tool_choice|response_format`.
- **Severity**: error

## P06 — Retry không jitter/backoff
- **NG**: `while True: try: call() except: continue`.
- **OK**: exponential + jitter; max attempts; circuit breaker.
- **Why**: tight-loop trên 429 → ban; thundering herd.
- **Detect**: Layer-2 — retry library / decorator.
- **Severity**: error

## P07 — Không trace token usage / cost
- **NG**: chỉ trả response, không log `usage.input_tokens|output_tokens|cache_read`.
- **OK**: emit metric per call: model, tokens, cost, latency, request_id.
- **Why**: cost spike không detect; không attribute per feature.
- **Detect**: Layer-2 — wrapper SDK có metric emit.
- **Severity**: warn

## P08 — RAG response không cite source
- **NG**: LLM trả lời từ retrieved chunks nhưng không nhắc source.
- **OK**: response kèm `sources: [chunk_id|doc_id]`; UI hiển thị citation.
- **Why**: hallucination silent; user trust giảm.
- **Detect**: Layer-2 — RAG handler có cite field trong schema.
- **Severity**: error

## P09 — Không golden eval trước merge prompt
- **NG**: sửa system prompt rồi deploy thẳng prod.
- **OK**: golden test set (accuracy, p95 latency, cost) → A/B vs old prompt → CI gate.
- **Why**: prompt regression silent, khó rollback.
- **Detect**: Layer-2 — repo có `evals/golden-tasks/`.
- **Severity**: error

## P10 — Provider lock-in (no abstraction)
- **NG**: import `anthropic` rải khắp business code.
- **OK**: thin LLM client interface; provider swap = đổi config.
- **Why**: vendor outage không failover được; cost optimization khó.
- **Detect**: Layer-2 — domain code không import SDK trực tiếp.
- **Severity**: info

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 log-prompt | `pack-ai-app-log-raw-prompt` | ✓ |
| P02 hardcoded-model | `pack-ai-app-hardcoded-model-id` | ✓ |
| P03 max-output | `pack-ai-app-no-max-tokens` | ✓ |
| P04 cache | `pack-ai-app-missing-prompt-cache` | ✓ |
| P05 regex-parse | — | ✓ |
| P06 retry | — | ✓ |
| P07 cost-trace | — | ✓ |
| P08 cite | — | ✓ |
| P09 eval | — | ✓ |
| P10 lockin | — | ✓ |
