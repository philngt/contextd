# pack-solo-builder

Cho **non-tech expert** (cơ khí, kế toán, y tế, luật, giáo viên, ...) dùng Claude Code làm **assistant cá nhân** để build tools hỗ trợ công việc. Wiki = "ngăn kéo dụng cụ" của bạn — Claude check ngăn kéo trước khi đề xuất, bạn không lặp lại tool đã có.

## Khi nào bật

- Bạn không phải dev, nhưng dùng Claude Code để generate scripts/apps tự động hóa công việc
- Bạn có **ý tưởng mơ hồ** ("muốn 1 tool tính moment uốn", "tool tracking máy móc bảo trì") nhưng không biết:
  - Hỏi mình câu nào để làm rõ scope
  - Nên dùng tech gì (Python script? GUI? web app?)
  - Đã build tool tương tự chưa
- Bạn muốn lưu các tool đã build vào 1 catalog có cấu trúc, không nằm rải rác

## Pack này KHÔNG phù hợp khi

- Bạn là engineer dev professional → dùng `pack-web-api`, `pack-frontend-react`, ...
- Bạn là PM/Product Owner trong team có engineer → dùng `pack-product`
- Bạn build production system phục vụ external customers (cần SLA, security audit, scale) → engineering pack
- Bạn muốn tự động hoá quyết định y tế, pháp lý, tài chính, kết cấu hoặc lĩnh vực regulated mà chưa có nguồn chuẩn + qualified reviewer → cần domain governance trước, recipe không phải authority

## Components

- `tool-design`: thiết kế 1 tool mới từ ý tưởng thô → spec
- `tool-extend`: thêm/sửa tính năng cho tool đã có
- `recipe`: catalog tech stack đề xuất per task type
- `tool-catalog`: scan + dedup các tool đã build

## Triết lý

1. **Spec trước, code sau** — `/tool-design` chỉ tạo spec. Khi spec đã `specced`, user có thể giao implementation ở task tiếp theo trong cùng conversation hoặc session khác.
2. **Recipe-driven** — mọi tech recommendation đến từ `recipes/` library, không tự sáng tạo. Nếu task không match recipe nào → STOP và yêu cầu user mô tả thêm.
3. **Target-platform explicit** — recipe ghi rõ platform được user cần và đã test. Container chỉ dùng khi portability/dependency/deployment benefit đủ rõ.
4. **1 tool = 1 mục đích** — không có "tool đa năng". Tool to → tách nhỏ thành nhiều tools.
5. **Plain language** — mọi reasoning bằng ngôn ngữ đời thường, không jargon.
6. **Evidence before automation** — công thức, regulation và high-impact decision phải có source/version/assumptions, review owner và verification fixtures.

## Slash commands liên quan

**Tool design (chính)**:
- [`/tool-design "{ý tưởng}"`](../../.claude/commands/tool-design.md) — wizard discovery + recipe match → output spec
- [`/tool-list`](../../.claude/commands/tool-list.md) — in toolbox đã có
- [`/tool-extend {slug}`](../../.claude/commands/tool-extend.md) — đề xuất update spec cho tool đã có

**Evidence ingestion (cho tài liệu ngành)** — pack-solo-builder tự động override prompts + UX:
- [`/evidence-ingest`](../../.claude/commands/evidence-ingest.md) — paste/MCP/API tài liệu ngành (PDF tiêu chuẩn, công thức, regulation)
- [`/evidence-analyze`](../../.claude/commands/evidence-analyze.md) — auto detect pack-solo-builder → dùng [domain-analysis-prompts.md](agents/pipeline/domain-analysis-prompts.md) thay vì engineering CORE prompts. Câu hỏi sinh ra tập trung "term này nghĩa là gì", "có nguồn chính thức không", KHÔNG hỏi API/schema/deployment.
- [`/evidence-qa`](../../.claude/commands/evidence-qa.md) — auto detect pack → áp [qa-batch-non-tech.md UX overrides](agents/pipeline/qa-batch-non-tech.md): wording plain, "Tôi biết / Hỏi expert / Bỏ qua / Để sau" thay vì jargon priority code, copy-paste block cho expert ngành.
- [`/evidence-apply`](../../.claude/commands/evidence-apply.md) — không cần override, route theo `Affects:` path (đã point tới `{ws}/domains/...` thay vì `{ws}/platform/...`).

## Constraints highlights

