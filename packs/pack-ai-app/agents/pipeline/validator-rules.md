# pack-ai-app — Validator Rules

Layer-1 rule. Implement: [`scripts/rules.py`](../../scripts/rules.py). Prefix `pack-ai-app-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-ai-app-hardcoded-model-id`   | warn  | Literal model ID (`claude-...`, `gpt-...`, `gemini-...`) in code outside config/test files. |
| `pack-ai-app-log-raw-prompt`       | error | Log/print call passing a variable named `prompt`/`system_prompt`/`messages` — risk of leaking PII. |
| `pack-ai-app-no-max-tokens`        | warn  | `messages.create(...)` / `chat.completions.create(...)` call without `max_tokens=` argument. |
| `pack-ai-app-missing-prompt-cache` | warn  | Long system message string literal (>800 chars) without `cache_control` referenced anywhere in the same file (Anthropic best practice). |

## Layer-2 self-check

```md
### LLM App (pack-ai-app)
- Model ID read from config, not hardcoded
- Prompt template versioned in code with explicit name/path
- max_tokens explicitly set per LLM call (no unbounded)
- Long system prompt uses cache_control (Anthropic) for cost
- No PII / raw user prompt in logs — log metadata only
- Structured output uses schema (tool_choice / response_format), not regex parsing
- RAG response cites source chunk
- Eval set passes before prompt change merges
```

## Limitations

- Regex-only — model ID pulled from constant in another file is invisible.
- `log-raw-prompt`: catches obvious patterns; sophisticated f-string embeds may bypass.
- `missing-prompt-cache`: file-scoped — cache_control may live in another module (false positive).
