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
| Language | Workspace-supported Python, pinned | Phù hợp với pandas/Plotly stack trong recipe; verify bằng dataset thật |
| Framework | `streamlit` (dashboard) hoặc direct render | Chọn theo interaction/deployment contract |
| Plot library | `plotly` (interactive) hoặc `matplotlib` (static) | Verify accessibility, export/font and dataset-size behavior |
| Data | `pandas` candidate | Validate schema/types/units before aggregation |

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

### Container option (nếu share/dependency isolation có rationale)

```yaml
services:
  dashboard:
    build:
      context: .
      args:
        PYTHON_BASE: ${PYTHON_IMAGE:?set a tested Python image tag or digest}
    working_dir: /app
    ports: ["8501:8501"]
    command: streamlit run dashboard.py --server.address=0.0.0.0
```

## Trade-offs

**Vì sao Streamlit + Plotly**: phù hợp dashboard Python nhỏ cần filter/hover và versioned transformations; verify keyboard/screen-reader fallback và static export nếu audience cần.

**Vì sao KHÔNG**:
- **Spreadsheet chart**: hợp exploratory/manual ownership; compare refresh/reproducibility/collaboration needs.
- **BI platform**: hợp governed multi-source analytics nếu organization đã sở hữu access/model/deployment stack.
- **D3/custom web**: hợp specialized interaction/visual grammar khi team owns web implementation.
- **Grafana/observability UI**: hợp operational time-series and alerts; không mặc định cho business dataset.
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

required = {"month", "product", "revenue"}
missing = required - set(df.columns)
if missing:
    st.error(f"Missing required columns: {', '.join(sorted(missing))}")
    st.stop()
df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
if df["revenue"].isna().any():
    st.error("Column 'revenue' contains invalid numeric values")
    st.stop()

# Filters
col1, col2 = st.columns(2)
months = col1.multiselect("Month", sorted(df["month"].unique()), default=list(df["month"].unique()))
products = col2.multiselect("Product", sorted(df["product"].unique()), default=list(df["product"].unique()))
filtered = df[df["month"].isin(months) & df["product"].isin(products)]

# KPIs
st.subheader("KPIs")
k1, k2, k3 = st.columns(3)
k1.metric("Total revenue", f"{filtered['revenue'].sum():,.0f}")
k2.metric("Average revenue per input row", f"{filtered['revenue'].mean():,.0f}")
k3.metric("Input rows", len(filtered))

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
- Visual/state complexity vẫn phù hợp một small dashboard và có accessible data-table fallback

❌ **KHÔNG match KHI**:
- Cần PDF report fix layout → `pdf-report-generator`
- Cần real-time streaming → cân nhắc Grafana, ngoài recipe
- 1 chart đơn lẻ in giấy → matplotlib + savefig đủ, không cần Streamlit
- Cần BI enterprise (filter phức tạp, nhiều data source) → Power BI/Tableau, ngoài recipe
