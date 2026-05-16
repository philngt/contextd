# pack-ai-app — Coding Rules

## SDK Usage

- Use official SDK (anthropic, openai, google-genai). Don't roll your own HTTP client.
- Pin SDK version trong `requirements.txt` / `package.json`. Test SDK upgrade trên golden set trước.
- Initialize client tại startup, reuse instance — không tạo client per-request.

## Prompt Construction

- System prompt: high-level role + rules + format spec. Static — cacheable.
- Few-shot examples: cố định trong code (versionable). Avoid dynamic example selection trừ khi có lý do mạnh.
- User message: chỉ chứa user input + minimal context. Keep dynamic content thấp để cache hit cao.

## Anthropic Prompt Caching

- `cache_control: {type: "ephemeral"}` ở cuối block bạn muốn cache (system, tool definitions, long context).
- Cache breakpoint thứ 4 tốn nhất — cân nhắc gộp.
- Tracking: `cache_creation_input_tokens` + `cache_read_input_tokens` từ response.

## RAG

- Chunk size + overlap từ config, không hardcode.
- Embedding model + version pinned — re-embed toàn corpus khi đổi model.
- Hybrid retrieval (BM25 + vector) cho recall tốt; rerank top-K bằng cross-encoder hoặc LLM.
- Citation: include chunk ID + source doc trong response, render trên UI.

## Tool Use / Function Calling

- Tool schema explicit (name, description, input_schema). No dynamic schema generation tại runtime.
- Tool execution: idempotent khi possible, có timeout, có error handling rõ ràng.
- Tool result format: structured JSON, không free-form text.

## Streaming

- Use SDK streaming API (`messages.stream()`), không poll.
- Backpressure: buffer client, không drop event.
- Cancel khi client disconnect — release upstream API connection.

## Error Handling

- Distinguish: rate limit (429) → backoff retry; 5xx → retry với jitter; 4xx (model error) → fail fast log.
- Provider down: degrade gracefully (fallback model hoặc cached response).
- Never catch+swallow LLM error — surface tới observability.

## Testing

- Unit test prompt template rendering (input → expected string).
- Integration test với recorded fixtures (vd `vcr.py`, `nock`) — không hit live API trong CI.
- Golden eval trên dataset thực tế trước release.
