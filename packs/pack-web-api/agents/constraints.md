# pack-web-api — Constraints

Hard rules cho REST/GraphQL/gRPC API. Additive trên engine constraints.

## API Boundary

- **Validate input at the boundary** — every endpoint validates payload + query + header before touching business logic. Use framework validation (`@Valid`, Pydantic, Zod, schema), not ad-hoc `if` checks.
- **Error response has a contract** — never return raw exception message or stack trace to client. Map exceptions to structured error response (`{code, message, requestId}`).
- **Auth check precedes business logic** — guard with middleware/interceptor/decorator, not inline `if user.role == ...` scattered across handlers.

## Idempotency

- **Mutating endpoints (POST/PUT/PATCH/DELETE) MUST be idempotent** when client retry is plausible (mobile/offline/3rd-party webhook). Either: (a) idempotency key header + dedup store, (b) upsert semantics on the underlying record.
- **GET MUST be safe** — no side-effects on read paths. No "track-and-update last-seen" type writes inline with GET.

## Versioning

- **Do not break a published API contract** — version in path/header before changing shape. Versioning strategy chosen per workspace, recorded in `{ws}/decisions/`.
- **Do not remove fields** from response without deprecation period documented.

## Information Leak

- **Do not log raw request body** containing PII/secrets. Mask field-by-field per data classification.
- **Do not include stack traces** in 5xx responses sent to public clients. Log with correlationId, return only `{code: "INTERNAL_ERROR", requestId}`.
- **Do not expose internal endpoint paths** (admin, debug, actuator) through public ingress without explicit allow-list.

## Rate Limiting & Abuse

- **Public endpoints have rate limit** — per IP/per token. Limit values from config, not hardcoded.
- **Heavy endpoints have circuit breaker** to downstream — avoid thundering herd on outage.
