# Context Audit Report

## Audit Target

- Task/frame:
- Operator question:
- Status: `ready|needs-evidence|needs-decision|needs-research|blocked`

## Evidence

- Inspected:
- Missing:
- Stale or contradictory:

## Context Map

- Task frame:
- Project memory:
- Repo evidence:
- Domain context:
- Decision context:
- Quality context:
- Handoff context:

## Findings

| Severity | Gap type | Evidence | Missing evidence | Root cause | Risk | Patch | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## Remediation

- Quick context patch:
- Durable context update:
- Skill/playbook remediation:
- Process guardrail:

## Acceptance Criteria

- Operator can name the authoritative context source.
- Missing evidence is explicit, not hidden in assumptions.
- The next action is safe to continue or clearly stopped.

## Verification Method

- Re-run `contextd explain "<task>" --format text`.
- Confirm selected docs, gaps, and warnings match the audit conclusion.
