# Service: reporting

## Purpose

Sinh 1 file HTML self-contained tổng hợp toàn workspace (Overview / Architecture / Contracts / Patterns / Domains / ADRs / Runbooks) cho stakeholder/onboarding/audit.

## Input

`/contextd-report` slash command với optional filters (date range, scope subset).

## Output

HTML file self-contained (open browser xem ngay, no server/dependency).

## Flow

Applies platform pattern:
→ [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md)

```
0. Workspace check
  ↓
1. Scan {ws}/{platform, projects, domains, decisions, runbooks}/
  ↓
2. Fill templates/report-html-skeleton.html + report-fragments.html
  ↓ per section
3. Detect gaps (sections empty) → render với "nodata" markers
  ↓
4. Emit HTML output file
```

## Config

```yaml
template_skeleton: "templates/report-html-skeleton.html"
template_fragments: "templates/report-fragments.html"
gap_marker: "nodata"
self_contained: true                  # NO external deps (CSS inline, no remote fetch)
```

## Config Overrides

| Parameter | Platform Default | This Service | Reason |
|-----------|-----------------|--------------|--------|
| _(none — engine-level)_ | | | |

## Failure Handling

| Scenario | Action |
|----------|--------|
| Workspace mostly empty | Render với nhiều `nodata` markers, KHÔNG block |
| Template missing | STOP với hint locate template |
| HTML emit fail (disk full) | STOP, surface error |

## Notes

- Output là **presentation document** — KHÔNG phải input cho code generation (đó là `/contextd-use`).
- Self-contained design: mở browser xem ngay, không cần dev server.
- Gap markers (`nodata`) hữu dụng để audit content coverage qua quarterly snapshots.

## Related

- Pattern: [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md)
- Engine source: `.claude/commands/contextd-report.md`
- Templates: `templates/report-html-skeleton.html`, `templates/report-fragments.html`
- Source: F-017d, evidence `2026-05-08-engine-bootstrap-wiki-template`
