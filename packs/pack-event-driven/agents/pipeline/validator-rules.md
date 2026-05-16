# pack-event-driven — Validator Rules

Layer-1 rule (regex-based) đặc thù Kafka/MQTT. Implement: [`scripts/rules.py`](../../scripts/rules.py).

Tất cả rule prefix `pack-event-driven-`.

## Rule list

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-event-driven-kafka-no-hardcoded-topic`     | error | Quoted lowercase dotted literal near a Kafka API verb (`@KafkaListener`, `KafkaTemplate`, `send(`, `subscribe(`…) and not on a config-read line (`@Value`, `getProperty`, `System.getenv`…). |
| `pack-event-driven-kafka-commit-before-process`  | error | `commitSync(` / `commitAsync(` appears BEFORE the first processing call (`process`, `for (`, `forEach`, `onMessage`, `publish(`…) in the same enclosing brace block. |
| `pack-event-driven-kafka-dlq-required`           | error | File looks like a Kafka consumer (has `@KafkaListener`, `KafkaConsumer`, `ConsumerRecord`, `@StreamListener`, or `poll(`) but contains no reference to `dlq` / `deadLetter` / `.dlq.`. |
| `pack-event-driven-kafka-batch-processing`       | warn  | Per-message loop `for (X x : messages)` while a batch hint is present in the file (`max.poll.records`, `setBatchListener`, `containerFactory=`…). |
| `pack-event-driven-mqtt-no-inline-topic`         | error | String concat / `String.format` / template-literal building of a topic literal that begins with `topic/`, when no helper (`buildTopic`, `topicFor`, `MqttTopic.`, `TopicFormatter`…) is referenced on the same line. |
| `pack-event-driven-mqtt-unregistered-type`       | error | Literal `topic/.../up/<type>` whose `<type>` is not in the `Registered Types` table of `{ws}/platform/contracts/mqtt-topic-contract.md`. |

## Layer 2 self-check additions

Khi pack được active, prompt-template self-check section sẽ append:

```md
### Kafka
- Offset committed only after processing completes
- DLQ path implemented for all failure scenarios
- Batch processing used when batch mode configured (not per-message loop)
- No hardcoded topic names — read from config

### MQTT
- Topic format matches contract: topic/{region}/{gatewayId}/up/{type}
- Only registered types used (per {ws}/platform/contracts/mqtt-topic-contract.md)
- No inline topic string construction — use helper
```

Xem [`prompt-overrides.md`](prompt-overrides.md).

## Heuristic limitations

- `kafka-no-hardcoded-topic`: requires Kafka API verb on same line; topic via static-final constant missed.
- `kafka-commit-before-process`: block-local; cross-method commit ordering invisible.
- `mqtt-no-inline-topic`: regex-based; complex builder patterns may bypass.

Layer 2 self-check + integration test bù vào.
