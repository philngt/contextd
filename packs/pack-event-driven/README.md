# pack-event-driven

Kafka/MQTT và event-driven backend patterns. Đây là pack đầu tiên của wiki-template — tách ra từ engine core (Phase 1 refactor).

## Khi nào bật pack này

Workspace có service:
- Tiêu thụ/sản xuất Kafka, RabbitMQ, NATS, SQS (event broker)
- Publish/subscribe MQTT
- Batch processing message stream
- Cần DLQ, offset commit, idempotency, retry với exponential backoff

## Components do pack này phục vụ

- `kafka`: consumer/producer patterns, offset commit, DLQ, batch
- `mqtt`: topic format contract, publish/subscribe, gateway routing
- `batch`: batched message processing trên event broker

## Constraints pack thêm

Xem [agents/constraints.md](agents/constraints.md). Tóm tắt:

- Không tạo Kafka topic / MQTT type mới ngoài contract
- Không hardcode topic name, connection string, gateway ID
- Không inline MQTT topic construction — dùng helper từ contract
- Không commit offset trước khi processing xong
- Mọi Kafka consumer phải có DLQ branch

## Validator rules pack thêm

Xem [agents/pipeline/validator-rules.md](agents/pipeline/validator-rules.md). Tất cả rule có prefix `pack-event-driven-`:

| Rule | Severity |
|------|----------|
| `pack-event-driven-kafka-no-hardcoded-topic` | error |
| `pack-event-driven-kafka-commit-before-process` | error |
| `pack-event-driven-kafka-dlq-required` | error |
| `pack-event-driven-kafka-batch-processing` | warn |
| `pack-event-driven-mqtt-no-inline-topic` | error |
| `pack-event-driven-mqtt-unregistered-type` | error |

## Bật pack

Trong `workspaces/{your-ws}/workspace.md`:

```md
## Packs

- pack-event-driven
```

## Customize per-workspace

Thêm rule chặt hơn tại `workspaces/{ws}/agents/pipeline/validator-rules.md` với prefix `ws-`. Pack rule luôn chạy trước, workspace rule chạy thêm — không thể tắt pack rule (strict-only direction).
