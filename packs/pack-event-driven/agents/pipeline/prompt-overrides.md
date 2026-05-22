# pack-event-driven — Prompt Overrides

Section bổ sung vào `agents/pipeline/prompt-template.md` self-check khi pack active.

## Self-Check Constraints (append vào `Constraints to check` của prompt-template)

```
### Kafka (pack-event-driven)
- Offset committed only after processing completes
- DLQ path implemented for all failure scenarios
- Batch processing used when batch mode configured (not per-message loop)
- No hardcoded topic names — read from config

### MQTT (pack-event-driven)
- Topic format matches contract: topic/{region}/{gatewayId}/up/{type}
- Only registered types used (per {ws}/platform/contracts/mqtt-topic-contract.md)
- No inline topic string construction — use helper
```

## Layer-2 LLM self-check (append vào validator-rules Layer 2)

```md
### Kafka
- Offset committed only after processing completes
- DLQ path implemented for all failure scenarios
- Batch processing used (not per-message loop)
- No hardcoded topic names

### MQTT
- Topic format matches: topic/{region}/{gatewayId}/up/{type}
- Only registered types used: {list from contract}
- No inline topic string construction
```

## Inclusion logic

Pack loader (`scripts/pack_loader.py`) merge nội dung file này vào prompt context khi build `current-task.md` cho `/use-contextd`.

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
