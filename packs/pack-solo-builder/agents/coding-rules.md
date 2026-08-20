# pack-solo-builder — Writing Rules

> "Coding rules" trong pack này = **writing rules** cho tool spec docs. Pack-solo-builder không sinh code trong slash commands — nó sinh artifacts: tool specs, recipe entries.

## Tool Spec Writing

- **Lead with the problem, not the tool**. Section đầu là `## Problem` mô tả pain point đời thực, không phải `## Tool features`.
- **System Map bắt đầu bằng plain text**: `Input: file Excel ABC.xlsx → Process: filter rows where Status=Open → Output: file Excel filtered.xlsx + summary terminal`.
- Chỉ thêm Mermaid khi có nhiều branch/integration cần nhìn quan hệ; plain text đủ cho flow tuyến tính:
    ```mermaid
    flowchart LR
      A[Excel input] --> B[Filter logic]
      B --> C[Excel output]
      B --> D[Summary terminal]
    ```
- **Tech Stack section** dùng table; chỉ so sánh alternative có thể làm thay đổi quyết định:
  | Component | Chọn | Vì sao | Vì sao KHÔNG alternative |
  |-----------|------|--------|--------------------------|
  | Language | Python | Có sẵn library xử lý Excel (pandas) | Không chọn JS vì cần Node + thêm setup |
- **Acceptance Criteria** dùng checkbox + dạng "When X, then Y":
  - [ ] Khi chạy `python tool.py input.xlsx`, sinh ra `input-filtered.xlsx`
  - [ ] Số dòng output = số dòng input có cột Status="Open"
  - [ ] Terminal in: "Filtered N rows from M total"

## Per-OS Setup Section

Format chuẩn:

```md
## Setup

### Linux / macOS
\`\`\`bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas openpyxl
\`\`\`

### Container option (only when the recipe requires it)
Vì sao container: pin dependency/runtime khi native setup hoặc sharing đã được chứng minh là vấn đề; không mặc định Docker cho mọi tool.

\`\`\`yaml
# compose.yaml
services:
  tool:
    build:
      context: .
      args:
        PYTHON_BASE: ${PYTHON_IMAGE:?set a workspace-tested Python image tag or digest}
    working_dir: /app
    command: python tool.py
\`\`\`

\`\`\`bash
docker compose run --rm tool input.xlsx
\`\`\`

### Windows native
\`\`\`powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install pandas openpyxl
\`\`\`
```

## Recipe Citation

Khi spec chọn 1 recipe, reference rõ:

```md
**Recipe used**: [bulk-file-processing](packs/pack-solo-builder/recipes/bulk-file-processing.md)
```

Nếu spec mix 2 recipes → list cả 2 + ghi rõ phần nào lấy từ recipe nào.

## Discovery Question Style (cho `/tool-design` Bước 2)

- Hỏi theo nhóm nhỏ, mặc định 1-2 câu/lần; điều chỉnh theo phản hồi thay vì dồn toàn bộ discovery.
- **Mỗi câu PHẢI có ví dụ cụ thể** trong description, ngay cả nếu là câu đơn giản.
- **Cho phép "tôi không biết"** option — Claude tự đề xuất default, ghi vào spec dưới `## Open Questions` để user revisit sau.
- **Câu thứ tự**:
  1. "Vấn đề bạn đang gặp là gì?" (1-2 câu, có ví dụ)
  2. "Hiện tại bạn làm tay/Excel mất bao lâu mỗi lần?"
  3. "Input là gì? File (loại nào)? Số tay nhập? Pull từ đâu?"
  4. "Output đi đâu? File? Màn hình? Email? Database?"
  5. "Tool này dùng 1 lần, thi thoảng, hằng ngày, hay tự động chạy?"
  6. "Chỉ bạn dùng, hay share đồng nghiệp?"
  7. "OS bạn chạy? Linux/macOS/Windows?"
  8. (optional) "Bạn quen Python/script chưa, hay muốn tránh hoàn toàn terminal?"

## Spec Status Machine

`draft` → `specced` → `building` → `done` (hoặc `shelved` ở bất kỳ stage)

- `draft`: còn Open Questions chưa trả lời.
- `specced`: 4 section bắt buộc đầy đủ + Open Questions empty/resolved → sẵn sàng implement.
- `building`: đã start implement, có Build Log.
- `done`: acceptance criteria pass.
- `shelved`: pause, ghi reason.

## Tool Naming

- Slug = kebab-case, ASCII; tuân host/path limit và giữ đủ ngắn để dùng trên CLI. Strip Vietnamese diacritics.
- Title = plain Vietnamese OK, mô tả mục đích và phân biệt được trong catalog; không đặt quota ký tự nếu host không yêu cầu.
- Folder convention: `{ws}/tools/{slug}-spec.md`. Nếu tool đã build, folder phụ `{ws}/tools/{slug}/` chứa code thực + link tới spec.

## Domain Term Handling

- Khi spec mention term ngành (vd "moment uốn", "VAT", "ICD-10"):
  1. Check `{ws}/domains/{field}/glossary.md` có chưa
  2. Có → link entry + source/version/units/assumptions liên quan
  3. Chưa hoặc provenance thiếu → ghi Knowledge Gap, giữ spec `draft`, không tự suy diễn
  4. High-impact use case → ghi qualified reviewer, human checkpoint và verification fixtures trước build
