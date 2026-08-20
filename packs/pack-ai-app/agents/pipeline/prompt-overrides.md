# pack-ai-app — Prompt Overrides

## Self-Check append

```
### LLM App (pack-ai-app)
- Provider/model snapshot and endpoint policy read from versioned config
- Prompt template has explicit version/name
- Provider-supported output budget field set intentionally and covered by compatibility tests
- Prompt caching is provider/model/endpoint aware; only stable eligible prefixes are cached when measured useful
- No PII / raw user prompt in logs (metadata only)
- Structured output uses a provider-supported schema path with refusal/parse/fallback tests
- Grounded response cites source chunk/doc and exposes insufficient-evidence behavior
- Usage/cost telemetry maps provider fields into a stable internal schema, including cache fields when available
- Retry handles ambiguous completion/idempotency/billing and respects provider policy
```

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
