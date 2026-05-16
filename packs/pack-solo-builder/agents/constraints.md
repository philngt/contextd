# pack-solo-builder — Constraints

Hard rules cho tool-design workflow của non-tech expert. Additive trên engine constraints.

## Spec Completeness

- **Mỗi tool spec PHẢI có 4 section bắt buộc**: `Problem`, `System Map`, `Tech Stack` (chosen + reasoning), `Acceptance Criteria`. Thiếu bất kỳ section nào → spec chưa hoàn thiện, KHÔNG được implement.
- **System Map PHẢI có**: Input → Process → Output (tối thiểu). Mermaid diagram + plain-text fallback.
- **Acceptance Criteria PHẢI testable**: "khi nhập X thì output Y" / "chạy command Z thì sinh file W". Không chấp nhận "tool hoạt động tốt" / "dễ dùng".

## Recipe Discipline

- **KHÔNG recommend tech stack không có trong `packs/pack-solo-builder/recipes/`**. Nếu user task không match recipe nào → STOP, hỏi user mô tả lại bằng từ khoá khác hoặc đề xuất add recipe mới.
- **Mỗi recommendation PHẢI cite recipe đã dùng** (đường dẫn cụ thể).
- **Mỗi tech choice PHẢI có 2 phần lý do**: (a) tại sao chọn cái này, (b) tại sao KHÔNG chọn alternative phổ biến nhất. Cả 2 bằng plain language.

## Tool Catalog Discipline

- **TRƯỚC khi propose tool mới**, scan `{ws}/tools/*.md` (ngoại trừ `README.md`). Nếu tìm thấy tool có tên/purpose tương tự → STOP, hỏi user "extend tool đã có hay tạo mới?".
- **1 tool = 1 mục đích**. Spec mô tả > 1 mục đích chính → STOP, đề xuất tách thành 2 specs.
- **Không trùng slug** trong cùng workspace. Slug đã tồn tại → suffix `-2`, `-3`, ... hoặc force user chọn tên mới.

## Cross-Platform Reasoning

- **Mọi tool spec PHẢI có Setup section per OS**: Linux (native venv chấp nhận) + Windows (recommend Docker + docker-compose nếu task có dependency phức tạp như image processing, PDF generation, hoặc cần share team).
- **GUI native (Tkinter, PyWebView) KHÔNG recommend Docker** — note rõ trong spec.
- **Web tool (Streamlit, Flask) PHẢI có docker-compose option** ngay cả khi user chạy local.

## Plain Language

- **KHÔNG dùng jargon kỹ thuật mà không giải thích 1 dòng**: nếu mention `venv`, `Docker`, `cron`, `SQLite`, `argparse`, ... PHẢI có 1 câu plain-language ngay sau (vd: "venv = thư mục riêng cho thư viện Python của tool này, tránh đụng tool khác").
- **KHÔNG dùng buzzword không cần thiết**: "scalable", "robust", "production-ready", "enterprise-grade" — đều spam từ.
- **KHÔNG nói "đơn giản" / "dễ"** vì điều đó tuỳ background người đọc. Nói cụ thể: "chạy 1 command", "fill 1 form", "click 2 nút".

## Code Generation Boundary

- **Slash `/tool-design` KHÔNG sinh code** — chỉ ghi spec. Code là việc của session khác (user gõ "implement spec ở `{ws}/tools/{slug}-spec.md`").
- **Slash `/tool-extend` KHÔNG sinh code** — chỉ propose update spec.
- **Khi spec có status `specced`** (đã review xong) thì AI mới được implement.

## Resume-ability

- Mọi spec có frontmatter `status: draft | specced | building | done | shelved`.
- Spec đang `draft` → có thể `/tool-design` lại để continue (đọc spec hiện có, hỏi tiếp các câu chưa trả lời).
- Spec `building` → có log `## Build Log` để track tiến độ qua nhiều sessions.

## Domain Knowledge Reuse

- **TRƯỚC khi spec mention công thức / standard ngành nghề** (vd "moment uốn", "VAT 10%", "ICD-10"), check `{ws}/domains/{field}/glossary.md`. Nếu đã có → reference, không paraphrase. Nếu chưa có → đề xuất user add vào glossary trước.
