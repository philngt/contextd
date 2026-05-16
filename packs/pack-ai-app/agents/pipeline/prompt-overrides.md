# pack-ai-app — Prompt Overrides

## Self-Check append

```
### LLM App (pack-ai-app)
- Model ID read from config (not hardcoded)
- Prompt template has explicit version/name
- max_tokens set explicitly per LLM call
- Long static system prompt uses cache_control
- No PII / raw user prompt in logs (metadata only)
- Structured output via schema (tool_choice / response_format)
- RAG response cites source chunk/doc
- Token usage logged per call (input, output, cache_read)
```
