# {Service Name}

## Purpose

{One sentence: what this service does and why it exists.}

## Input

{What triggers this service — Kafka topic, HTTP request, MQTT message, scheduled job, etc.}

Message/request schema:
```json
{
  // schema here
}
```

## Output

{What this service produces — Kafka event, HTTP response, MQTT publish, DB write, etc.}

## Flow

Applies platform pattern:
→ {link to `{ws}/platform/patterns/...` — relative path từ file service này, vd `../../platform/patterns/kafka-event-processing.md`}

```
Step 1 → Step 2 → Step 3 → Output
                      ↓ (on failure)
                 Retry → DLQ / Error response
```

## Config

```yaml
# list config keys and defaults
# note which are overrides from platform defaults
```

## Config Overrides

| Parameter | Platform Default | This Service | Reason |
|-----------|-----------------|--------------|--------|
| {param} | {default} | {value} | {why} |

## Failure Handling

| Scenario | Action |
|----------|--------|
| {error type} | {what happens} |

## Notes

{Anything that would surprise a reader — hidden invariants, non-obvious dependencies, known quirks.}

## Related

> Mọi link phải nằm trong cùng workspace (`{ws}/...`). KHÔNG link sang workspace khác.

- {Link to pattern used — `../../platform/patterns/...`}
- {Link to domain workflow if applicable — `../../domains/{domain}/workflow.md`}
- {Link to contract if applicable — `../../platform/contracts/...`}
- {Link to relevant ADRs — `../../decisions/...` hoặc `decisions/...` (project-level)}
