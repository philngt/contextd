---
title: "{Brief title — 1 line, action-oriented}"
status: draft  # draft | review | approved | shipped | cut
owner: "{PM/owner name}"
created: YYYY-MM-DD
target_release: YYYY-Qx  # or YYYY-MM
personas: ["{persona-slug-1}", "{persona-slug-2}"]
---

# {Brief title}

## Problem

{Quantify the problem. "30% of new users abandon onboarding at step 3" beats "users find onboarding hard".
What user pain are we solving? Why now? What evidence?}

## Target User

{Which persona(s)? Link to {ws}/product/personas/{slug}.md.
Estimated reach: how many users affected?}

## Success Metric

| Metric | Baseline | Target | Measurement window |
|--------|----------|--------|-------------------|
| {primary metric} | {current value} | {target value} | {weekly/monthly/...} |
| {secondary metric (optional)} | | | |

> Pair vanity metrics (counts, views) with engagement/retention metrics.

## Acceptance Criteria

- [ ] {User can X when Y}
- [ ] {When Z happens, system shows W}
- [ ] {Edge case: ...}

> Each criterion testable. "Improve UX" is NOT acceptance criteria.

## Out of Scope

- {What we explicitly are NOT doing in this brief}
- {Future iteration ideas}

## Constraints (non-negotiable, not implementation)

- {Latency / cost / compliance / data residency / accessibility — things engineering MUST respect}
- {KHÔNG viết "use Postgres" — đó là implementation. Viết "data must persist across sessions" — đó là constraint.}

## Open Questions

- {Question 1 — owner: {who decides}}
- {Question 2}

---

## Technical reference (for engineering)

> Section này engineering fill. PM viết brief KHÔNG cần đụng tới.

- Related contracts: {link `{ws}/platform/contracts/...`}
- Related patterns: {link `{ws}/platform/patterns/...`}
- Related services: {link `{ws}/projects/{p}/services/...`}
- ADR (nếu có): {link `{ws}/decisions/...`}
