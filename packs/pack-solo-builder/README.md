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

## Components

- `tool-design`: thiết kế 1 tool mới từ ý tưởng thô → spec
- `tool-extend`: thêm/sửa tính năng cho tool đã có
- `recipe`: catalog tech stack đề xuất per task type
- `tool-catalog`: scan + dedup các tool đã build

## Triết lý

1. **Spec trước, code sau** — Claude KHÔNG sinh code khi spec chưa rõ. Nếu rõ rồi, code là việc của session khác.
2. **Recipe-driven** — mọi tech recommendation đến từ `recipes/` library, không tự sáng tạo. Nếu task không match recipe nào → STOP và yêu cầu user mô tả thêm.
3. **Cross-platform first** — recipe luôn cover cả Linux + Windows. Trên Windows, recommend Docker + docker-compose để dependency không vỡ.
4. **1 tool = 1 mục đích** — không có "tool đa năng". Tool to → tách nhỏ thành nhiều tools.
5. **Plain language** — mọi reasoning bằng ngôn ngữ đời thường, không jargon.

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
- Mọi recommendation kèm "vì sao chọn" + "vì sao không alternative"
- Windows-specific: nếu task cần dependency phức tạp (image processing, PDF, share team) → recommend Docker

## Recipe library

Hiện có 10 recipes (xem [`recipes/README.md`](recipes/README.md)). User có thể tự thêm bằng `templates/tool-recipe.md`.

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

| Rule | Severity | Check |
|------|----------|-------|
| `pack-solo-builder-spec-missing-system-map` | error | Spec thiếu section "System Map" |
| `pack-solo-builder-spec-missing-stack` | error | Spec thiếu section "Tech Stack" |
| `pack-solo-builder-spec-missing-acceptance` | error | Spec thiếu "Acceptance Criteria" |
| `pack-solo-builder-spec-missing-problem` | error | Spec thiếu "Problem" |
| `pack-solo-builder-recipe-not-in-library` | warn  | Spec mention tech không có trong `recipes/` |
| `pack-solo-builder-jargon-without-explain` | warn  | Spec dùng từ kỹ thuật không có 1-line explain |
| `pack-solo-builder-multi-purpose-tool` | warn  | Spec mô tả > 1 mục đích (vi phạm "1 tool = 1 mục đích") |
