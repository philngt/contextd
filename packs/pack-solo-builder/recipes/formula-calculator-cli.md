# Recipe: Formula Calculator (CLI)

Tool nhập vài giá trị → tính theo công thức → in kết quả. Chạy thi thoảng, không cần lưu lịch sử.

## When to use

Task signals:
- "Convert đơn vị (mm ↔ inch, °C ↔ °F)"
- "Tính tổng/chiết khấu theo business rule đã được approve"
- "Thay công thức spreadsheet ổn định bằng một lệnh có test"
- "Áp công thức Excel rườm rà thành 1 lệnh nhanh"

Không phải:
- Cần lưu lịch sử mỗi lần tính → recipe `daily-form-with-history`
- Tính trên nhiều dòng dữ liệu → recipe `bulk-file-processing`
- Công thức ảnh hưởng y tế, pháp lý, tài chính, kết cấu hoặc an toàn nhưng chưa có authoritative source + qualified review → giữ spec `draft`, recipe này không cung cấp domain formula

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Language | Workspace-supported Python, pinned | Chọn version đã test trên target environment |
| CLI args | `argparse` (built-in) | Hoặc `typer` nếu muốn UX đẹp hơn |
| Math | built-in `decimal`/`math`; `numpy` chỉ khi data shape cần | Numeric type, rounding và units phải explicit |
| Output | `print` + table với `rich` (optional) | rich = library in màn hình đẹp |

### Linux/macOS/Windows native

```bash
python3 -m venv .venv
source .venv/bin/activate     # Linux/macOS
.venv\Scripts\Activate.ps1    # Windows PowerShell
pip install rich              # optional, for pretty output
```

Container thường không tạo lợi ích cho calculator một file. Dùng native environment trên target đã test; chỉ thêm container khi dependency/isolation requirement thực sự có.

## Trade-offs

**Vì sao Python CLI**: phù hợp khi input/output nhỏ, người dùng chấp nhận terminal và cần một implementation có tests/versioned formula thay vì cell spreadsheet dễ sửa nhầm.

**Vì sao KHÔNG**:
- **Spreadsheet**: vẫn phù hợp khi user cần inspect/ad-hoc edit; CLI phù hợp hơn khi formula cần version/test/repeatability.
- **Web/desktop form**: chọn khi accessibility, discoverability hoặc non-terminal workflow quan trọng hơn footprint.
- **JS/TS**: hợp nếu runtime hiện có là Node/browser; không đổi stack chỉ vì recipe example dùng Python.

## Skeleton

```python
# temperature.py — ví dụ conversion có formula công khai, không phải domain authority
import argparse
from decimal import Decimal

def celsius_to_fahrenheit(celsius: Decimal) -> Decimal:
    return (celsius * Decimal(9) / Decimal(5)) + Decimal(32)

def main():
    ap = argparse.ArgumentParser(description="Convert Celsius to Fahrenheit")
    ap.add_argument("--celsius", type=Decimal, required=True)
    args = ap.parse_args()
    result = celsius_to_fahrenheit(args.celsius)
    print(f"{args.celsius} °C = {result.normalize()} °F")

if __name__ == "__main__":
    main()
```

Chạy:
```bash
python temperature.py --celsius 25
```

## Decision tree

✅ **Match recipe này KHI**:
- Input đủ nhỏ/rõ để CLI flags hoặc stdin không gây nhầm units
- Output text/number ngắn, in terminal đủ
- Không cần lưu lịch sử
- Chạy thi thoảng (không tự động)

❌ **KHÔNG match KHI**:
- Cần lưu mỗi lần tính → `daily-form-with-history`
- Cần share team không cài Python → `team-shared-web-tool`
- Cần GUI form → `desktop-gui-simple`
- Cần plot kết quả → mix với `data-visualization`
- Công thức high-impact chưa có evidence/reviewer/fixtures → không implement; resolve domain contract trước
