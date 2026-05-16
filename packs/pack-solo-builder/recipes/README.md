# Recipe Library — pack-solo-builder

Mỗi recipe = 1 stack đề xuất cho 1 kiểu task. Slash `/tool-design` đọc library này để recommend tech.

## Format mỗi recipe

5 section bắt buộc:

1. **When to use** — task signals (user trả lời discovery như nào thì match recipe này)
2. **Tech Stack** — Linux + Windows variants, có Docker note nếu phù hợp
3. **Trade-offs** — vì sao chọn cái này, vì sao không alternative
4. **Skeleton commands** — copy-paste để start ngay
5. **Decision tree mini** — match recipe này KHI ... và KHÔNG match KHI ...

## Recipes hiện có

| Recipe | Tag |
|--------|-----|
| [bulk-file-processing](bulk-file-processing.md) | `batch`, `excel`, `csv`, `pdf` |
| [formula-calculator-cli](formula-calculator-cli.md) | `compute`, `cli`, `formula` |
| [daily-form-with-history](daily-form-with-history.md) | `form`, `record`, `history`, `streamlit` |
| [data-visualization](data-visualization.md) | `chart`, `dashboard`, `plot` |
| [scheduled-recurring-task](scheduled-recurring-task.md) | `schedule`, `cron`, `automation` |
| [team-shared-web-tool](team-shared-web-tool.md) | `share`, `team`, `web`, `docker` |
| [pdf-report-generator](pdf-report-generator.md) | `report`, `pdf`, `print` |
| [desktop-gui-simple](desktop-gui-simple.md) | `gui`, `desktop`, `tkinter`, `personal` |
| [api-data-fetcher](api-data-fetcher.md) | `api`, `fetch`, `external-data` |
| [local-database-manager](local-database-manager.md) | `crud`, `database`, `sqlite`, `records` |

## Add recipe mới

1. Copy `templates/tool-recipe.md` vào file mới `packs/pack-solo-builder/recipes/{name}.md`
2. Fill 5 section
3. Add row vào table phía trên
4. (Optional) Add signal vào `agents/pipeline/retrieval-map.md` Recipe Match table

## Cross-platform principle

Mọi recipe PHẢI cover:
- **Linux/macOS**: native venv (đơn giản nhất)
- **Windows**: native venv NẾU không có deps phức tạp; Docker + docker-compose NẾU có deps phức tạp (image, PDF, share)

Nếu recipe không apply được cross-platform (vd GUI native), note rõ trong file.
