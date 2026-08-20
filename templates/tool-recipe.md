---
type: Recipe
title: "Recipe: {Recipe Name}"
description: "{1-2 dòng: kiểu task nào, stack gì, ai dùng}"
tags: [recipe]
---

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
| Language/runtime | {runtime + tested version/profile} | Pin from the target environment, not from this template |
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

### Container target (optional; only when the deployment/runtime owner requires it)

```yaml
# compose.yaml
services:
  {service-name}:
    build:
      context: .
      args:
        RUNTIME_BASE: ${RUNTIME_IMAGE:?set a tested image tag or digest}
    working_dir: /app
    command: python tool.py
```

```dockerfile
# Dockerfile
ARG RUNTIME_BASE
FROM ${RUNTIME_BASE}
WORKDIR /app
COPY requirements.lock .
RUN python -m pip install --no-cache-dir -r requirements.lock
COPY . .
CMD ["python", "tool.py"]
```

## Trade-offs

**Vì sao chọn stack này**:
- {Lý do 1 — concrete benefit}
- {Lý do 2}

**Material alternatives đã cân nhắc**:
- **{Alternative}**: {trade-off hoặc lý do không chọn cho target hiện tại}

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
