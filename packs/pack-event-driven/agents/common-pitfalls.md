# pack-event-driven — Top 10 Common Pitfalls

Anti-pattern lặp lại với Kafka/MQTT/broker. Additive trên [constraints.md](constraints.md).

## P01 — Commit offset trước khi process
- **NG**: `consumer.commitSync()` rồi mới gọi `process(msg)`.
- **OK**: process xong (idempotent) → commit. Crash giữa chừng → reprocess.
- **Why**: data loss khi worker crash sau commit.
- **Detect**: Layer-1 `pack-event-driven-kafka-commit-before-process`.
- **Severity**: error

## P02 — Thiếu DLQ / retry strategy
- **NG**: lỗi parse → log + skip, hoặc retry vô hạn block partition.
- **OK**: bounded retry (exponential) → DLQ topic; alert khi DLQ tăng.
- **Why**: 1 poison message dừng cả partition; mất visibility.
- **Detect**: Layer-1 `pack-event-driven-kafka-dlq-required` + Layer-2 delivery-policy review.
- **Severity**: error

## P03 — Hardcoded topic name
- **NG**: `consume("orders.created.v1")`.
- **OK**: topic name từ config; helper `topicFor(domain, event, version)`.
- **Why**: rename topic = redeploy toàn cluster; lỗi typo silent.
- **Detect**: Layer-1 `pack-event-driven-kafka-no-hardcoded-topic`.
- **Severity**: warn

## P04 — Inline MQTT topic string
- **NG**: `client.publish("topic/" + region + "/" + gw + "/up/temp", ...)`.
- **OK**: `buildTopic({region, gatewayId, direction: 'up', type})` per contract.
- **Why**: drift khỏi contract; refactor format = grep toàn repo.
- **Detect**: Layer-1 `pack-event-driven-mqtt-no-inline-topic`.
- **Severity**: warn

## P05 — Per-message loop khi batch mode
- **NG**: batch listener nhưng synchronous commit từng record mà không có correctness/latency rationale.
- **OK**: choose batch, per-record retry, partial ack, or split strategy from delivery contract; measure throughput and failure isolation.
- **Why**: commit frequency và failure granularity trade off throughput, duplicates và replay scope.
- **Detect**: Layer-1 `pack-event-driven-kafka-batch-processing` (heuristic) + Layer-2 policy review.
- **Severity**: warn

## P06 — Thiếu dedup khi at-least-once
- **NG**: producer retry → consumer xử lý 2 lần → duplicate order.
- **OK**: idempotency key (eventId) + dedup store / upsert.
- **Why**: re-delivery is common under retry/rebalance/failure unless an end-to-end exactly-once contract is proven.
- **Detect**: Layer-2 — handler có check `seenEventIds`.
- **Severity**: error

## P07 — Ordering assumption khi partition > 1
- **NG**: code giả định msg đến đúng thứ tự global.
- **OK**: partition key = entity ID; ordering chỉ trong cùng partition.
- **Why**: out-of-order race condition.
- **Detect**: Layer-2 — review partition key strategy doc.
- **Severity**: error

## P08 — Thiếu schema versioning
- **NG**: payload đổi field, không version → consumer cũ crash.
- **OK**: schema registry / version trong payload (`schemaVersion: 2`); backward compat.
- **Why**: rolling deploy break; consumer lag spike.
- **Detect**: Layer-2 — contract doc có schema version field.
- **Severity**: error

## P09 — Swallow deserialize error
- **NG**: `try { parse(msg) } catch { return }` — message biến mất.
- **OK**: parse fail → DLQ với raw bytes + error.
- **Why**: poison message disappears, không debug được.
- **Detect**: Layer-2 — deser error path đến DLQ.
- **Severity**: error

## P10 — Không propagate correlationId
- **NG**: log `"processed msg"` không kèm event ID, trace ID.
- **OK**: trace context (W3C) trong header; log `correlationId`.
- **Why**: không trace được flow xuyên service.
- **Detect**: Layer-2 — handler log có trace ID.
- **Severity**: warn

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 commit-before | `pack-event-driven-kafka-commit-before-process` | ✓ |
| P02 DLQ | `pack-event-driven-kafka-dlq-required` | ✓ |
| P03 hardcoded-topic | `pack-event-driven-kafka-no-hardcoded-topic` | ✓ |
| P04 inline-topic | `pack-event-driven-mqtt-no-inline-topic` | ✓ |
| P05 batch policy | `pack-event-driven-kafka-batch-processing` | ✓ |
| P06 dedup | — | ✓ |
| P07 ordering | — | ✓ |
| P08 schema-ver | — | ✓ |
| P09 swallow-deser | — | ✓ |
| P10 correlation | — | ✓ |
