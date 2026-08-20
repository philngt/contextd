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

- Provider-aware prompt caching cho stable/eligible context, có invalidation + telemetry
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

## When not to enable

- Huấn luyện/fine-tune model hoặc ML pipeline thuần túy; pack này chỉ quản lý application runtime quanh model API.
- Agent loop, destructive tool, handoff hoặc MCP orchestration; dùng thêm `pack-agentic`.

## Retrieval behavior

Routing tách `llm`, `prompt`, `rag`, và `embedding`. Keyword ưu tiên artifact/API cụ thể (`system prompt`, `vector store`, `embedding model`) để không biến mọi task có từ “prompt” hoặc “retrieval” thành full AI context.

## Verification

```bash
contextd pack-validate --pack pack-ai-app --format text
contextd context "Review grounded RAG response contract" --preview --format json
python scripts/validate.py --file <llm-fixture> --workspace <workspace-with-pack>
```

Standards baseline được review ngày `2026-08-20`: [OpenAI request IDs and production debugging](https://platform.openai.com/docs/api-reference/debugging-requests), [OpenAI data controls by endpoint](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint). Provider behavior phải được pin trong workspace contract và eval lại khi đổi model/endpoint.
