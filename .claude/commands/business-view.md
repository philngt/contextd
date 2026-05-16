# Business View

Dịch một artifact kỹ thuật (service, contract, pattern, ADR) sang **business view** — góc nhìn không-jargon, dành cho PM / business / executive đọc.

> Output là tài liệu giải thích, KHÔNG sửa file gốc. Output ghi vào `{ws}/product/views/` để tracking.
> Reference: [pack-product retrieval-map](../../packs/pack-product/agents/pipeline/retrieval-map.md), [pack-product coding-rules.md (Translation table)](../../packs/pack-product/agents/coding-rules.md).

---

## Input

| Arg | Required | Notes |
|---|---|---|
| `{target}` | required | Đường dẫn relative tới `{ws}/` hoặc tên service/contract/pattern. Vd: `projects/billing/services/invoice-service.md`, `platform/contracts/payment-api.md`, hoặc `invoice-service`. |
| `--audience {who}` | optional | `pm` (default) / `executive` / `customer-success` / `sales`. Ảnh hưởng tone + depth. |
| `--out {path}` | optional | Override output. Default: `{ws}/product/views/{slug-of-target}-business-view.md`. |

---

## Bước 0 — Workspace & pack check

1. Resolve workspace. Set `{ws}`.
2. STOP nếu workspace chưa init.
3. Warn nhẹ nếu `pack-product` chưa bật (command vẫn chạy, nhưng output không được pack-product validator check).

## Bước 1 — Resolve target

1. Nếu `{target}` là path → check tồn tại trong `{ws}/`. STOP nếu không.
2. Nếu là tên (vd `invoice-service`) → glob trong `{ws}/`:
   - `{ws}/projects/*/services/{target}.md`
   - `{ws}/platform/contracts/{target}.md`
   - `{ws}/platform/patterns/{target}.md`
3. Nhiều match → AskUserQuestion để user chọn.
4. Set `target_path`, `target_type` (service / contract / pattern / adr / unknown).

## Bước 2 — Gather context (priority order)

Theo [retrieval-map](../../packs/pack-product/agents/pipeline/retrieval-map.md) cross-pack section:

1. Đọc `target_path` — extract: name, purpose (1-line từ H1/intro), responsibilities (bullets), dependencies (other services/contracts).
2. Tìm related domain rules:
   - Glob `{ws}/domains/*/workflow.md` — nếu mention `target_name` → include.
3. Tìm related personas:
   - Glob `{ws}/product/personas/*.md` — nếu domain workflow của target chạm persona, include.
4. Tìm related briefs:
   - Glob `{ws}/product/briefs/*.md` — nếu frontmatter mention `target_name` hoặc body link tới `target_path` → include.
5. Tìm related metrics:
   - Read `{ws}/product/metrics.md` — nếu metric có dashboard liên quan target → include.

**Cap context**: tối đa 8 file phụ trợ. Quá → ưu tiên domain + briefs.

## Bước 3 — Translate using mapping table

Áp dụng mapping từ [pack-product coding-rules.md](../../packs/pack-product/agents/coding-rules.md) "Translation from Engineering" section:

| Engineering term | Business view |
|---|---|
| Endpoint / API | Capability the system offers |
| Schema / DTO | Information shape we exchange |
| Service | Component that does X for users |
| Deployment / container | Where it runs (cloud / region / device) |
| Migration | One-time data update |
| Refactor | Internal cleanup, no user-visible change |
| Latency p99 | "99% of users see response within Xms" |
| Throughput | How many requests we can handle per second/minute |

Tone theo `--audience`:
- `pm`: chi tiết enough để brief mới — bao gồm capabilities + constraints + dependencies (in business terms).
- `executive`: 1 paragraph + 3 bullet — what it does, who it serves, what it costs/risks.
- `customer-success`: focus on what customer sees + what to say when feature breaks.
- `sales`: focus on capability + differentiator + limits (pricing-relevant).

## Bước 4 — Generate output

Format:

```md
---
target: {target_path}
target_type: {service|contract|pattern|adr}
audience: {audience}
generated: YYYY-MM-DD
generated_by: /business-view
---

# {Human-readable title — what this is, in business terms}

## What it does

{1-2 paragraphs in plain language — NO jargon. What user/business value does this thing provide?}

## Who uses it

- {Persona / role 1} — {how they encounter it}
- {Persona / role 2}

## Key capabilities

- {Capability 1 — phrased as user-facing outcome}
- {Capability 2}
- {Capability 3}

## Limits & guarantees

- {What it CAN handle — load, scale, response time in plain terms}
- {What it CANNOT do — explicit non-features, scope boundary}
- {SLA / guarantee — "99.9% available" → "down at most ~9 minutes per week"}

## Dependencies (in business terms)

- {Depends on X — which means if X is down, this also degrades in Y way}

## Related product context

- Briefs: {links to {ws}/product/briefs/...}
- Personas: {links}
- Metrics: {which metric in {ws}/product/metrics.md tracks this}

## When it breaks

- {Symptom user sees}
- {What CS/support should say}
- {Runbook link if exists in {ws}/runbooks/}

---

> **Technical reference** (for engineering, kept here so this view stays sync-able):
> - Source: [{target_path}]({target_path})
> - Related contracts: {list}
> - Related patterns: {list}
> - Related ADRs: {list}
```

## Bước 5 — Validate output

Chạy `pack-product` validator trên output:
- `pack-product-jargon-leak` — nếu vẫn còn jargon trong main body (trên footnote `Technical reference`), WARN + suggest rewrite.

## Bước 6 — Confirm

```
✓ Business view created: {ws}/product/views/{slug}-business-view.md
  - Source:    {target_path} ({target_type})
  - Audience:  {audience}
  - Context used: {N} files (domains, personas, briefs, metrics)

⚠ Jargon warnings: {count} (review file)

Next steps:
  - Share with {audience}
  - Update khi source doc {target_path} đổi (re-run /business-view)
```

---

## Notes

- **Re-runnable**: gọi lại với cùng target → overwrite output (sau khi confirm) — vì engineering doc là source of truth, view phải sync lại.
- **Multiple audiences**: chạy nhiều lần với `--audience` khác nhau → output file khác nhau (suffix audience).
- **Cross-workspace**: KHÔNG được. Target PHẢI trong `{ws}` active.
