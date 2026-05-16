# Recipe: PDF Report Generator

Sinh PDF từ data + template. Vd: invoice, biên bản kiểm tra, báo cáo định kỳ, certificate.

## When to use

Task signals:
- "Cần in báo cáo PDF với layout cố định"
- "Generate invoice PDF từ database"
- "Biên bản nghiệm thu có logo công ty"
- "Certificate / hợp đồng template + fill data"

Không phải:
- Cần dashboard interactive → recipe `data-visualization`
- Output là file Excel cho user edit → recipe `bulk-file-processing`

## Tech Stack

2 hướng tuỳ độ phức tạp layout:

| Hướng | Library | Khi nào |
|-------|---------|---------|
| HTML → PDF | `weasyprint` | Layout phức tạp, dùng CSS để style đẹp |
| Code → PDF trực tiếp | `reportlab` | Layout đơn giản, không quen HTML/CSS |

| Component | Chọn | Note |
|-----------|------|------|
| Language | Python 3.11+ | |
| HTML template | `jinja2` (cho weasyprint) | Render dynamic data vào HTML |
| PDF library | `weasyprint` (recommend) | HTML + CSS → PDF, layout giống browser print |
| Alternative | `reportlab` | Code Python trực tiếp draw PDF |

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
# WeasyPrint cần system libs (Pango, Cairo)
# Ubuntu/Debian:
sudo apt install libpango-1.0-0 libpangoft2-1.0-0
pip install weasyprint jinja2
```

### Windows native — KHÔNG recommend

WeasyPrint trên Windows native rất khó install (cần GTK runtime). **Chuyển sang Docker**.

### Windows + Docker (recommend)

```yaml
# docker-compose.yml
services:
  report-gen:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - .:/app
      - ./output:/output
    command: bash -c "
      apt-get update && apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 &&
      pip install -q weasyprint jinja2 &&
      python tool.py
    "
```

```bash
docker compose run --rm report-gen
```

Hoặc dùng Python image có pre-installed deps:

```yaml
services:
  report-gen:
    image: python:3.11
    # full python image (không -slim) đã có nhiều system libs
    working_dir: /app
    volumes: [".:/app", "./output:/output"]
    command: bash -c "pip install -q weasyprint jinja2 && python tool.py"
```

### Alternative: ReportLab (đơn giản hơn nếu OK với layout cơ bản)

```bash
pip install reportlab
```

ReportLab pure-Python, không system deps → chạy native mọi OS không cần Docker.

## Trade-offs

**Vì sao WeasyPrint** (cho layout phức tạp):
- Viết HTML + CSS quen thuộc, render giống browser
- Tận dụng Jinja2 template loop / conditional dễ
- Output PDF chất lượng print

**Vì sao KHÔNG**:
- **Microsoft Word + Mail Merge**: GUI, khó automate, không version-control template.
- **LibreOffice headless**: được nhưng setup phức tạp, render quirks.
- **HTML → wkhtmltopdf**: deprecated, nhiều bug, không support modern CSS.
- **Pure ReportLab**: code dài, mỗi pixel phải tự đặt — không hợp cho layout phức tạp.
- **LaTeX**: render đẹp nhất nhưng học mất tuần.

## Skeleton — WeasyPrint approach

`template.html`:
```html
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 2cm; }
  body { font-family: sans-serif; }
  .header { display: flex; align-items: center; border-bottom: 2px solid #333; padding-bottom: 10px; }
  .logo { width: 80px; }
  table { width: 100%; border-collapse: collapse; margin-top: 20px; }
  th, td { border: 1px solid #999; padding: 8px; text-align: left; }
  th { background: #eee; }
  .total { font-weight: bold; font-size: 1.1em; margin-top: 20px; text-align: right; }
</style>
</head>
<body>
  <div class="header">
    <img class="logo" src="logo.png">
    <div>
      <h1>{{ company }}</h1>
      <p>{{ address }}</p>
    </div>
  </div>

  <h2>Invoice #{{ invoice.id }}</h2>
  <p>Date: {{ invoice.date }} · Customer: {{ invoice.customer }}</p>

  <table>
    <thead>
      <tr><th>Item</th><th>Qty</th><th>Price</th><th>Subtotal</th></tr>
    </thead>
    <tbody>
      {% for item in invoice.items %}
      <tr>
        <td>{{ item.name }}</td>
        <td>{{ item.qty }}</td>
        <td>{{ "{:,.0f}".format(item.price) }}</td>
        <td>{{ "{:,.0f}".format(item.qty * item.price) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="total">Total: {{ "{:,.0f}".format(invoice.total) }} VND</div>
</body>
</html>
```

`tool.py`:
```python
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pathlib import Path

invoice = {
    "id": "INV-2026-0001",
    "date": "2026-05-15",
    "customer": "ACME Corp",
    "items": [
        {"name": "Service A", "qty": 2, "price": 500_000},
        {"name": "Service B", "qty": 1, "price": 1_200_000},
    ],
    "total": 2 * 500_000 + 1_200_000,
}

env = Environment(loader=FileSystemLoader("."))
tpl = env.get_template("template.html")
html_str = tpl.render(company="My Company", address="HCMC, Vietnam", invoice=invoice)

Path("output").mkdir(exist_ok=True)
HTML(string=html_str, base_url=".").write_pdf(f"output/{invoice['id']}.pdf")
print(f"Generated output/{invoice['id']}.pdf")
```

## Decision tree

✅ **Match recipe này KHI**:
- Output cuối là PDF (in giấy hoặc email gửi)
- Layout cố định, có template chuẩn
- Cần generate batch (nhiều file PDF cùng template)

❌ **KHÔNG match KHI**:
- Output Excel/Word để user edit → recipe khác
- Layout đơn giản, gửi email plain → text email đủ
- Cần fill PDF có sẵn (form fillable PDF) → dùng `pypdf` thay vì generate from scratch
