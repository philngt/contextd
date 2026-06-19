# Find

Fuzzy search across active workspace patterns, contracts, services, packs. Skip intent parser ceremony — chỉ khi user đã biết mình cần gì.

```
/find <keywords>
```

Examples:
- `/find kafka consumer` → patterns + contracts liên quan kafka/consumer
- `/find ratelimit` → bất kỳ pattern/contract/service nào nhắc đến rate limit
- `/find idempotency` → cross-cutting principles + pack-specific rules

> Khác `/use-contextd`: KHÔNG planner/selector/reviewer subagent, KHÔNG ghi context-file. Chỉ trả top-5 candidate + 1-2 dòng snippet. Lightweight.

---

## Bước 0 — Workspace check

Theo [workspace-resolution.md Profile B](../../agents/pipeline/workspace-resolution.md#profile-b--knowledge-root-only-active-workspace-optional). Set: `effective_knowledge_root`, `workspace_active`.

Nếu `workspace_active` null → vẫn chạy, scope mở rộng tới mọi workspace + engine + packs. Trong output đánh tag workspace name cho mỗi result.

---

## Bước 1 — Build search corpus

Glob các file dưới đây thành flat list (mỗi item: `{path, workspace, kind, content}`):

| Kind | Path glob | Workspace tag |
|------|-----------|---------------|
| pattern | `{ws}/platform/patterns/*.md` | workspace name |
| contract | `{ws}/platform/contracts/*.md` | workspace name |
| service | `{ws}/projects/*/services/*.md` | workspace name |
| runbook | `{ws}/runbooks/*.md` | workspace name |
| pack-constraints | `packs/*/agents/constraints.md` | `(pack:{name})` |
| pack-readme | `packs/*/README.md` | `(pack:{name})` |
| cross-cutting | `agents/cross-cutting-principles.md` | `(engine)` |

Nếu `workspace_active` set → CHỈ `{ws}/...` của workspace đó + packs active của workspace đó (từ `workspace.md ## Packs`) + engine.

Nếu null → tất cả workspace + tất cả packs + engine.

Skip file > 100KB (defensive).

---

## Bước 2 — Score & rank

Cho mỗi `keyword` trong query (lowercase, split space):

| Match location | Weight |
|---|---|
| Filename (basename without `.md`) | 10 |
| First H1 heading | 8 |
| H2/H3 heading | 5 |
| First 500 chars (lead paragraph) | 3 |
| Anywhere else in content | 1 |

Score = sum across all keywords (substring match, case-insensitive). Tiebreaker: filename match > heading match > content match.

Item score = 0 → exclude.

Sort desc, lấy top-5.

---

## Bước 3 — Render output

```
Found {N} matches for "{query}" (workspace: {workspace_active or "all"}):

1. [{kind}] {workspace_tag} {path}
   {first non-empty line of file, trimmed to 120 chars}
   Score: {N}  •  Match: filename + heading

2. [{kind}] ...
```

Nếu 0 match:
```
No match. Try:
  - Broader keyword (vd "kafka" thay vì "kafka-consumer-batch-retry")
  - Check workspace: workspace_active = {active or "none"}
  - Suggest: /list-workspaces, hoặc /use-contextd "{original query}" để full pipeline
```

---

## Bước 4 — Suggest next

After top-5:

```
Next steps:
  - Open a file: just paste path
  - Full context analysis: /use-contextd "{query}"
  - See full pattern table: cat {ws}/patterns-index.md
```

---

## Hard rules

- Read-only. KHÔNG ghi file. KHÔNG sửa `.contextd/context/current-task.json`.
- Respect workspace lock: nếu `workspace_active` set, KHÔNG hiển thị result từ workspace khác (engine + packs of active workspace OK).
- KHÔNG dispatch subagent — pipeline lite by design.
- KHÔNG fetch ngoài `{effective_knowledge_root}/`.

## Khi nào nên dùng

- "Tôi nhớ workspace này có pattern X, đường dẫn là gì?"
- "Có constraint nào về idempotency trong stack tôi không?"
- Quick lookup trước khi mở task đầy đủ với `/use-contextd`.

Không nên dùng:
- Task implement code (dùng `/use-contextd`).
- Audit toàn bộ wiki (dùng `/contextd-eval`).
- Tìm theo intent có domain logic phức tạp (`/use-contextd` planner sẽ tốt hơn).
