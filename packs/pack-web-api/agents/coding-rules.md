# pack-web-api — Coding Rules

## Endpoint Layer

- Controller/handler methods stay thin — delegate business logic to service. No DB query / external call inline trong controller.
- Map domain exceptions to HTTP status via global exception handler (`@ControllerAdvice`, error middleware), not try/catch trong từng handler.
- Response DTO ≠ entity. Never return JPA/ORM entity directly — use mapper.

## Validation

- Use framework validation tại boundary: `@Valid` + JSR-380 (Java), Pydantic v2 (Python), Zod (TS), proto validation (gRPC).
- Validate query params + path vars + headers, không chỉ body.
- Custom validator cho business rule, không nhồi vào DTO `@AssertTrue` complex.

## Error Handling

- Define error catalog tại 1 chỗ (enum/constant), reference từ handler. Không dùng raw string `"NOT_FOUND"` rải rác.
- 4xx → user-actionable + actionable error code; 5xx → log + opaque response (request ID only).
- Never `catch (Exception)` rồi swallow — re-throw, log, hoặc map sang domain exception cụ thể.

## Auth & Authorization

- Authentication tại middleware/filter chain, không trong handler.
- Authorization check explicit per endpoint (annotation `@PreAuthorize`, `@RequiresRole`, hoặc decorator) — không inline `if user.role`.
- Token validation: signature + expiry + audience. Reject early.

## Pagination & Filtering

- Cursor-based pagination cho large list, offset chỉ cho UI có total count rõ.
- Filter params validated whitelist — không cho phép arbitrary field/operator (SQL injection / mass assignment).
- Default page size + max page size từ config.

## Observability

- Correlation ID propagated từ inbound header → log + downstream calls.
- Log mỗi request: method, path, status, latency, userId (nếu auth). KHÔNG log body trừ debug mode.
- Metrics: rps, p50/p95/p99 latency, error rate per endpoint.
