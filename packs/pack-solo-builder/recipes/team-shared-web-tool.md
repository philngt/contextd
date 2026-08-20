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
| Container | Docker + Compose (optional) | Reproducible deploy khi server/container target đã được chốt |
| Reverse proxy / identity | Workspace-approved gateway | TLS, authentication và access logs theo network/data policy |
| Storage | SQLite hoặc server DB theo measured concurrency | Backup/restore và write behavior phải verify |

Recipe này = wrapper trên recipe khác (vd `daily-form-with-history`, `data-visualization`) + Docker deploy + multi-user consideration.

### Container deployment example

```yaml
# compose.yaml
services:
  web-tool:
    build:
      context: .
      args:
        PYTHON_BASE: ${PYTHON_IMAGE:?set a tested Python image tag or digest}
    working_dir: /app
    volumes:
      - tool-data:/app/data    # SQLite/output persist
    ports:
      - "8501:8501"
    command: streamlit run app.py --server.address=0.0.0.0 --server.port=8501
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

### Multi-user and trust boundary

- Một field "Tên người dùng" chỉ là metadata, **không phải authentication**. Nếu identity/permissions/audit quan trọng, đặt app sau approved identity-aware proxy hoặc chuyển sang architecture có auth contract.
- Benchmark concurrent reads/writes trên target workload. SQLite có serialized write behavior; không dùng số user cố định để quyết định DB.
- LAN không tự động là trusted. Chốt network exposure, data classification, session isolation, CSRF/upload limits, rate/abuse controls và audit retention theo risk.

### HTTPS / custom domain

Không copy một TLS snippet cố định từ recipe. Dùng reverse proxy/certificate/identity mechanism đã được workspace hoặc platform owner approve; pin image/config, validate forwarded headers/origin, document certificate renewal và test access-denied paths. Nếu chưa có owner cho phần này, giới hạn app ở localhost hoặc giữ spec `draft`.

## Trade-offs

**Vì sao Docker + Streamlit**:
- `compose.yaml` mô tả cùng service/dependency contract trên target có Docker Compose đã test
- User chỉ cần browser, không cài gì
- Update tool: `git pull && docker compose up -d --build`
- Backup: application-consistent snapshot + restore test, không chỉ copy live volume

**Vì sao KHÔNG**:
- **Cài Python trên từng máy đồng nghiệp**: maintenance nightmare khi version Python khác nhau.
- **Managed cloud**: có thể phù hợp nếu data residency, auth, cost và retention được approve; không reject chỉ vì là cloud.
- **SPA + API**: hợp khi UX/API ownership, authz hoặc scale cần boundary riêng; không cần cho form nội bộ nhỏ.

## Skeleton

`app.py` — copy từ recipe `daily-form-with-history` hoặc `data-visualization`, không cần đổi gì khác. Streamlit chạy trong Docker giống y native.

`requirements.lock` (resolved versions from the tested build):
```
streamlit
pandas
# + thư viện của tool gốc
```

`compose.yaml`: như trên. Pin dependencies bằng lock file và validate resolved Compose config trước deploy.

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
- Cần share qua browser và có owner cho network/data access
- Mạng LAN OK (không cần internet public)
- Data/access risk phù hợp với controls đã thiết kế; nếu cần authz/audit nghiêm thì add engineering/security review

❌ **KHÔNG match KHI**:
- Tool GUI native (Tkinter, ...) — không web-able → giữ recipe gốc, không share
- Cần auth user riêng + permission phức tạp → ngoài scope solo builder
- Cần expose internet public → cần thuê VPS + setup auth nghiêm + HTTPS Let's Encrypt — ngoài scope
- Data cực nhạy cảm (PII, finance regulated) → cần security review chuyên nghiệp
