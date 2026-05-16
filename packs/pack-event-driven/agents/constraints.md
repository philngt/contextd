# pack-event-driven — Constraints

Hard rules đặc thù event-driven (Kafka/MQTT/broker). Pack này được load **additive** sau engine constraints. Strict-only direction.

## Architecture

- **Do not bypass retry logic** — every Kafka consumer must implement retry + DLQ per the platform pattern
- **Do not add new Kafka topics** without updating the topic contract trong `{ws}/platform/contracts/`
- **Do not add new MQTT types** without registering them trong `{ws}/platform/contracts/mqtt-topic-contract.md`

## Code

- **Do not hardcode** topic names, broker connection strings, region codes, or gateway IDs — read from config
- **Do not inline** MQTT topic construction — use the contract format helper (`buildTopic`, `topicFor`, ...)
- **Do not commit offset before processing** — this is a data-loss risk; commit only after successful processing of the batch/message

## Knowledge

- **Do not assume** topic formats, partition keys, or consumer group naming — read the contract
- **Do not duplicate** broker setup code — apply existing `{ws}/platform/patterns/kafka-event-processing.md` (or equivalent)

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)
