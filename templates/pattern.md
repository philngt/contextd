# {Pattern Name}

## Context

{When does this pattern apply? What problem does it solve? What is the trigger or precondition?}

## Flow

```
Step 1 → Step 2 → Step 3 → Output
                      ↓ (on failure)
                 Retry → DLQ / Error path
```

1. {Step 1 description}
2. {Step 2 description}
3. {Step 3 description}
4. On failure: {behavior}

## Default Config

```yaml
# Sensible defaults. Projects override per service.
key_1: value
key_2: value
```

## Failure Strategy

| Scenario | Action |
|----------|--------|
| {transient error} | {retry behavior} |
| {poison input} | {DLQ / reject behavior} |
| {downstream unavailable} | {retry + alert} |

## Implementation Rules

- {Hard rule 1 — must / must not}
- {Hard rule 2}
- {Hard rule 3}

## Override Points

{Which config keys are projects allowed to override? Which are fixed?}

## Anti-patterns

- {What this pattern is NOT — common mistakes}

## Used By

> Link tới services trong cùng workspace dùng pattern này. Khi `/evidence-apply` tạo service mới dựa trên pattern này, dòng link tương ứng được auto-append vào bảng dưới.

- [{project} / {service}](../../projects/{project}/services/{service}.md)

## Related

- {Link to contract — `../contracts/...`}
- {Link to architecture — `../architecture/...`}
- {Link to ADR — `../../decisions/...`}
