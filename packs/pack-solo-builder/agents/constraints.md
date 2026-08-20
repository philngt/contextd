# pack-solo-builder — Constraints

Hard rules cho tool-design workflow của non-tech expert. Additive trên engine constraints.

## Spec Completeness (`pack-solo-builder-spec-completeness`)

- **Mỗi tool spec PHẢI có 4 section bắt buộc**: `Problem`, `System Map`, `Tech Stack` (chosen + reasoning), `Acceptance Criteria`. Thiếu bất kỳ section nào → spec chưa hoàn thiện, KHÔNG được implement.
- **System Map PHẢI có**: Input → Process → Output tối thiểu bằng plain text; diagram chỉ thêm khi quan hệ/branch đủ phức tạp để giúp người đọc.
- **Acceptance Criteria PHẢI testable**: "khi nhập X thì output Y" / "chạy command Z thì sinh file W". Không chấp nhận "tool hoạt động tốt" / "dễ dùng".

## Recipe Discipline (`pack-solo-builder-recipe-discipline`)

- **KHÔNG recommend tech stack không có trong `packs/pack-solo-builder/recipes/`**. Nếu user task không match recipe nào → STOP, hỏi user mô tả lại bằng từ khoá khác hoặc đề xuất add recipe mới.
- **Mỗi recommendation PHẢI cite recipe đã dùng** (đường dẫn cụ thể).
- **Mỗi material tech choice PHẢI có lý do bằng plain language**; so sánh alternative khi trade-off có thể thay đổi quyết định, không tạo boilerplate cho lựa chọn hiển nhiên.

## Tool Catalog Discipline (`pack-solo-builder-catalog-discipline`)

- **TRƯỚC khi propose tool mới**, scan `{ws}/tools/*.md` (ngoại trừ `README.md`). Nếu tìm thấy tool có tên/purpose tương tự → STOP, hỏi user "extend tool đã có hay tạo mới?".
- **1 tool = 1 mục đích**. Spec mô tả > 1 mục đích chính → STOP, đề xuất tách thành 2 specs.
- **Không trùng slug** trong cùng workspace. Slug đã tồn tại → đề nghị extend/rename và để user xác nhận; không tự tạo bản sao `-2` khó phân biệt.

## Cross-Platform Reasoning (`pack-solo-builder-cross-platform`)

- **Tool spec PHẢI nêu target environments thực tế** và setup/test cho từng target; không bắt mọi tool support Linux + Windows nếu user không cần.
- **Container chỉ dùng khi có portability/dependency/deployment benefit rõ**; native GUI và single-user script thường ưu tiên native setup.
- **Web tool chỉ cần compose/container option khi sharing/deployment/isolated dependency là requirement**, không vì framework name.

## Plain Language (`pack-solo-builder-plain-language`)

- **KHÔNG dùng jargon kỹ thuật mà không giải thích 1 dòng**: nếu mention `venv`, `Docker`, `cron`, `SQLite`, `argparse`, ... PHẢI có 1 câu plain-language ngay sau (vd: "venv = thư mục riêng cho thư viện Python của tool này, tránh đụng tool khác").
- **KHÔNG dùng buzzword không cần thiết**: "scalable", "robust", "production-ready", "enterprise-grade" — đều spam từ.
- **KHÔNG nói "đơn giản" / "dễ"** vì điều đó tuỳ background người đọc. Nói cụ thể: "chạy 1 command", "fill 1 form", "click 2 nút".

## Code Generation Boundary (`pack-solo-builder-code-boundary`)

- **Slash `/tool-design` KHÔNG sinh code** — chỉ ghi spec. Sau khi spec đã `specced`, implementation phải là một explicit follow-up task; task đó có thể ở cùng conversation hoặc session khác.
- **Slash `/tool-extend` KHÔNG sinh code** — chỉ propose update spec.
- **Khi spec có status `specced`** (đã review xong) thì AI mới được implement.

## Resume-ability (`pack-solo-builder-resumability`)

- Mọi spec có frontmatter `status: draft | specced | building | done | shelved`.
- Spec đang `draft` → có thể `/tool-design` lại để continue (đọc spec hiện có, hỏi tiếp các câu chưa trả lời).
- Spec `building` → có log `## Build Log` để track tiến độ qua nhiều sessions.

## Domain Knowledge Reuse (`pack-solo-builder-knowledge-reuse`)

- **TRƯỚC khi spec dùng công thức / standard / regulation ngành nghề**, check `{ws}/domains/{field}/glossary.md` và source/version được cite. Nếu đã có → reference đúng entry; nếu chưa có hoặc provenance không đủ → ghi knowledge gap và giữ spec `draft`, không tự điền từ memory.

## Safety & Evidence Boundary (`pack-solo-builder-safety-boundary`)

- **Recipe là implementation guidance, không phải domain authority.** Công thức hoặc rule ảnh hưởng y tế, pháp lý, tài chính, kết cấu, an toàn hay compliance phải có authoritative source ID/version/jurisdiction, unit/assumption contract, qualified review owner và verification fixtures.
- **Không tự động hoá final high-impact decision** nếu chưa có human-review checkpoint, failure/override path và audit evidence phù hợp domain policy.
- **External API/scraping phải theo provider contract**: terms/permission, privacy, authentication, freshness, rate-limit/retry semantics và identifying User-Agent khi cần; không giả browser để né policy.

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
