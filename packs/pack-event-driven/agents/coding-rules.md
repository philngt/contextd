# pack-event-driven — Coding Rules

Additive rules trên engine coding-rules. Áp dụng khi workspace bật pack này.

## Error Handling at Message-Consumer Boundary

- Classify errors by retryability and business meaning. Transient failures use bounded backoff/jitter; permanent/poison events follow the workspace quarantine/DLQ/drop policy with evidence and alerting.
- Progress-marker order follows declared semantics. A common at-least-once path is process → durable side effect → ack/commit; transactional or at-most-once designs must document and test their different failure trade-off.

## Idempotency for Re-deliverable Handlers

- Re-deliverable handlers MUST be idempotent or carry an equivalent dedup/transaction contract; document the identity key and retention window.
- Outbox pattern khi cần atomic commit DB + publish.

## Batch vs Per-Message

- Với batch mode, choose whole-batch, partial-ack, split/retry, or per-record handling from ordering, replay scope and failure-isolation needs; avoid synchronous per-record commits without measured rationale.
- Document batch failure behavior, progress marker, idempotency/dedup and poison-event destination in the service contract.

## Topic Naming & Format

- Topic name từ contract config / generated constant — không string-concat inline.
- MQTT topic: dùng helper formatter từ contract (vd `MqttTopic.format(region, gatewayId, "up", type)`).

## Observability cho Event Flow

- Emit metric: `consumer.lag`, `consumer.processed`, `consumer.dlq`, `consumer.retry` per topic + consumer-group.
- Log mỗi DLQ event với: messageId, error type, retry count, original timestamp.

## Domain Decision Lens

Use within this pack's scope; existing constraints remain authoritative.

- **Observe:** Trace event identity, partition/order key, producer acknowledgement, consumer progress marker, durable side effect, retry destination, and replay window under the declared delivery contract.
- **Mechanism:** A broker acknowledgement and a committed offset describe different boundaries from a database outcome. Lag zero can coexist with missing effects when failures are swallowed or progress advances early.
- **Choose:** For at-least-once work, pair durable processing with idempotency/deduplication and the required commit order. Choose bounded retries, quarantine, or outbox coordination from failure and atomicity requirements.
- **Exception:** At-most-once or transactional contracts have different trade-offs and must be explicit. Producer idempotence does not by itself make an external database effect exactly once.
- **Verify:** Inject failures before/after effects and progress updates; test restart, duplicate delivery, ordering, and poison events. Reconcile identities and expected outcomes, not only aggregate counts or lag.
- **Stop:** Pause replay or retention changes when duplicate effects, ordering requirements, or the lost-event interval are unknown. Do not declare recovery solely because the consumer caught up.
