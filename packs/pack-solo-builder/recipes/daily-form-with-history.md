# Recipe: Daily Form with History

Tool dạng form nhập data hằng ngày + lưu lịch sử để xem lại sau. Vd: nhật ký bảo trì máy, log đơn hàng, ghi chỉ số.

## When to use

Task signals:
- "Hằng ngày cần nhập 5-10 chỉ số rồi xem lại lịch sử"
- "Tracking máy móc bảo trì: ngày, máy, kỹ thuật viên, kết quả"
- "Log đơn hàng nhỏ + xem báo cáo cuối tháng"
- "Nhật ký công việc + filter theo tuần"

Không phải:
- Chỉ tính toán không cần lưu → `formula-calculator-cli`
- Cần share team đa người dùng → `team-shared-web-tool` (recipe này build local trước, share sau)
- Records phức tạp đa bảng → cân nhắc Postgres (ngoài recipe library)

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Language | Python 3.11+ | Streamlit là Python framework |
| UI Framework | `streamlit` | Web app build cực nhanh, không cần HTML/CSS |
| Database | `sqlite3` (built-in Python) | File `.db` đơn lẻ, copy đi đâu cũng chạy |
| Date/time | `datetime` (built-in) | Đủ cho daily log |
| Display | `pandas` (cho bảng lịch sử) | Streamlit hiển thị DataFrame đẹp tự động |

### Linux/macOS native

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit pandas
streamlit run tool.py
# Mở browser http://localhost:8501
```

### Windows native

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install streamlit pandas
streamlit run tool.py
```

### Windows + Docker (recommend nếu share đồng nghiệp)

```yaml
# docker-compose.yml
services:
  daily-form:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - .:/app
      - ./data:/app/data    # SQLite file persist ở host
    ports:
      - "8501:8501"
    command: bash -c "pip install -q streamlit pandas && streamlit run tool.py --server.address=0.0.0.0"
```

```bash
docker compose up
# Browser http://localhost:8501
```

## Trade-offs

**Vì sao Streamlit + SQLite**:
- Streamlit: viết Python thuần, ra web app trong < 50 dòng. Không cần HTML/CSS/JS.
- SQLite: 0 setup, 0 server, file nhỏ, backup = copy 1 file.

**Vì sao KHÔNG**:
- **Google Sheets / Airtable**: cloud lock-in, dữ liệu rời máy, khó offline. Có thể OK nếu OK với cloud.
- **Excel + macro**: phải mở Excel, không có form UI tốt, dễ corrupt khi nhiều dòng.
- **Flask/FastAPI**: phải tự viết HTML form + route, mất thêm 4-5 lần thời gian Streamlit.
- **Postgres**: overkill cho 1 user, cần server.
- **MongoDB**: không có schema → dễ lỗi data corruption khi fields mismatch.

## Skeleton

```python
# tool.py — Daily maintenance log
import streamlit as st
import sqlite3
from datetime import date
import pandas as pd
from pathlib import Path

DB = Path("data/maintenance.db")
DB.parent.mkdir(exist_ok=True)

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date DATE,
            machine TEXT,
            technician TEXT,
            issue TEXT,
            resolved INTEGER
        )
        """)

def insert(log_date, machine, technician, issue, resolved):
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO log(log_date, machine, technician, issue, resolved) VALUES (?,?,?,?,?)",
            (log_date.isoformat(), machine, technician, issue, int(resolved))
        )

def fetch_all() -> pd.DataFrame:
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query("SELECT * FROM log ORDER BY log_date DESC, id DESC", con)

# UI
init_db()
st.title("Nhật ký bảo trì máy")

with st.form("entry", clear_on_submit=True):
    col1, col2 = st.columns(2)
    log_date = col1.date_input("Ngày", value=date.today())
    machine = col2.text_input("Máy", placeholder="Vd: CNC-01")
    technician = st.text_input("Kỹ thuật viên")
    issue = st.text_area("Sự cố / công việc", height=80)
    resolved = st.checkbox("Đã xử lý xong")
    if st.form_submit_button("Lưu"):
        insert(log_date, machine, technician, issue, resolved)
        st.success("Đã lưu!")

st.divider()
st.subheader("Lịch sử")
df = fetch_all()
machine_filter = st.multiselect("Filter máy", options=sorted(df["machine"].unique()) if not df.empty else [])
if machine_filter:
    df = df[df["machine"].isin(machine_filter)]
st.dataframe(df, use_container_width=True)
st.caption(f"Tổng: {len(df)} record")
```

## Decision tree

✅ **Match recipe này KHI**:
- 1 user nhập, cần xem lại lịch sử
- Schema đơn giản (5-15 fields, 1 bảng)
- OK với web UI mở trong browser
- Cần search/filter cơ bản

❌ **KHÔNG match KHI**:
- Cần đa user concurrent → cân nhắc Postgres hoặc Airtable
- Cần GUI native không dùng browser → `desktop-gui-simple`
- Records cực nhiều bảng (>5 bảng có quan hệ) → cần thiết kế DB nghiêm túc, ngoài recipe
- Chỉ 1 lần tính, không lưu → `formula-calculator-cli`
