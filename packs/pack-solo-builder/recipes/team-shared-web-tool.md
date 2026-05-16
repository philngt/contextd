# Recipe: Team-Shared Web Tool

Tool web app share đồng nghiệp dùng — họ KHÔNG cần cài Python/dependency, chỉ mở browser.

## When to use

Task signals:
- "Tôi build tool xong, muốn 5 đồng nghiệp dùng được"
- "Đồng nghiệp không biết code, không cài Python"
- "Cần truy cập từ máy khác trong văn phòng"
- "Muốn deploy lên 1 server LAN nội bộ"

Không phải:
- Chỉ mình dùng → recipe gốc (không cần share infra)
- Cần internet public + auth nghiêm túc → ngoài scope (cần thuê hosting + setup auth)

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Web framework | `streamlit` | Build web app cực nhanh từ Python |
| Container | `docker` + `docker-compose` | 1-command deploy |
| Reverse proxy | `nginx` (optional) | Nếu cần custom domain hoặc HTTPS |
| Storage | SQLite trong volume | Persistent, backup = copy file |

Recipe này = wrapper trên recipe khác (vd `daily-form-with-history`, `data-visualization`) + Docker deploy + multi-user consideration.

### Setup chung (Linux + Windows + macOS)

```yaml
# docker-compose.yml
services:
  web-tool:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - .:/app
      - tool-data:/app/data    # SQLite/output persist
    ports:
      - "8501:8501"
    command: bash -c "pip install -q -r requirements.txt && streamlit run app.py --server.address=0.0.0.0 --server.port=8501"
    restart: unless-stopped

volumes:
  tool-data:
```

```bash
docker compose up -d
```

Đồng nghiệp truy cập: `http://{ip-máy-chủ}:8501` từ browser. Tìm IP:
- Linux/macOS: `ip addr` hoặc `ifconfig`
- Windows: `ipconfig` (xem IPv4 Address)

### Multi-user consideration

Streamlit mặc định là **single-user session per browser tab**. Nếu cần:
- **Phân biệt user**: thêm field "Tên người dùng" vào form, lưu cùng record. KHÔNG dùng auth thật cho tool nội bộ team trust nhau.
- **Concurrent edit**: SQLite handle concurrent reads tốt, write thì khoảng 1-2 user đồng thời OK. Nhiều hơn → cân nhắc Postgres.
- **Quota / rate limit**: Streamlit không có built-in. Tool nội bộ thường không cần.

### HTTPS / custom domain (optional)

Nếu cần `https://tools.local/myapp`:

```yaml
# docker-compose.yml extended
services:
  web-tool:
    # ... như trên
    expose: ["8501"]
    # bỏ ports mapping ra ngoài

  nginx:
    image: nginx:alpine
    ports: ["443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on: [web-tool]
```

`nginx.conf`:
```nginx
server {
    listen 443 ssl;
    server_name tools.local;
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    location / {
        proxy_pass http://web-tool:8501;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Self-signed cert cho LAN:
```bash
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/key.pem -out certs/cert.pem \
  -subj "/CN=tools.local"
```

## Trade-offs

**Vì sao Docker + Streamlit**:
- 1 file `docker-compose.yml` deploy được cả Linux + Windows server
- User chỉ cần browser, không cài gì
- Update tool: `git pull && docker compose up -d --build`
- Backup: copy folder volume

**Vì sao KHÔNG**:
- **Cài Python trên từng máy đồng nghiệp**: maintenance nightmare khi version Python khác nhau.
- **Streamlit Cloud (cloud free tier)**: cloud lock-in, dữ liệu rời máy team — không OK với data nhạy cảm.
- **Heroku / Render**: cost + cloud lock-in.
- **Build SPA (React) + REST API**: 10x effort cho cùng UX.

## Skeleton

`app.py` — copy từ recipe `daily-form-with-history` hoặc `data-visualization`, không cần đổi gì khác. Streamlit chạy trong Docker giống y native.

`requirements.txt`:
```
streamlit
pandas
# + thư viện của tool gốc
```

`docker-compose.yml`: như trên.

Deploy 1 lần, dùng nhiều ngày:
```bash
# Lần đầu
docker compose up -d

# Update sau khi sửa code
docker compose restart

# Stop
docker compose down

# Xem log
docker compose logs -f
```

## Decision tree

✅ **Match recipe này KHI**:
- Tool đã build và chạy local OK
- Cần ≥ 2 người dùng
- Mạng LAN OK (không cần internet public)
- Data không quá nhạy cảm (auth nghiêm = ngoài scope)

❌ **KHÔNG match KHI**:
- Tool GUI native (Tkinter, ...) — không web-able → giữ recipe gốc, không share
- Cần auth user riêng + permission phức tạp → ngoài scope solo builder
- Cần expose internet public → cần thuê VPS + setup auth nghiêm + HTTPS Let's Encrypt — ngoài scope
- Data cực nhạy cảm (PII, finance regulated) → cần security review chuyên nghiệp
