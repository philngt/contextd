# pack-web-api — Top 10 Common Pitfalls

Anti-pattern lặp lại trong REST/GraphQL/gRPC. Additive trên [constraints.md](constraints.md).
Mỗi item: rule (NG → OK), why, detect, severity.

## P01 — N+1 query trên endpoint list
- **NG**: handler `GET /orders` loop từng order rồi `findUserById` mỗi vòng.
- **OK**: join/`IN (...)` 1 query, hoặc dataloader gom batch.
- **Why**: latency tăng tuyến tính theo size; DB rớt khi traffic spike.
- **Detect**: manual review + APM trace; regex hint `for.*find.*ById\(` trong handler.
- **Severity**: error

## P02 — Missing pagination on list endpoint
- **NG**: `GET /items` trả full table.
- **OK**: cursor/offset + max page size; trả `nextCursor` + `total` (optional).
- **Why**: payload bloat, OOM client, DoS vector.
- **Detect**: Layer-2 — review response shape có `page|cursor|limit` không.
- **Severity**: error

## P03 — Return entity thay vì DTO (over-exposure)
- **NG**: trả thẳng JPA/ORM entity → leak field nội bộ (`passwordHash`, `internalNote`).
- **OK**: map sang response DTO whitelist field.
- **Why**: mass-data-exposure (OWASP API3:2023).
- **Detect**: Layer-2 — check return type của controller method.
- **Severity**: error

## P04 — Mass assignment
- **NG**: `userRepo.save(req.body)` cho phép set `role`, `isAdmin`.
- **OK**: request DTO chỉ chứa field user được phép sửa.
- **Why**: privilege escalation (OWASP API6).
- **Detect**: regex `save\(.*body\)|save\(.*req\.\w+\)`; Layer-2 check.
- **Severity**: error

## P05 — Leak stack trace / internal error trong 5xx
- **NG**: `e.printStackTrace()` hoặc `return { error: e.toString() }`.
- **OK**: log full với correlationId, response `{code: "INTERNAL_ERROR", requestId}`.
- **Why**: information disclosure → recon vector.
- **Detect**: Layer-1 `pack-web-api-print-stack-trace`.
- **Severity**: error

## P06 — Undefined retry semantics on mutation
- **NG**: `POST /payments` retry tạo 2 charge.
- **OK**: durable idempotency/outcome record, conditional/state-machine semantics, or explicit reconciliation/non-retry contract chosen from operation risk.
- **Why**: client retry plausible (mobile/webhook) → duplicate side-effects.
- **Detect**: Layer-2 — review mutating endpoint có dedup strategy.
- **Severity**: error

## P07 — Missing rate limit trên auth/expensive endpoint
- **NG**: `/login`, `/forgot-password`, `/search` không giới hạn.
- **OK**: abuse policy chọn identity key, quota/rate/concurrency/challenge and downstream protection từ threat/workload evidence; values từ config.
- **Why**: credential stuffing, scraping, thundering herd.
- **Detect**: Layer-2 — list endpoint nhạy cảm, check middleware.
- **Severity**: error

## P08 — Broken Object Level Authorization (BOLA / IDOR)
- **NG**: `GET /orders/:id` trả order bất kể caller có sở hữu không.
- **OK**: authz check `order.userId == caller.id` (hoặc policy engine) trước khi return.
- **Why**: OWASP API1:2023 — lỗ hổng phổ biến nhất.
- **Detect**: Layer-2 — mỗi GET/PUT/DELETE by-id có ownership check.
- **Severity**: error

## P09 — Hardcoded base URL / endpoint của downstream
- **NG**: `fetch("https://api.partner.com/v1/...")` ngay trong code.
- **OK**: config-driven URL, env-specific.
- **Why**: không deploy được sang staging/prod khác môi trường.
- **Detect**: Layer-1 `pack-web-api-hardcoded-base-url`.
- **Severity**: warn

## P10 — Broad `catch (Exception e)` swallow
- **NG**: `catch (Exception e) { log.error(e); }` rồi return 200/null.
- **OK**: catch specific exception, rethrow domain error, return đúng status code.
- **Why**: bug ẩn, mismatch HTTP semantics, debugging vô vọng.
- **Detect**: Layer-1 `pack-web-api-broad-exception-catch`.
- **Severity**: warn

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 N+1 | — (design) | ✓ |
| P02 pagination | — | ✓ |
| P03 DTO | — | ✓ |
| P04 mass-assign | `pack-web-api-mass-assignment` | ✓ |
| P05 stack-trace | `pack-web-api-print-stack-trace` | ✓ |
| P06 idempotency | — | ✓ |
| P07 rate-limit | — | ✓ |
| P08 BOLA | — | ✓ |
| P09 hardcoded-url | `pack-web-api-hardcoded-base-url` | ✓ |
| P10 broad-catch | `pack-web-api-broad-exception-catch` | ✓ |
