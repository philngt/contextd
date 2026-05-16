# pack-solo-builder — Writing Rules

> "Coding rules" trong pack này = **writing rules** cho tool spec docs. Pack-solo-builder không sinh code trong slash commands — nó sinh artifacts: tool specs, recipe entries.

## Tool Spec Writing

- **Lead with the problem, not the tool**. Section đầu là `## Problem` mô tả pain point đời thực, không phải `## Tool features`.
- **System Map dùng plain text + mermaid**:
  - Plain text trước (cho người không quen mermaid): `Input: file Excel ABC.xlsx → Process: filter rows where Status=Open → Output: file Excel filtered.xlsx + summary terminal`
  - Mermaid sau (cho người quen):
    ```mermaid
    flowchart LR
      A[Excel input] --> B[Filter logic]
      B --> C[Excel output]
      B --> D[Summary terminal]
    ```
- **Tech Stack section** dùng table format:
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

### Windows (recommend: Docker)
Vì sao Docker: pandas + openpyxl trên Windows native đôi khi vỡ do thiếu Visual C++ build tools. Docker tránh hết.

\`\`\`yaml
# docker-compose.yml
services:
  tool:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - .:/app
    command: python tool.py
\`\`\`

\`\`\`bash
docker compose run --rm tool input.xlsx
\`\`\`

### Windows (native, nếu không muốn Docker)
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

- **1-2 câu/lần**, không dồn 8 câu cùng lúc — non-tech sẽ nản.
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

- Slug = kebab-case, ASCII only, max 60 chars. Strip Vietnamese diacritics.
- Title = plain Vietnamese OK, mô tả mục đích, ≤ 80 chars.
- Folder convention: `{ws}/tools/{slug}-spec.md`. Nếu tool đã build, folder phụ `{ws}/tools/{slug}/` chứa code thực + link tới spec.

## Domain Term Handling

- Khi spec mention term ngành (vd "moment uốn", "VAT", "ICD-10"):
  1. Check `{ws}/domains/{field}/glossary.md` có chưa
  2. Có → link tới entry: `[moment uốn](../../domains/co-khi/glossary.md#moment-uon)`
  3. Chưa → spec đề cập, đồng thời notify user "term này nên add vào glossary để Claude future-proof"
