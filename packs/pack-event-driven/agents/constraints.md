# pack-event-driven — Constraints

Hard rules đặc thù event-driven (Kafka/MQTT/broker). Pack này được load **additive** sau engine constraints. Strict-only direction.

## Architecture (`pack-event-driven-architecture`)

- **Delivery failure policy is mandatory** — each consumer follows the workspace contract for retry, dead-letter/quarantine, pause/escalation, or intentional drop; no silent skip or unbounded retry.
- **Do not add new Kafka topics** without updating the topic contract trong `{ws}/platform/contracts/`
- **Do not add new MQTT types** without registering them trong `{ws}/platform/contracts/mqtt-topic-contract.md`

## Code (`pack-event-driven-code`)

- **Do not hardcode** topic names, broker connection strings, region codes, or gateway IDs — read from config
- **Do not inline** MQTT topic construction — use the contract format helper (`buildTopic`, `topicFor`, ...)
- **Progress marker follows the delivery contract** — for at-least-once flows, ack/commit only after the required durable outcome; at-most-once/transactional exceptions must be explicit and tested.

## Knowledge (`pack-event-driven-knowledge`)

- **Do not assume** topic formats, partition keys, or consumer group naming — read the contract
- **Do not duplicate** broker setup code — apply existing `{ws}/platform/patterns/kafka-event-processing.md` (or equivalent)

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
