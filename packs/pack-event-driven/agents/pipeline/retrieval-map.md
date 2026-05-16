# pack-event-driven — Retrieval Map

Component → file path mapping. Khi task-to-docs-map detect component thuộc pack này, retrieval pipeline load thêm các file dưới đây từ workspace active.

## By Component

| Component | Docs to Retrieve (relative to `{ws}/`) |
|-----------|----------------------------------------|
| `kafka` | `platform/patterns/kafka-event-processing.md` |
| `mqtt`  | `platform/patterns/mqtt-routing.md`, `platform/contracts/mqtt-topic-contract.md` |
| `batch` | `platform/patterns/kafka-event-processing.md` (batch section) |

> Nếu file không tồn tại trong `{ws}/` → ghi vào Knowledge Gaps. KHÔNG fallback sang workspace khác hoặc pack docs.

## Component Keywords (cho task-to-docs-map)

Pack manifest (`pack.yaml#keywords`) định nghĩa keyword → component mapping:

```yaml
kafka: [kafka, consumer, producer, topic, offset, dlq, partition, "@KafkaListener", broker]
mqtt: [mqtt, publish, subscribe, gateway, "topic format"]
batch: [batch, chunk, bulk, poll, "max.poll.records"]
```

Intent-parser merge keyword set của tất cả pack đang active để detect components trong task.
