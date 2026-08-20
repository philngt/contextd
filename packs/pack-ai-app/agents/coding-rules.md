# pack-ai-app — Coding Rules

## SDK Usage

- Prefer a maintained provider SDK or workspace-approved gateway client; a raw HTTP adapter needs the same auth, retry, streaming, telemetry and compatibility tests.
- Pin SDK/client version in the dependency lock. Test SDK/provider upgrade on representative eval + contract fixtures.
- Initialize client tại startup, reuse instance — không tạo client per-request.

## Prompt Construction

- Separate stable policy/instructions from task/user/retrieved data so provenance, versioning and provider-eligible caching are explicit.
- Few-shot examples are versioned and selected by measured task coverage; static or dynamic selection both require eval evidence and contamination/privacy review.
- Include only relevant user/retrieved context, but never omit constraints or evidence merely to improve cache hit rate.

## Provider-aware Prompt Caching

- Read eligibility, minimums, lifetime, breakpoints/key semantics, data controls and pricing from the pinned provider/model/endpoint contract.
- Cache only stable reusable prefixes; prompt/source/model/tool-schema version changes invalidate the logical key.
- Normalize provider cache-write/read telemetry and compare measured hit rate, latency and cost. No universal threshold or savings claim.

## RAG

- Chunk size + overlap từ config, không hardcode.
- Embedding model + version pinned — re-embed toàn corpus khi đổi model.
- Choose lexical/vector/hybrid retrieval and reranking from corpus/query evals; `top_k`, filters and reranker budget are configuration, not a universal stack.
- Citation: include chunk ID + source doc trong response, render trên UI.

## Tool Use / Function Calling

- Tool schema explicit (name, description, input_schema). No dynamic schema generation tại runtime.
- Tool execution: idempotent khi possible, có timeout, có error handling rõ ràng.
- Tool result follows an explicit schema/content contract (including references or multimodal content when supported); unbounded free-form payloads do not flow directly into context.

## Streaming

- Use the pinned SDK's streaming path only when UX/moderation/structured-output behavior warrants it; otherwise non-streaming is valid.
- Backpressure is bounded; slow/disconnected clients trigger cancellation, coalescing or spill strategy instead of unbounded buffering.
- Cancel khi client disconnect — release upstream API connection.

## Error Handling

- Classify provider errors from the pinned endpoint contract: rate/temporary failures may retry with `Retry-After`/jitter; invalid/auth/policy errors fail fast; timeout/5xx with ambiguous completion require idempotency/dedup and billing-aware handling.
- Provider down: apply an approved failure policy (fail closed, queue, fallback model, or explicitly freshness-safe cached response) and record semantic differences.
- Never catch+swallow LLM error — surface tới observability.

## Testing

- Unit test prompt template rendering (input → expected string).
- Integration test với recorded fixtures (vd `vcr.py`, `nock`) — không hit live API trong CI.
- Golden eval trên dataset thực tế trước release.
