# pack-ai-app — Validator Rules

Layer-1 rule. Implement: [`scripts/rules.py`](../../scripts/rules.py). Prefix `pack-ai-app-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-ai-app-hardcoded-model-id`   | warn  | Literal model ID (`claude-...`, `gpt-...`, `gemini-...`) in code outside config/test files. |
| `pack-ai-app-log-raw-prompt`       | error | Log/print call passing a variable named `prompt`/`system_prompt`/`messages` — risk of leaking PII. |
| `pack-ai-app-no-max-tokens`        | warn  | LLM call without a visible provider output ceiling (`max_tokens`, `max_completion_tokens`, `max_output_tokens`, or equivalent generation config). |
| `pack-ai-app-missing-prompt-cache` | warn  | Long Anthropic prompt heuristic without a visible cache policy; requires review of current eligibility, data controls, and invalidation. |

## Layer-2 self-check

```md
### LLM App (pack-ai-app)
- Model ID read from config, not hardcoded
- Prompt template versioned in code with explicit name/path
- Application output ceiling explicitly set with the provider's current parameter
- Long stable prompt has an explicit provider-aware cache/no-cache decision
- No PII / raw user prompt in logs — log metadata only
- Structured output uses schema (tool_choice / response_format), not regex parsing
- RAG response cites source chunk
- Eval set passes before prompt change merges
```

## Limitations

- Regex-only — model ID pulled from constant in another file is invisible.
- `log-raw-prompt`: catches obvious patterns; sophisticated f-string embeds may bypass.
- `missing-prompt-cache`: file-scoped — cache_control may live in another module (false positive).
