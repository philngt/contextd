# pack-web-api — Validator Rules

Layer-1 rule. Implement: [`scripts/rules.py`](../../scripts/rules.py). Prefix `pack-web-api-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-web-api-print-stack-trace`     | error | `printStackTrace()` call detected — leaks internals via log/response. |
| `pack-web-api-missing-valid`         | warn  | `@RequestBody Foo` parameter without `@Valid` / `@Validated` on the same parameter. |
| `pack-web-api-hardcoded-base-url`    | warn  | Literal `http://` or `https://` URL in code, excluding `localhost`, `127.0.0.1`, `example.com`, test files. |
| `pack-web-api-broad-exception-catch` | warn  | `catch (Exception e)` / `catch (Throwable t)` followed by no body / single log call (likely swallow). |

## Layer-2 self-check

```md
### API Boundary (pack-web-api)
- Input validated at the boundary (framework validation, not ad-hoc if-checks)
- Error response uses structured shape — no raw exception/stack trace in body
- Auth check precedes business logic (middleware/decorator, not inline)
- Mutating endpoint has idempotency strategy (key header or upsert)
- No PII/secret in request log
```

## Limitations

- Regex-only — `printStackTrace()` inside string literal would false-positive (rare).
- `missing-valid`: only catches `@RequestBody` Java-Spring style; FastAPI/Express/Zod patterns need pack extension.
- `hardcoded-base-url`: doesn't follow imported constants — URL via static-final missed.
