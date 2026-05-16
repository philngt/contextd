# pack-event-driven — Coding Rules

Additive rules trên engine coding-rules. Áp dụng khi workspace bật pack này.

## Error Handling at Message-Consumer Boundary

- Classify errors: **transient** (network blip, deadlock) → retry với exponential backoff; **permanent** (schema invalid, business rule violation) → dead-letter + log + alert.
- Never let an unhandled exception cross a message-consumer boundary without first updating the consumer's progress marker (offset / ack / cursor) correctly. Order: process → side-effect committed → ack/offset commit. Never commit before processing.

## Idempotency for Re-deliverable Handlers

- Kafka/MQTT/SQS consumers MUST be idempotent (de-dup key on message ID/event ID, or upsert semantics on downstream store).
- Outbox pattern khi cần atomic commit DB + publish.

## Batch vs Per-Message

- Khi consumer chạy batch mode (`max.poll.records`, `setBatchListener`), không loop từng message với commit riêng — commit cả batch sau khi batch processed.
- Failure handling: batch fail → option (a) reprocess cả batch (yêu cầu idempotent), option (b) split batch và retry per-message + DLQ. Document choice trong service doc.

## Topic Naming & Format

- Topic name từ contract config / generated constant — không string-concat inline.
- MQTT topic: dùng helper formatter từ contract (vd `MqttTopic.format(region, gatewayId, "up", type)`).

## Observability cho Event Flow

- Emit metric: `consumer.lag`, `consumer.processed`, `consumer.dlq`, `consumer.retry` per topic + consumer-group.
- Log mỗi DLQ event với: messageId, error type, retry count, original timestamp.
