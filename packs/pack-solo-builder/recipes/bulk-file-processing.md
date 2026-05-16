# Recipe: Bulk File Processing

Process nhiều file (CSV, Excel, PDF, images) thành output mới — lọc, gộp, transform, rename, extract.

## When to use

Task signals từ user:
- "Tôi có nhiều file Excel/CSV/PDF cần xử lý cùng kiểu"
- "Hằng tuần tôi mở 50 file Excel để copy-paste cùng 1 cột"
- "Cần gộp nhiều CSV thành 1 file"
- "Cần đổi tên hàng loạt file theo rule"
- "Cần extract data từ nhiều PDF"

Không phải:
- Chỉ 1 file → recipe `formula-calculator-cli` đủ
- Cần xem trực quan → recipe `data-visualization`

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Language | Python 3.11+ | Có sẵn library xử lý mọi format file |
| Excel | `openpyxl` (đọc/ghi `.xlsx`) | KHÔNG dùng `xlrd` (deprecated cho .xlsx) |
| CSV | `pandas` | Built-in `csv` cũng được nhưng pandas tiện filter/group |
| PDF (extract text) | `pdfplumber` | Tốt hơn `PyPDF2` cho table extraction |
| PDF (extract images) | `pdf2image` + `Pillow` | Cần Poppler binary (Docker giải quyết hết) |
| CLI args | `argparse` (built-in) | Không cần thư viện thêm |

### Linux/macOS setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas openpyxl pdfplumber
```

### Windows native (NẾU chỉ làm CSV/Excel)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install pandas openpyxl
```

### Windows + Docker (recommend nếu đụng PDF)

PDF processing trên Windows native cần install Poppler thủ công — Docker tránh hết.

```yaml
# docker-compose.yml
services:
  bulk-tool:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - .:/app
      - ./input:/input
      - ./output:/output
    command: bash -c "pip install -q -r requirements.txt && python tool.py"
```

```txt
# requirements.txt
pandas
openpyxl
pdfplumber
```

```bash
docker compose run --rm bulk-tool
```

## Trade-offs

**Vì sao Python**: ngôn ngữ có ecosystem mạnh nhất cho file processing. Pandas + openpyxl + pdfplumber là combo cover 90% bulk task.

**Vì sao KHÔNG**:
- **Excel macro VBA**: chỉ chạy trong Excel, không reuse cho CSV/PDF, khó automate.
- **Power Query / Power Automate**: GUI tốt nhưng vendor lock-in Microsoft, học thêm mất 1 tuần, không version-control được logic.
- **Bash + awk/sed**: nhanh cho text thuần nhưng không xử lý Excel/PDF native.
- **Node.js**: được, nhưng library Excel/PDF không bằng Python.

## Skeleton

```python
# tool.py
import argparse
from pathlib import Path
import pandas as pd

def process_one(input_path: Path, output_dir: Path) -> dict:
    """Process 1 file. Return summary dict."""
    df = pd.read_excel(input_path)  # hoặc pd.read_csv
    # transform here
    filtered = df[df["Status"] == "Open"]
    out_path = output_dir / f"{input_path.stem}-filtered.xlsx"
    filtered.to_excel(out_path, index=False)
    return {"file": input_path.name, "in_rows": len(df), "out_rows": len(filtered)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir", type=Path, help="Folder chứa file input")
    ap.add_argument("--output", type=Path, default=Path("output"), help="Folder ghi output")
    ap.add_argument("--pattern", default="*.xlsx", help="File pattern, vd *.xlsx, *.csv")
    args = ap.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    files = sorted(args.input_dir.glob(args.pattern))
    print(f"Found {len(files)} files")
    summaries = [process_one(f, args.output) for f in files]
    for s in summaries:
        print(f"  {s['file']}: {s['in_rows']} -> {s['out_rows']} rows")

if __name__ == "__main__":
    main()
```

Chạy:
```bash
python tool.py ./input --output ./output --pattern "*.xlsx"
```

## Decision tree

✅ **Match recipe này KHI**:
- Input ≥ 2 file cùng format
- Logic xử lý mỗi file giống nhau
- User OK với chạy CLI command

❌ **KHÔNG match KHI**:
- Cần GUI để click → recipe `desktop-gui-simple`
- Cần share team chạy không cài Python → recipe `team-shared-web-tool`
- Cần chạy tự động định kỳ → recipe `scheduled-recurring-task` (build trên recipe này + add scheduler)
- Cần chart/dashboard → recipe `data-visualization`
