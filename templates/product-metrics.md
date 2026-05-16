---
last_updated: YYYY-MM-DD
nsm_owner: "{role/team}"
---

# Product Metrics

## North Star Metric (NSM)

> One metric. Multiple north stars = no north star.

**{NSM name}**

| Attribute | Value |
|-----------|-------|
| Definition (formula) | {how computed} |
| Current value | {value} as of YYYY-MM-DD |
| Target (12mo) | {value} |
| Owner | {role/team} |
| Cadence | weekly / monthly |
| Dashboard | {link or "not yet"} |

**Why this NSM**: {1-2 paragraphs linking metric to long-term value creation for both user and business}

---

## Input metrics (drive NSM)

| Metric | Definition | Owner | Cadence | Current | Target | Dashboard |
|--------|------------|-------|---------|---------|--------|-----------|
| Activation rate | {formula} | | weekly | | | |
| D7 retention | {formula} | | weekly | | | |
| Conversion (signup → paid) | {formula} | | weekly | | | |

---

## Leading indicators (early signals)

| Metric | Watching for | Owner | Cadence |
|--------|--------------|-------|---------|
| {indicator} | {what change in this means} | | daily / weekly |

---

## Guardrail metrics (don't break these while improving NSM)

| Metric | Floor / Ceiling | Why it matters |
|--------|-----------------|----------------|
| {p99 latency / error rate / cost per user / ...} | {threshold} | {risk if breached} |

---

## Metric review cadence

- **Weekly**: input metrics + leading indicators
- **Monthly**: NSM trend + guardrails
- **Quarterly**: revisit NSM definition itself (drift check)
