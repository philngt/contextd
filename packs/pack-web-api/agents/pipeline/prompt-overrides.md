# pack-web-api — Prompt Overrides

## Self-Check append

```
### API Boundary (pack-web-api)
- Input validated at the boundary (framework validation, not ad-hoc if-checks)
- Error response uses structured shape — no raw exception/stack trace in body
- Auth check precedes business logic (middleware/decorator, not inline)
- Mutating endpoint has idempotency strategy (key header or upsert)
- No PII/secret in request/response log
- No hardcoded base URL (read from config/env)
```
