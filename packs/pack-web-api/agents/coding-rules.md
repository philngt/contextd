# pack-web-api — Coding Rules

## Endpoint Layer

- Keep transport parsing/auth/error mapping separate from domain decisions; a vertical slice may co-locate code, but its boundary remains testable.
- Map domain failures through a centralized/consistent transport error contract; local handling is allowed when the endpoint owns recovery semantics.
- Serialize an explicit response field contract. Do not expose persistence/domain objects implicitly or rely on accidental serializer defaults.

## Validation

- Use the validator supported by the pinned framework/runtime (for example Jakarta Validation, Pydantic, Zod/JSON Schema, or protobuf validation).
- Validate every consumed untrusted body/query/path/header field; untouched transport metadata does not need fake checks.
- Custom validator cho business rule, không nhồi vào DTO `@AssertTrue` complex.

## Error Handling

- Define error catalog tại 1 chỗ (enum/constant), reference từ handler. Không dùng raw string `"NOT_FOUND"` rải rác.
- 4xx → user-actionable + actionable error code; 5xx → log + opaque response (request ID only).
- Never `catch (Exception)` rồi swallow — re-throw, log, hoặc map sang domain exception cụ thể.

## Auth & Authorization

- Authentication tại middleware/filter chain, không trong handler.
- Authorization check explicit per endpoint (annotation `@PreAuthorize`, `@RequiresRole`, hoặc decorator) — không inline `if user.role`.
- Token validation follows issuer/profile contract: allowed algorithm/key, issuer, audience/resource, expiry/not-before, token type and revocation/session rules where applicable. Reject before domain access.

## Pagination & Filtering

- Chọn cursor/keyset hoặc offset theo consistency, ordering, random-access và total-count contract; mọi list có bounded page size.
- Filter params validated whitelist — không cho phép arbitrary field/operator (SQL injection / mass assignment).
- Default page size + max page size từ config.

## Observability

- Correlation ID propagated từ inbound header → log + downstream calls.
- Structured access telemetry follows data policy: route template, method, status, latency, correlation/trace ID and privacy-safe principal/tenant signal when justified. Raw body or identifiers are not enabled by a generic debug switch.
- Metrics include traffic, failures and SLO-relevant latency/distribution; choose percentiles/windows with enough samples rather than hardcode p50/p95/p99 everywhere.

## Domain Decision Lens

Use within this pack's scope; existing constraints remain authoritative.

- **Observe:** Inspect caller identity, authorization, resource/action, request/response schema, durable effects, retry/deadline budget, and the workspace API contract.
- **Mechanism:** A client timeout does not reveal whether the server committed an effect. Repeating a request can duplicate work unless request identity and the effect boundary support the declared retry semantics.
- **Choose:** Choose validation and authorization at the trusted boundary, an explicit idempotency/status strategy for uncertain outcomes, and bounded retries for suitable failures. Select protocol and sync/async behavior from client needs.
- **Exception:** An accepted asynchronous request is not a completed outcome. A syntactically read-only operation may still be expensive; method names alone do not justify unlimited retries or access.
- **Verify:** Exercise duplicate/concurrent requests, invalid input, cross-resource denial, timeout after commit, and recovery. Compare durable effects with response/error contracts and trace receipts.
- **Stop:** Pause a material contract change when ownership, compatibility, authorization, or retry semantics are unresolved. Do not mask an unknown outcome with a successful-looking response.
