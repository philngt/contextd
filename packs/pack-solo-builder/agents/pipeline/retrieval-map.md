# pack-solo-builder — Retrieval Map

| Component | Docs to Retrieve |
|-----------|------------------|
| `tool-design`    | `packs/pack-solo-builder/recipes/README.md`, `tools/README.md`, `domains/{domain}/glossary.md`, `templates/tool-spec.md` |
| `tool-extend`    | `tools/README.md` |
| `recipe`         | `packs/pack-solo-builder/recipes/README.md`, `templates/tool-recipe.md` |
| `tool-catalog`   | `tools/README.md` |

Các row trên là **initial context**. Sau khi index/signal chọn candidate, workflow mới load đúng `recipes/{candidate}.md` hoặc `tools/{candidate}-spec.md`. Full glob chỉ là fallback khi index thiếu, stale hoặc ambiguous; không materialize toàn bộ catalog mặc định.

## Recipe Match Algorithm (cho `/tool-design`)

Sau discovery, đọc recipe index và match theo signal trước; chỉ mở recipe candidate + alternative có trade-off thực sự khác:

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

Nhiều signal khớp → chọn owner recipe cho core purpose; mix recipe chỉ khi mỗi recipe sở hữu một phần rõ và cite phần đó.

Không signal nào khớp → ghi explicit recipe gap và đề xuất tạo/review recipe mới. KHÔNG được tự sáng tạo stack hoặc ép user đổi wording để làm heuristic pass.

## Tool Catalog Scan (cho dedup)

Trước khi propose tool mới, đọc `{ws}/tools/README.md`, shortlist candidate rồi load candidate specs. Nếu index thiếu/stale/ambiguous mới scan `{ws}/tools/*-spec.md`. So sánh:

- **Title** — normalized case/diacritics + semantic similarity
- **Problem section** — core outcome/entity overlap, không dùng một threshold keyword chung
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

- Recipe match dựa index signal — không hiểu sâu domain. User review proposed recipe trước khi accept.
- Catalog shortlist là heuristic; synonym hoặc index stale có thể tạo false negative nên workflow có fallback scan và manual confirm.
