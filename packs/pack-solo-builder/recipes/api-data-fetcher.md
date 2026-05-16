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
| Language | Python 3.11+ | |
| HTTP client | `requests` (sync) hoặc `httpx` (async) | requests đủ cho 99% case |
| HTML scraping | `beautifulsoup4` + `lxml` | Nếu API không có, scrape web |
| Cache | SQLite hoặc JSON file | Tránh hit API lặp lại |
| Retry | `tenacity` | Auto retry khi network fail |
| Schedule | Recipe `scheduled-recurring-task` | Wrap recipe này nếu cần auto |

### Linux/macOS/Windows native

```bash
python3 -m venv .venv
source .venv/bin/activate     # Linux/macOS
.venv\Scripts\Activate.ps1    # Windows PowerShell
pip install requests beautifulsoup4 tenacity
```

Recipe này không cần Docker — `requests` không có system deps.

### Windows + Docker (nếu pair với scheduled-recurring-task)

```yaml
services:
  fetcher:
    image: python:3.11-slim
    working_dir: /app
    volumes: [".:/app", "./cache:/app/cache"]
    command: bash -c "pip install -q -r requirements.txt && python fetch.py"
```

## Trade-offs

**Vì sao Python + requests**:
- `requests` API rất sạch, code ngắn
- Có thư viện cho mọi format response (JSON, XML, HTML scraping)
- Cache với SQLite/JSON đơn giản

**Vì sao KHÔNG**:
- **curl + bash**: OK cho 1 lệnh, khó parse JSON / handle retry / cache.
- **Postman**: GUI manual, không automate được.
- **Node.js + axios**: được, nhưng hệ Python tích hợp phần process data (pandas) tốt hơn.
- **Selenium/Playwright cho mọi scrape**: overkill — chỉ dùng khi site có JS heavy. Tĩnh thì BeautifulSoup đủ.

## Skeleton

```python
# fetch.py — Pull tỷ giá USD/VND từ API
import json
from pathlib import Path
from datetime import datetime, date
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

CACHE = Path("cache/usd-vnd.json")
CACHE.parent.mkdir(exist_ok=True)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def fetch_rate() -> dict:
    """Pull from a public FX API. Replace URL with real one."""
    url = "https://api.example.com/fx/usd-vnd"
    r = requests.get(url, timeout=10)
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
from bs4 import BeautifulSoup

def scrape_steel_price():
    url = "https://example-supplier.vn/gia-thep"
    r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
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

- **LUÔN có cache** — đừng hit API mỗi lần script chạy. Tốn quota + chậm.
- **LUÔN có timeout** trên `requests.get` — 10-30 giây. Không để treo vô tận.
- **LUÔN retry với backoff** — network fail là chuyện bình thường, không crash script.
- **LUÔN có User-Agent** khi scrape — server từ chối request không có UA.
- **LUÔN respect robots.txt** + rate limit khi scrape — 1 request / 2-5 giây.
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
