# Recipe: API Data Fetcher

Pull data từ API ngoài (REST, GraphQL, web scraping) → cache local → process. Vd: tỷ giá, giá vàng, tracking shipment, tin tức.

## When to use

Task signals:
- "Cần pull tỷ giá USD/VND mỗi ngày từ ngân hàng"
- "Lấy giá vật liệu từ website nhà cung cấp"
- "Track trạng thái đơn hàng từ API logistics"
- "Aggregate data từ nhiều API về 1 chỗ"

Không phải:
- API gọi 1 lần → script đơn giản, không cần recipe riêng
- Real-time stream (WebSocket) → ngoài scope solo builder

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Language | Workspace-supported Python, pinned | Pin cùng HTTP/parser dependencies đã test |
| HTTP client | `requests` (sync) hoặc `httpx` (async) | Chọn theo concurrency/cancellation/runtime contract, không theo popularity claim |
| HTML scraping | `beautifulsoup4` + `lxml` | Nếu API không có, scrape web |
| Cache | SQLite hoặc JSON file | Tránh hit API lặp lại |
| Retry | `urllib3.Retry` through `requests` adapter | Scope retry to idempotent/transient failures and respect `Retry-After` |
| Schedule | Recipe `scheduled-recurring-task` | Wrap recipe này nếu cần auto |

### Linux/macOS/Windows native

```bash
python3 -m venv .venv
source .venv/bin/activate     # Linux/macOS
.venv\Scripts\Activate.ps1    # Windows PowerShell
pip install requests beautifulsoup4
```

Native setup is the default for this small client. Add a container only when scheduling, isolation or deployment ownership justifies it.

### Container option (nếu schedule/dependency isolation có rationale)

```yaml
services:
  fetcher:
    build:
      context: .
      args:
        PYTHON_BASE: ${PYTHON_IMAGE:?set a tested Python image tag or digest}
    working_dir: /app
    volumes: ["./cache:/app/cache"]
    command: python fetch.py
```

## Trade-offs

**Vì sao Python + requests**:
- `requests` fits a small synchronous GET workflow and exposes explicit timeout/status handling.
- Python parsers can cover the response formats selected for this tool; validate schema and fixtures rather than assuming every format.
- SQLite/JSON can implement a local cache when freshness/data policy allows.

**Vì sao KHÔNG**:
- **curl + bash**: OK cho 1 lệnh, khó parse JSON / handle retry / cache.
- **Postman**: GUI manual, không automate được.
- **Node.js client**: hợp nếu target runtime/team already owns Node; compare cancellation, schema validation and downstream processing needs.
- **Selenium/Playwright cho mọi scrape**: overkill — chỉ dùng khi site có JS heavy. Tĩnh thì BeautifulSoup đủ.

## Skeleton

```python
# fetch.py — Pull tỷ giá USD/VND từ API
import json
import os
from pathlib import Path
from datetime import datetime, date
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

CACHE = Path("cache/usd-vnd.json")
CACHE.parent.mkdir(exist_ok=True)
TIMEOUT = (
    float(os.environ.get("FETCH_CONNECT_TIMEOUT_SECONDS", "5")),
    float(os.environ.get("FETCH_READ_TIMEOUT_SECONDS", "20")),
)

SESSION = requests.Session()
SESSION.mount("https://", HTTPAdapter(max_retries=Retry(
    total=int(os.environ.get("FETCH_RETRY_TOTAL", "3")),
    backoff_factor=float(os.environ.get("FETCH_RETRY_BACKOFF", "0.5")),
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods={"GET"},
    respect_retry_after_header=True,
)))

def fetch_rate() -> dict:
    """Example GET. Replace URL and defaults with the provider contract."""
    url = "https://api.example.com/fx/usd-vnd"
    r = SESSION.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def get_today_rate() -> dict:
    """Use cache if fetched today; else fetch fresh."""
    today = date.today().isoformat()
    if CACHE.exists():
        cached = json.loads(CACHE.read_text())
        if cached.get("date") == today:
            return cached
    # cache miss or stale
    data = fetch_rate()
    payload = {
        "date": today,
        "fetched_at": datetime.now().isoformat(),
        "rate": data,
    }
    CACHE.write_text(json.dumps(payload, indent=2))
    return payload

if __name__ == "__main__":
    rate = get_today_rate()
    print(f"USD/VND on {rate['date']}: {rate['rate']}")
```

### Web scraping example (khi không có API)

```python
import requests
import os
from bs4 import BeautifulSoup

def scrape_steel_price():
    url = "https://example-supplier.vn/gia-thep"
    r = requests.get(
        url,
        timeout=(5, 20),  # replace with configured provider/SLO values
        headers={"User-Agent": os.environ["FETCHER_USER_AGENT"]},
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    prices = []
    for row in soup.select("table.price-list tr"):
        cells = row.find_all("td")
        if len(cells) >= 2:
            prices.append({"product": cells[0].text.strip(), "price": cells[1].text.strip()})
    return prices
```

## Best practices

- Cache chỉ khi freshness/data policy cho phép; key, TTL/revalidation và stale behavior theo provider contract.
- Mọi request có configured connect/read deadline + cancellation; giá trị dựa trên upstream SLO và task frequency.
- Retry chỉ operation idempotent/transient failure, có backoff/jitter và tôn trọng `Retry-After`/provider limit.
- Scraping chỉ khi terms/permission cho phép; dùng identifying User-Agent/contact thay vì giả browser và tuân robots/rate policy được publish.
- **KHÔNG hardcode API key** — đặt trong env var hoặc file `.env` (không commit).

## Decision tree

✅ **Match recipe này KHI**:
- Cần pull data từ API/website ngoài
- Lưu local để process tiếp
- Có thể delay vài giây ↔ giờ (không cần realtime)

❌ **KHÔNG match KHI**:
- Realtime stream (WebSocket, SSE) → ngoài scope
- API có auth phức tạp (OAuth flow) → spec cần thêm step auth
- Dữ liệu cực lớn (TB/ngày) → cân nhắc data engineering pipeline, ngoài scope
