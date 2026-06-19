# pack-solo-builder — Retrieval Map

| Component | Docs to Retrieve |
|-----------|------------------|
| `tool-design`    | `packs/pack-solo-builder/recipes/*.md` (toàn bộ — chọn match best); `tools/*.md` (catalog scan); `domains/*/glossary.md` (term reference); `templates/tool-spec.md` |
| `tool-extend`    | `tools/*-spec.md`; `tools/README.md` (catalog index) |
| `recipe`         | `packs/pack-solo-builder/recipes/*.md`; `templates/tool-recipe.md` |
| `tool-catalog`   | `tools/*.md` (full scan); `tools/README.md` (index nếu có) |

## Recipe Match Algorithm (cho `/tool-design`)

Sau Bước 2 (discovery questions xong), match recipe theo signal:

| Signal từ user trả lời | Recipe ưu tiên |
|------------------------|----------------|
| "process file CSV/Excel/PDF nhiều" | `bulk-file-processing` |
| "tính toán theo công thức" + "chạy thi thoảng" | `formula-calculator-cli` |
| "nhập form + lưu lại để xem sau" | `daily-form-with-history` + `local-database-manager` |
| "vẽ biểu đồ" / "dashboard" | `data-visualization` |
| "tự động chạy mỗi ngày/tuần" | `scheduled-recurring-task` |
| "share đồng nghiệp" / "team dùng chung" | `team-shared-web-tool` |
| "sinh PDF báo cáo" | `pdf-report-generator` |
| "GUI native" / "không muốn terminal" + "chỉ mình dùng" | `desktop-gui-simple` |
| "pull data từ API/website" | `api-data-fetcher` |
| "quản lý records" / "CRUD" | `local-database-manager` |

Nhiều signal khớp → spec sẽ mix recipes. Cite cả 2.

Không signal nào khớp → STOP và hỏi user mô tả khác. KHÔNG được tự sáng tạo stack.

## Tool Catalog Scan (cho dedup)

Trước khi propose tool mới, scan `{ws}/tools/*-spec.md`. So sánh:

- **Title** (case-insensitive, strip diacritics) — fuzzy match ≥ 70% similarity
- **Problem section** — keyword overlap ≥ 3 từ chính (loại bỏ stopwords)
- **System Map Input/Output** — input/output type giống

Nếu match → STOP, hỏi user "có vẻ giống `{slug}` đã có, extend hay tạo mới?" với option:
1. Extend `{slug}` (chuyển sang `/tool-extend {slug}`)
2. Tạo mới (force, vẫn cảnh báo)
3. Cancel

## Domain Glossary Lookup

Khi user trả lời discovery questions có term ngành (regex match danh sách trong `{ws}/domains/*/glossary.md`):

- Có → tự động link entry trong spec
- Chưa → spec ghi term, notify user end of session: "Recommend add các term sau vào glossary: ..."

## Limitations

- Recipe match dựa keyword + signal — không hiểu sâu domain. User nên review proposed recipe trước khi accept.
- Catalog scan dùng fuzzy text — false negative nếu user dùng synonym khác. Manual confirm vẫn cần.
