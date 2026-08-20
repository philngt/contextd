# pack-ai-app — Constraints

## Prompt & Context (`pack-ai-app-prompt-context`)

- **Prompt versioning** — every system/user prompt template lives in code with a version tag (constant name, file path, hoặc semver). KHÔNG inline magic-string prompt scattered.
- **Provider-aware cache policy** — enable prompt caching only for stable, eligible content according to the configured provider/model contract; record cache read/write tokens and invalidate on prompt/source version change. Không hardcode một ngưỡng token dùng cho mọi provider.
- **Output budget enforced** — set an explicit application-level output ceiling using the provider's current parameter (`max_tokens`, `max_completion_tokens`, `max_output_tokens`, or equivalent).
- **No PII in logs** — never `log.info(prompt)` / `print(prompt)` containing raw user input. Mask hoặc log only metadata (length, hash, request ID).

## Model & Provider (`pack-ai-app-model-provider`)

- **Model ID/snapshot from config**, not scattered literals. Pin production snapshots where supported and run evals before model/provider changes.
- **Retry policy is provider/operation aware** — retry only documented transient outcomes, respect `Retry-After`, cap attempts/deadline and handle ambiguous completion/billing/idempotency. Circuit breaking/load shedding follows measured failure mode; never tight-loop.
- **Delivery mode is intentional** — choose streaming/non-streaming from UX, moderation, retry, and structured-output requirements; record the trade-off instead of using a global latency threshold.

## Structured Output (`pack-ai-app-structured-output`)

- **Schema validation** cho output expected là structured. Use the pinned provider's supported structured-output/tool schema path, validate locally, and define refusal/truncation/parse-failure behavior; text parsing is fallback only with fixtures and failure limits.
- **Grounding contract** — evidence-backed/RAG response cites source IDs and distinguishes supported facts, inference, and insufficient evidence. Tasks that intentionally do not require grounding must declare that mode.

## Eval (`pack-ai-app-eval`)

- **Representative eval set** trước khi merge prompt/model/retrieval change. Metrics and slices derive from the task contract (quality/safety/grounding/latency/cost as applicable), with sample size and uncertainty.
- **A/B compare** old prompt vs new prompt trên cùng golden set.
- **No prompt deploy without eval pass** — CI gate.

## Cost & Observability (`pack-ai-app-cost-observability`)

- **Usage telemetry normalized per request** — provider/model/endpoint, input/output and cache/reasoning/tool usage fields when available; preserve raw provider request ID for debugging and aggregate only on privacy-approved dimensions.
- **Cost alarm** uses a configured budget/SLO and workload-normalized baseline; threshold ownership and response action must be explicit.
- **Trace** mỗi LLM call: prompt hash, model, latency, status. KHÔNG log raw prompt body.

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
