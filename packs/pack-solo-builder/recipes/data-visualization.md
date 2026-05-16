# Recipe: Data Visualization

Vẽ chart/dashboard từ data có sẵn (CSV, Excel, SQLite). Xem trend, compare, distribution.

## When to use

Task signals:
- "Vẽ biểu đồ doanh thu theo tháng từ file Excel"
- "Dashboard tracking KPI từ CSV xuất ra"
- "So sánh số liệu giữa nhiều dòng sản phẩm"
- "Heatmap, scatter plot, pie chart"

Không phải:
- Cần report PDF gửi → recipe `pdf-report-generator` (build trên recipe này + export)
- Cần nhập + xem live → recipe `daily-form-with-history`

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Language | Python 3.11+ | Ecosystem chart mạnh nhất |
| Framework | `streamlit` (cho dashboard) hoặc `matplotlib` (cho chart 1 lần) | Streamlit nếu cần interactive; matplotlib nếu chỉ render PNG |
| Plot library | `plotly` (interactive) hoặc `matplotlib` (static) | Plotly đẹp + zoom được; matplotlib in PDF/PNG tốt |
| Data | `pandas` | Standard cho data manipulation |

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit pandas plotly openpyxl
streamlit run dashboard.py
```

### Windows native

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install streamlit pandas plotly openpyxl
streamlit run dashboard.py
```

### Windows + Docker (nếu share team)

```yaml
services:
  dashboard:
    image: python:3.11-slim
    working_dir: /app
    volumes: [".:/app"]
    ports: ["8501:8501"]
    command: bash -c "pip install -q streamlit pandas plotly openpyxl && streamlit run dashboard.py --server.address=0.0.0.0"
```

## Trade-offs

**Vì sao Streamlit + Plotly**: dashboard trong 30-50 dòng Python, chart zoom/hover/filter ngay. So với Excel chart: code reproducible, version-control, share link không gửi file.

**Vì sao KHÔNG**:
- **Excel chart**: nhanh ban đầu nhưng manual, không update tự động khi data đổi.
- **Power BI / Tableau**: tốt nhưng đắt, học mất tuần, vendor lock-in.
- **D3.js**: cực mạnh nhưng cần JS expert, overkill.
- **Grafana**: chuyên cho metric/time-series, overkill cho ad-hoc chart.
- **matplotlib alone**: static — không interactive. OK nếu chỉ cần PNG/PDF.

## Skeleton

```python
# dashboard.py — Sales dashboard
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.title("Sales Dashboard")

# Load data
@st.cache_data
def load(path):
    return pd.read_excel(path)

uploaded = st.file_uploader("Upload Excel sales data", type=["xlsx", "csv"])
if not uploaded:
    st.info("Upload file để xem dashboard")
    st.stop()

df = pd.read_excel(uploaded) if uploaded.name.endswith(".xlsx") else pd.read_csv(uploaded)

# Filters
col1, col2 = st.columns(2)
months = col1.multiselect("Month", sorted(df["month"].unique()), default=list(df["month"].unique()))
products = col2.multiselect("Product", sorted(df["product"].unique()), default=list(df["product"].unique()))
filtered = df[df["month"].isin(months) & df["product"].isin(products)]

# KPIs
st.subheader("KPIs")
k1, k2, k3 = st.columns(3)
k1.metric("Total revenue", f"{filtered['revenue'].sum():,.0f}")
k2.metric("Avg order", f"{filtered['revenue'].mean():,.0f}")
k3.metric("Orders", len(filtered))

# Charts
st.subheader("Revenue by month")
fig1 = px.line(filtered.groupby("month")["revenue"].sum().reset_index(), x="month", y="revenue", markers=True)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Revenue by product")
fig2 = px.bar(filtered.groupby("product")["revenue"].sum().reset_index(), x="product", y="revenue")
st.plotly_chart(fig2, use_container_width=True)
```

## Decision tree

✅ **Match recipe này KHI**:
- Data đã có (CSV/Excel/SQLite)
- Cần xem trend / compare / distribution
- OK với browser-based dashboard
- 1-3 chart đủ

❌ **KHÔNG match KHI**:
- Cần PDF report fix layout → `pdf-report-generator`
- Cần real-time streaming → cân nhắc Grafana, ngoài recipe
- 1 chart đơn lẻ in giấy → matplotlib + savefig đủ, không cần Streamlit
- Cần BI enterprise (filter phức tạp, nhiều data source) → Power BI/Tableau, ngoài recipe
