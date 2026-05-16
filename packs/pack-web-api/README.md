# pack-web-api

REST/GraphQL/gRPC API patterns. Bật khi service cung cấp HTTP endpoint, GraphQL resolver, hoặc gRPC server.

## Khi nào bật

- Spring `@RestController` / `@RequestMapping`
- Express/Fastify/Koa route handlers
- FastAPI / Flask endpoints
- GraphQL resolver (Apollo, graphql-java)
- gRPC service implementation

## Components

- `rest`: REST endpoint patterns
- `graphql`: GraphQL resolver patterns
- `grpc`: gRPC service patterns
- `api`: shared API concerns (validation, error shape, auth)

## Constraints highlights

- Input validation tại boundary (`@Valid`, schema validation, Zod, ...)
- Error response phải có shape contract (không trả raw exception/stack trace)
- Idempotency key cho mutating endpoints (POST/PUT/PATCH/DELETE) khi client có thể retry
- Auth check trước business logic
- Không leak internal info qua response/header

## Validator rules

| Rule | Severity | Check |
|------|----------|-------|
| `pack-web-api-print-stack-trace`     | error | `printStackTrace()` call — leaks internals to logs/response |
| `pack-web-api-missing-valid`         | warn  | `@RequestBody Foo` parameter without `@Valid`/`@Validated` |
| `pack-web-api-hardcoded-base-url`    | warn  | Literal `http(s)://...` URL outside localhost/test code |
| `pack-web-api-broad-exception-catch` | warn  | `catch (Exception e)` followed by empty body or single log+swallow |

## Bật pack

```md
## Packs

- pack-web-api
```
