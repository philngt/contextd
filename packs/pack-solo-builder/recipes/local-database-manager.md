# Recipe: Local Database Manager

Quản lý records (CRUD) trong DB local. Vd: kho linh kiện, danh bạ khách hàng, library sách, inventory dụng cụ.

## When to use

Task signals:
- "Quản lý kho linh kiện: thêm/sửa/xoá/search"
- "Danh bạ khách hàng + lịch sử giao dịch"
- "Inventory dụng cụ trong xưởng"
- "Library sách cá nhân + cho mượn tracking"

Không phải:
- Chỉ nhập + xem lịch sử (không sửa) → recipe `daily-form-with-history`
- Cần share team với auth nghiêm → ngoài scope (cần Postgres + auth)

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Language | Python 3.11+ | |
| Database | `sqlite3` (built-in) | File `.db` đơn lẻ |
| ORM (optional) | `sqlmodel` hoặc `peewee` | Nếu nhiều bảng/relation. Bỏ qua nếu 1 bảng đơn giản. |
| UI | `streamlit` | CRUD form trong 100 dòng Python |
| Migration | `alembic` (nếu dùng SQLAlchemy/sqlmodel) | Nếu schema sẽ đổi qua thời gian |

### Linux/macOS/Windows native

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit pandas sqlmodel
streamlit run tool.py
```

### Windows + Docker (recommend nếu share)

```yaml
services:
  db-manager:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - .:/app
      - ./data:/app/data    # SQLite file persist
    ports: ["8501:8501"]
    command: bash -c "pip install -q streamlit pandas sqlmodel && streamlit run tool.py --server.address=0.0.0.0"
```

## Trade-offs

**Vì sao SQLite + Streamlit**:
- SQLite: 0 setup, file copy đi đâu cũng chạy, backup = copy file
- Streamlit: form CRUD trong 100 dòng, không cần HTML
- Cross-platform (Linux/Windows/macOS)

**Vì sao KHÔNG**:
- **Excel làm DB**: dễ hỏng khi nhiều dòng, không có constraint, không multi-user.
- **Access (MS Access)**: GUI tốt nhưng vendor lock-in Microsoft, khó automate.
- **Postgres**: cần server, overkill cho 1 user. Cân nhắc nếu sau này scale.
- **MongoDB**: schemaless dễ corrupt khi nhiều fields. CRUD records cấu trúc → SQL phù hợp hơn.
- **Notion / Airtable**: cloud lock-in, dữ liệu rời máy, cost khi nhiều records.

## Skeleton — Single-table CRUD

```python
# tool.py — Inventory linh kiện
import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

DB = Path("data/inventory.db")
DB.parent.mkdir(exist_ok=True)

def init():
    with sqlite3.connect(DB) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            qty INTEGER DEFAULT 0,
            unit TEXT DEFAULT 'cái',
            location TEXT,
            note TEXT
        )
        """)

def fetch(query: str = "") -> pd.DataFrame:
    with sqlite3.connect(DB) as con:
        if query:
            return pd.read_sql_query(
                "SELECT * FROM parts WHERE sku LIKE ? OR name LIKE ? ORDER BY name",
                con, params=(f"%{query}%", f"%{query}%")
            )
        return pd.read_sql_query("SELECT * FROM parts ORDER BY name", con)

def upsert(part: dict):
    with sqlite3.connect(DB) as con:
        if part.get("id"):
            con.execute(
                "UPDATE parts SET sku=?, name=?, qty=?, unit=?, location=?, note=? WHERE id=?",
                (part["sku"], part["name"], part["qty"], part["unit"], part["location"], part["note"], part["id"])
            )
        else:
            con.execute(
                "INSERT INTO parts(sku, name, qty, unit, location, note) VALUES (?,?,?,?,?,?)",
                (part["sku"], part["name"], part["qty"], part["unit"], part["location"], part["note"])
            )

def delete(part_id: int):
    with sqlite3.connect(DB) as con:
        con.execute("DELETE FROM parts WHERE id=?", (part_id,))

# UI
init()
st.set_page_config(page_title="Inventory", layout="wide")
st.title("Quản lý kho linh kiện")

tab_list, tab_edit = st.tabs(["📋 Danh sách", "➕ Thêm / Sửa"])

with tab_list:
    q = st.text_input("Search (SKU hoặc tên)")
    df = fetch(q)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"Total: {len(df)} parts")

    st.subheader("Xoá part")
    if not df.empty:
        del_id = st.selectbox("Chọn part để xoá", options=df["id"], format_func=lambda x: f"#{x} {df[df['id']==x]['name'].iloc[0]}")
        if st.button("Xoá", type="primary"):
            delete(del_id)
            st.success(f"Đã xoá part #{del_id}")
            st.rerun()

with tab_edit:
    df = fetch()
    edit_id = st.selectbox(
        "Chọn part để sửa (hoặc 'New' để thêm mới)",
        options=[None] + list(df["id"]),
        format_func=lambda x: "➕ New" if x is None else f"#{x} {df[df['id']==x]['name'].iloc[0]}"
    )
    existing = df[df["id"]==edit_id].iloc[0].to_dict() if edit_id else {}

    with st.form("edit", clear_on_submit=False):
        col1, col2 = st.columns(2)
        sku = col1.text_input("SKU", value=existing.get("sku", ""))
        name = col2.text_input("Tên", value=existing.get("name", ""))
        col3, col4, col5 = st.columns(3)
        qty = col3.number_input("Số lượng", min_value=0, value=int(existing.get("qty", 0)))
        unit = col4.text_input("Đơn vị", value=existing.get("unit", "cái"))
        location = col5.text_input("Vị trí", value=existing.get("location", ""))
        note = st.text_area("Note", value=existing.get("note", ""))

        if st.form_submit_button("Lưu"):
            upsert({
                "id": edit_id, "sku": sku, "name": name, "qty": qty,
                "unit": unit, "location": location, "note": note
            })
            st.success("Đã lưu!")
            st.rerun()
```

## Backup strategy

SQLite = 1 file. Backup = `cp data/inventory.db data/inventory-{date}.db`. Recommend:
- **Daily auto backup**: pair với recipe `scheduled-recurring-task`
- **Trước migration schema**: backup tay
- **Cloud backup** (optional): rclone đẩy `data/*.db` lên cloud storage

## Decision tree

✅ **Match recipe này KHI**:
- Cần CRUD records cấu trúc (có schema)
- 1-3 user dùng (single-user là chính)
- Records ≤ 100k rows (SQLite handle tốt)
- OK với web UI

❌ **KHÔNG match KHI**:
- Concurrent write nhiều user → Postgres
- Records không có schema cố định → cân nhắc JSON file hoặc document DB
- Cần auth user riêng + permission → ngoài scope solo builder
- Records > 1M rows → cân nhắc Postgres / specialized DB
