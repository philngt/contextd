# pack-web-api — Constraints

Hard rules cho REST/GraphQL/gRPC API. Additive trên engine constraints.

## API Boundary (`pack-web-api-boundary`)

- **Validate consumed untrusted input at the boundary** — payload/query/path/header fields used by the endpoint get schema + semantic validation before business logic; do not require meaningless validation for untouched headers.
- **Error response has a contract** — never return raw exception message or stack trace to client. Map exceptions to structured error response (`{code, message, requestId}`).
- **Auth check precedes business logic** — guard with middleware/interceptor/decorator, not inline `if user.role == ...` scattered across handlers.

## Idempotency (`pack-web-api-idempotency`)

- **Retry behavior for mutations is explicit** when clients/intermediaries may retry. Use an idempotency key + durable outcome record, conditional request/version, natural operation ID, upsert/state-machine semantics, or an explicit non-retryable contract with reconciliation. Handle ambiguous completion, retention and concurrent duplicates.
- **GET MUST be safe** — no side-effects on read paths. No "track-and-update last-seen" type writes inline with GET.

## Versioning (`pack-web-api-versioning`)

- **Do not break a published API contract silently** — prefer compatible evolution; when a real break is required, use the workspace version/migration strategy (path/header/media/schema revision as appropriate) and record it in `{ws}/decisions/`.
- **Do not remove fields** from response without deprecation period documented.

## Information Leak (`pack-web-api-information-leak`)

- **Do not log raw request body** containing PII/secrets. Mask field-by-field per data classification.
- **Do not include stack traces** in 5xx responses sent to public clients. Log with correlationId, return only `{code: "INTERNAL_ERROR", requestId}`.
- **Do not expose internal endpoint paths** (admin, debug, actuator) through public ingress without explicit allow-list.

## Rate Limiting & Abuse (`pack-web-api-abuse-controls`)

- **Abusable/costly endpoints have an explicit abuse-control policy** — choose quota/rate/concurrency limits and identity key from threat/workload evidence; values from config.
- **Downstream failure strategy is explicit** — timeout, retry, concurrency cap, circuit breaker or load shedding chosen from idempotency and failure-mode analysis, không bắt buộc một pattern cho mọi endpoint.

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
