# pack-ai-app

LLM application patterns — Anthropic / OpenAI / Gemini SDK, prompt engineering, RAG, cost tracking.

## Khi nào bật

- Service gọi LLM API (Anthropic SDK, OpenAI SDK, LangChain, ...)
- RAG pipeline với vector DB
- Có eval/benchmark cho prompt
- Cần track LLM cost / token usage

## Components

- `llm`: SDK calls, tool use, streaming
- `prompt`: prompt template, caching, versioning
- `rag`: retrieval + augmentation
- `embedding`: vector search, similarity

## Constraints highlights

- Prompt caching cho system prompt > ~1024 tokens (Anthropic best practice)
- Structured output qua schema (tool_choice, response_format)
- Token budget per request — không để runaway
- Không log raw user prompt (PII risk)
- Citation/grounding khi trả response từ RAG
- Eval harness có golden set, đo accuracy/cost trước khi ship prompt change

## Validator rules

| Rule | Severity |
|------|----------|
| `pack-ai-app-hardcoded-model-id` | warn |
| `pack-ai-app-log-raw-prompt` | error |
| `pack-ai-app-no-max-tokens` | warn |
| `pack-ai-app-missing-prompt-cache` | warn |

## Bật pack

```md
## Packs

- pack-ai-app
```
