# Recipe: {Recipe Name}

> 1-2 dòng mô tả: kiểu task này dùng stack gì, ai dùng cho mục đích gì.

## When to use

Task signals từ user (cách user mô tả task của họ):
- "{example signal 1}"
- "{example signal 2}"
- "{example signal 3}"

Không phải:
- {anti-pattern 1 → recipe khác phù hợp hơn}
- {anti-pattern 2}

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Language | {Python 3.11+ / Node / ...} | |
| {Component 2} | {choice} | {1-line note} |
| {Component 3} | {choice} | |

### Linux/macOS

```bash
{install commands}
```

### Windows native

```powershell
{install commands}
```

### Windows + Docker (recommend nếu deps phức tạp)

```yaml
# docker-compose.yml
services:
  {service-name}:
    image: python:3.11-slim
    working_dir: /app
    volumes: [".:/app"]
    command: bash -c "pip install -q {deps} && python tool.py"
```

## Trade-offs

**Vì sao chọn stack này**:
- {Lý do 1 — concrete benefit}
- {Lý do 2}

**Vì sao KHÔNG alternative**:
- **{Alternative 1}**: {1 câu lý do không chọn}
- **{Alternative 2}**: {1 câu lý do}
- **{Alternative 3}**: {1 câu lý do}

## Skeleton

```python
# {filename} — {1-line description}
{code skeleton complete enough to copy-paste-run}
```

Chạy:
```bash
{example command}
```

## Decision tree

✅ **Match recipe này KHI**:
- {Condition 1 — concrete}
- {Condition 2}
- {Condition 3}

❌ **KHÔNG match KHI**:
- {Anti-condition 1 → recipe khác}
- {Anti-condition 2 → recipe khác}
- {Anti-condition 3}

## Notes

- {Best practice / gotcha / common mistake}
- {Performance note nếu relevant}
- {Security/data note nếu relevant}
