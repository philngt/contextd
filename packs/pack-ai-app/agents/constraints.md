# pack-ai-app — Constraints

## Prompt & Context

- **Prompt versioning** — every system/user prompt template lives in code with a version tag (constant name, file path, hoặc semver). KHÔNG inline magic-string prompt scattered.
- **Prompt cache cho long static context** — Anthropic SDK: `cache_control` cho system prompt > ~1024 tokens. Cache hit rate tracked.
- **Token budget enforced** — `max_tokens` set explicitly per call. Không để default unbounded.
- **No PII in logs** — never `log.info(prompt)` / `print(prompt)` containing raw user input. Mask hoặc log only metadata (length, hash, request ID).

## Model & Provider

- **Model ID from config**, not hardcoded. Easy to upgrade Opus 4.6 → 4.7 hoặc swap provider.
- **Retry với exponential backoff** + circuit breaker on provider 5xx / rate limit. Don't tight-loop.
- **Streaming preferred** for user-facing response > 1s; non-streaming chỉ cho batch/job.

## Structured Output

- **Schema validation** cho output expected là JSON/structured. Use `tool_choice` (Anthropic) / `response_format` (OpenAI) / function calling, KHÔNG parse text với regex.
- **Hallucination guardrail** — response từ RAG MUST cite source (chunk ID / doc ID); response without grounding flagged.

## Eval

- **Golden test set** trước khi merge prompt change. Min metrics: accuracy on golden tasks, p95 latency, p95 cost.
- **A/B compare** old prompt vs new prompt trên cùng golden set.
- **No prompt deploy without eval pass** — CI gate.

## Cost & Observability

- **Token usage logged per request** — input tokens, output tokens, cache_hit_tokens, model. Aggregate per user/feature/day.
- **Cost alarm** khi spike (>2x baseline).
- **Trace** mỗi LLM call: prompt hash, model, latency, status. KHÔNG log raw prompt body.
