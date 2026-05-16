# Workspace — {Company / Project Name}

## Identity

- Company: {tên công ty}
- Role: {vị trí của user trong công ty này}
- Period: {YYYY-MM → present | YYYY-MM}
- Repo(s): {git URL hoặc "n/a"}

## Packs

Liệt kê các pack workspace này opt-in. Mỗi pack thêm constraints, coding rules, validator rules, retrieval map cho stack tương ứng. Xem [`packs/README.md`](../../packs/README.md) cho catalog.

- {vd: pack-event-driven nếu workspace có Kafka/MQTT}

> Để workspace KHÔNG opt-in pack nào, để section trống hoặc xoá hẳn. Engine rules vẫn apply.

## Tech Stack

- Languages: {Java | Kotlin | Swift | Kotlin | TS | Go | Python | ...}
- Messaging: {kafka | mqtt | rabbit | sqs | none}
- Storage: {postgres | mongo | mysql | redis | ...}
- Infra: {k8s | ecs | bare-vm | serverless | ...}

## Entry Points

Đọc theo thứ tự khi bắt đầu task trong workspace này:

- Contracts: [platform/contracts/](platform/contracts/)
- Patterns Index: [patterns-index.md](patterns-index.md)
- Active Projects: [projects/](projects/)
- Domains: [domains/](domains/)
- Runbooks (incident): [runbooks/](runbooks/)
- Workspace ADRs: [decisions/](decisions/)

## Override Notes

Liệt kê file override engine defaults nếu có:

- `agents/constraints.md` — {mô tả} | hoặc "không có"
- `agents/pipeline/validator-rules.md` — {mô tả} | hoặc "không có"

## Glossary (optional)

| Term | Meaning |
|------|---------|
| {từ chuyên ngành} | {định nghĩa trong context của workspace này} |