- Spec PHẢI có 4 section: Problem, System Map, Tech Stack (chosen + why), Acceptance Criteria
- KHÔNG recommend tech không có trong `recipes/` library
- KHÔNG sinh code trong slash `/tool-design` — chỉ ghi spec
- TRƯỚC khi propose tool mới, scan `{ws}/tools/` xem đã có tương tự chưa
- Mỗi lựa chọn kỹ thuật material có lý do plain-language; chỉ so sánh alternative khi trade-off có thể đổi quyết định
- Setup chỉ cover target OS đã chốt; container là một option có rationale, không phải default bắt buộc
- Formula/regulation/high-impact workflow chưa có authoritative evidence + review owner phải giữ `draft`, không được coi recipe là nguồn chuyên môn

## Recipe library

Hiện có 11 recipes (xem [`recipes/README.md`](recipes/README.md)). User có thể tự thêm bằng `templates/tool-recipe.md`.

| Recipe | Use cho |
|--------|---------|
| [bulk-file-processing](recipes/bulk-file-processing.md) | Process nhiều CSV/Excel/PDF |
| [formula-calculator-cli](recipes/formula-calculator-cli.md) | Tính toán theo công thức, chạy thi thoảng |
| [daily-form-with-history](recipes/daily-form-with-history.md) | Nhập form + lưu lịch sử |
| [data-visualization](recipes/data-visualization.md) | Chart/dashboard từ data |
| [scheduled-recurring-task](recipes/scheduled-recurring-task.md) | Chạy tự động định kỳ |
| [team-shared-web-tool](recipes/team-shared-web-tool.md) | Share tool với đồng nghiệp |
| [pdf-report-generator](recipes/pdf-report-generator.md) | Sinh PDF báo cáo |
| [desktop-gui-simple](recipes/desktop-gui-simple.md) | GUI native dùng cá nhân |
| [api-data-fetcher](recipes/api-data-fetcher.md) | Pull data từ API ngoài |
| [local-database-manager](recipes/local-database-manager.md) | Quản lý records local |
| [multi-agent-orchestrator](recipes/multi-agent-orchestrator.md) | Điều phối nhiều CLI agent đã được pin/test |

## Cấu trúc workspace khuyến nghị

```
workspaces/{ws}/
├── tools/                    # toolbox của bạn — 1 file/tool
│   ├── README.md             # auto-generated index
│   └── {slug}-spec.md
├── domains/{field}/          # nếu có chuyên ngành (cơ khí, kế toán)
│   ├── glossary.md           # terminology + công thức + standards (target của /evidence-apply khi pack active)
│   └── workflow-{slug}.md    # quy trình ngành (vd phác đồ điều trị, SOP)
├── evidence/                 # raw + analysis (auto-managed bởi /evidence-* commands)
└── workspace.md              # bật pack-solo-builder ở section ## Packs
```

## Bật pack

**Cách 1 — Per-codebase (recommend cho non-tech)**: chạy `/contextd-setup` trong codebase, ở Bước 4.5 tick checkbox `pack-solo-builder`. UI tự ghi vào `<cwd>/.contextd/config.json#packs` — không cần edit markdown.

**Cách 2 — Workspace-wide**: edit `workspaces/{ws}/workspace.md` section `## Packs`:

```md
## Packs

- pack-solo-builder
```

Áp dụng mọi codebase trong workspace (trừ codebase có override per-codebase).

> Per-codebase override (`.contextd/config.json#packs`) **replace** workspace default (`workspace.md ## Packs`), không additive. Legacy `.claude/wiki.json#packs` chỉ là compatibility adapter trong migration window. Resolution: xem [workspace-resolution.md#effective-packs-resolution](../../agents/pipeline/workspace-resolution.md#effective-packs-resolution).

## Validator rules

Source-of-truth là [validator-rules.md](agents/pipeline/validator-rules.md), với
exact rule-ID parity được kiểm tra với [rules.py](scripts/rules.py). Structural
errors giữ spec ở `draft`; heuristic warnings flag setup, recipe citation,
jargon, scope và acceptance criteria để reviewer quyết định, không tự suy diễn.

## Retrieval behavior

Pack route bằng intent phrase cụ thể như `thiết kế công cụ`, `mở rộng công cụ`, `technology recipe`, hoặc `tool catalog`. Các từ quá rộng như `build`, `sửa`, `script`, `idea` đã bị loại để không kéo recipe library vào mọi task.

## Verification

```bash
contextd pack-validate --pack pack-solo-builder --format text
contextd context "Thiết kế công cụ cá nhân từ recipe" --preview --format json
python scripts/validate.py --file <tool-spec-fixture> --workspace <workspace-with-pack>
```
