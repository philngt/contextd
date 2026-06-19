# pack-qc

Quality control **+ performance optimization** pack. Test design/execution, defect triage, regression coverage, release quality gates **and** baseline metrics, bottleneck-first tuning, safe optimization, regression guarding.

> **v0.2.0 absorbs `pack-optimize`** — workspaces that previously listed `- pack-optimize` should switch to `- pack-qc`.

## When to enable

Workspace opts in by adding `- pack-qc` under `## Packs` in `workspaces/{ws}/workspace.md`.

Enable when workspace needs:
- Quality gate standardization for release
- Defect lifecycle + regression planning with evidence
- Performance work with baseline/target metrics + profiling discipline
- Optimization rollout with feature flag + regression guards

## What it adds

- **Constraints** (`agents/constraints.md`) — hard rules for QC + perf workflow (two sections)
- **Working rules** (`agents/coding-rules.md`, compatibility filename) — conventions for test cases, bug reports, perf reports
- **Validator rules** (`agents/pipeline/validator-rules.md` + `scripts/rules.py`) — automated gates
- **Retrieval map** (`agents/pipeline/retrieval-map.md`) — component → knowledge docs mapping
- **Prompt overrides** (`agents/pipeline/prompt-overrides.md`) — QC + perf self-check
- **Common pitfalls** (`agents/common-pitfalls.md`) — Top 10 QC + Top 10 perf

## Components declared

Quality control: `test-case-design`, `test-execution`, `defect-triage`, `regression-plan`

Performance optimization: `performance-profiling`, `bottleneck-analysis`, `optimization-safety`, `regression-guard`

## Conflicts with

(none)

## Related

- Pack mechanism: [packs/README.md](../README.md)
- Cross-cutting principles: [agents/cross-cutting-principles.md](../../agents/cross-cutting-principles.md)
