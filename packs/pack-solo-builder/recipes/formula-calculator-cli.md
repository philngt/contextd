# Recipe: Formula Calculator (CLI)

Tool nhập vài giá trị → tính theo công thức → in kết quả. Chạy thi thoảng, không cần lưu lịch sử.

## When to use

Task signals:
- "Tính moment uốn cho dầm thép"
- "Tính tax/VAT theo công thức cụ thể"
- "Convert đơn vị (mm ↔ inch, °C ↔ °F) hàng loạt"
- "Tính BMI / liều thuốc theo cân nặng"
- "Áp công thức Excel rườm rà thành 1 lệnh nhanh"

Không phải:
- Cần lưu lịch sử mỗi lần tính → recipe `daily-form-with-history`
- Tính trên nhiều dòng dữ liệu → recipe `bulk-file-processing`

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Language | Python 3.11+ | Built-in math đủ; cần phức tạp hơn dùng `numpy` |
| CLI args | `argparse` (built-in) | Hoặc `typer` nếu muốn UX đẹp hơn |
| Math | `math` (built-in) hoặc `numpy` | numpy nếu có vector/matrix |
| Output | `print` + table với `rich` (optional) | rich = library in màn hình đẹp |

### Linux/macOS/Windows native

```bash
python3 -m venv .venv
source .venv/bin/activate     # Linux/macOS
.venv\Scripts\Activate.ps1    # Windows PowerShell
pip install rich              # optional, for pretty output
```

Recipe này SIÊU đơn giản — không cần Docker. Dùng native venv mọi OS.

## Trade-offs

**Vì sao Python CLI**: 1 file `.py`, chạy `python tool.py 100 200`, kết quả ra ngay. Không setup phức tạp, không UI bloat, copy file đi máy khác chạy luôn.

**Vì sao KHÔNG**:
- **Excel formula**: phải mở Excel, tốn 30 giây, dễ sửa nhầm cell. CLI chạy 1 giây.
- **Web form (Streamlit)**: overkill cho task tính 1 lần — Streamlit cần 5 giây boot.
- **GUI desktop (Tkinter)**: cần build dialog, code dài hơn 5x cho cùng kết quả.
- **JS/TS**: phải Node setup, library math không tốt bằng Python.

## Skeleton

```python
# moment-uon.py — tính moment uốn cho dầm chữ nhật
import argparse
import math

def moment_uon(b: float, h: float, F: float, L: float) -> dict:
    """
    b: bề rộng (mm)
    h: chiều cao (mm)
    F: lực tác dụng (N)
    L: chiều dài nhịp (mm)
    """
    W = (b * h ** 2) / 6   # mô-đun chống uốn
    M = (F * L) / 4         # moment max (dầm đơn giản, lực giữa nhịp)
    sigma = M / W          # ứng suất
    return {
        "W (mm^3)": round(W, 2),
        "M (N.mm)": round(M, 2),
        "sigma (MPa)": round(sigma, 2),
    }

def main():
    ap = argparse.ArgumentParser(description="Tính moment uốn cho dầm chữ nhật")
    ap.add_argument("--b", type=float, required=True, help="Bề rộng dầm (mm)")
    ap.add_argument("--h", type=float, required=True, help="Chiều cao dầm (mm)")
    ap.add_argument("--F", type=float, required=True, help="Lực tác dụng (N)")
    ap.add_argument("--L", type=float, required=True, help="Chiều dài nhịp (mm)")
    args = ap.parse_args()

    result = moment_uon(args.b, args.h, args.F, args.L)
    print("Kết quả:")
    for k, v in result.items():
        print(f"  {k:20s} = {v}")

if __name__ == "__main__":
    main()
```

Chạy:
```bash
python moment-uon.py --b 100 --h 200 --F 5000 --L 3000
```

## Decision tree

✅ **Match recipe này KHI**:
- Input < 10 giá trị, fit vào CLI args
- Output text/number ngắn, in terminal đủ
- Không cần lưu lịch sử
- Chạy thi thoảng (không tự động)

❌ **KHÔNG match KHI**:
- Cần lưu mỗi lần tính → `daily-form-with-history`
- Cần share team không cài Python → `team-shared-web-tool`
- Cần GUI form → `desktop-gui-simple`
- Cần plot kết quả → mix với `data-visualization`
