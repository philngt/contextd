# Tool List

In bảng toàn bộ tools trong toolbox của workspace active. Group theo status. Help non-tech xem nhanh "tôi đã build cái gì rồi".

> Output in console — KHÔNG ghi file. Đây là tra cứu nhanh.
> Reference: [pack-solo-builder README](../../packs/pack-solo-builder/README.md).

---

## Input

| Arg | Required | Notes |
|---|---|---|
| `--status {value}` | optional | Filter theo status: `draft`, `specced`, `building`, `done`, `shelved`. Default: tất cả. |
| `--recipe {name}` | optional | Filter tools dùng recipe cụ thể. Vd: `--recipe bulk-file-processing`. |

---

## Bước 0 — Workspace check

Resolve workspace. Set `{ws}`. STOP nếu chưa init.

## Bước 1 — Discover

1. Glob `{ws}/tools/*-spec.md` (loại trừ `README.md` và file không có suffix `-spec.md`).
2. Nếu zero files:
   ```
   📦 Toolbox trống.

   Build tool đầu tiên: /tool-design "ý tưởng của bạn"
   ```
   STOP.

## Bước 2 — Parse mỗi spec

Đọc frontmatter + section Problem (first 2 lines) từng file. Extract:

- `slug` (từ filename hoặc frontmatter)
- `title` (H1)
- `status` (frontmatter)
- `recipe_used` (frontmatter)
- `os` (frontmatter)
- `created` (frontmatter)
- `purpose_short` (first sentence của Problem section, max 100 chars)

## Bước 3 — Apply filter

- Nếu `--status` có → filter theo.
- Nếu `--recipe` có → filter theo (match exact recipe name).

## Bước 4 — Render output

Group theo status, in từng group. Status order: `building` → `specced` → `draft` → `done` → `shelved`.

```
📦 Toolbox: {ws} ({total} tools)

🔨 BUILDING ({n}) — đang implement
┌────────────────────┬─────────────────────────────┬──────────────────────┬─────────┐
│ Slug               │ Title                       │ Recipe               │ OS      │
├────────────────────┼─────────────────────────────┼──────────────────────┼─────────┤
│ moment-uon         │ Tính moment uốn dầm thép    │ formula-calculator   │ cross   │
│ inventory-mgr      │ Quản lý kho linh kiện        │ local-database-mgr   │ windows │
└────────────────────┴─────────────────────────────┴──────────────────────┴─────────┘

📋 SPECCED ({n}) — sẵn sàng implement
{table}

📝 DRAFT ({n}) — còn Open Questions
{table}

✅ DONE ({n})
{table}

📦 SHELVED ({n}) — paused
{table}
```

Nếu group nào có 0 entry sau filter → skip group đó (không in empty section).

## Bước 5 — Footer hints

```
─────────────────────────────────────────────────────────
Commands:
  /tool-design "{ý tưởng}"           — build tool mới
  /tool-design --resume {slug}        — continue spec đang draft
  /tool-extend {slug}                 — thêm/sửa tính năng tool đã có
  cat {ws}/tools/{slug}-spec.md       — xem spec chi tiết
─────────────────────────────────────────────────────────
```

---

## Notes

- **Read-only** — không modify file gì.
- **Workspace isolation** — chỉ scan `{ws}/tools/`, không cross-workspace.
- **Encoding**: dùng box-drawing characters đơn giản (├ ─ │ ┌ ┐ └ ┘ ┤ ┬ ┴ ┼) — universal terminal support.
- Nếu spec parse fail (corrupt frontmatter, missing H1) → ghi vào row "⚠ {filename} — parse error" thay vì crash.
