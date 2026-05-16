# Runbook: {Incident Name}

## Symptom

{What the on-call engineer observes — alerts fired, user reports, metrics that are out of range.}

## Likely Causes

1. {Most common cause}
2. {Second most common cause}
3. {Less common cause}

## Diagnosis Steps

```bash
# Step 1: {what to check}
{command}

# Step 2: {what to check}
{command}
```

Key signals to look for:
- {signal 1 and what it means}
- {signal 2 and what it means}

## Fix

| Cause | Fix |
|-------|-----|
| {cause} | {action} |
| {cause} | {action} |

## Verification

{How to confirm the fix worked — metric returns to normal, alert resolves, smoke test passes.}

```bash
# Verification command
{command}
```

## Escalation

{When to escalate, who to escalate to, and what information to include in the escalation.}

## Related

> Mọi link nằm trong cùng workspace (`{ws}/...`).

- {Link to relevant platform pattern — `../platform/patterns/...`}
- {Link to related runbooks — `./{other-runbook}.md`}
- {Link to affected service docs — `../projects/{project}/services/...`}
