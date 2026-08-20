# Recipe Library — pack-solo-builder

Mỗi recipe = 1 stack đề xuất cho 1 kiểu task. Slash `/tool-design` đọc library này để recommend tech.

## Format mỗi recipe

5 section bắt buộc:

1. **When to use** — task signals (user trả lời discovery như nào thì match recipe này)
2. **Tech Stack** — target environments thực tế, version/dependency đã test, container chỉ khi có rationale
3. **Trade-offs** — lý do chọn cho target hiện tại; chỉ so sánh alternative material
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
| [multi-agent-orchestrator](multi-agent-orchestrator.md) | `agent`, `orchestrate`, `claude`, `gemini`, `codex`, `cli` |

## Add recipe mới

1. Copy `templates/tool-recipe.md` vào file mới `packs/pack-solo-builder/recipes/{name}.md`
2. Fill 5 section
3. Add row vào table phía trên
4. (Optional) Add signal vào `agents/pipeline/retrieval-map.md` Recipe Match table

## Platform and evidence principle

- Recipe phải nêu environment đã test và cách pin runtime/dependencies; không claim cross-platform nếu chưa verify trên các target đó.
- Native setup là lựa chọn hợp lệ trên mọi OS. Container/Compose chỉ thêm khi isolation, portability, deployment hoặc system dependency tạo lợi ích rõ.
- Công thức, regulation, scraping/API policy và high-impact workflow phải cite authority bên ngoài recipe; unresolved evidence giữ tool spec ở trạng thái `draft`.
- Nếu một target không được hỗ trợ hoặc chưa test, ghi rõ thay vì copy setup boilerplate.

## Container baseline (when a recipe justifies it)

Install dependencies at image build time from a reviewed lock file; container startup runs only the tool. Set `PYTHON_IMAGE` to a workspace-tested tag or digest and keep the resolved value in build/release evidence.

```dockerfile
ARG PYTHON_BASE
FROM ${PYTHON_BASE}
WORKDIR /app
COPY requirements.lock .
RUN python -m pip install --no-cache-dir -r requirements.lock
COPY . .
```

```yaml
# compose.yaml
services:
  tool:
    build:
      context: .
      args:
        PYTHON_BASE: ${PYTHON_IMAGE:?set a tested Python image tag or digest}
```

Do not `pip install` on every `docker compose up`; it makes startup network-dependent and silently changes dependencies.
