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

## When not to enable

- Security testing/pentest; dùng `pack-security` với authorization boundary riêng.
- “Optimization” chưa có baseline, target, profiler evidence hoặc regression guard.

## Retrieval behavior

Quality workflow và performance workflow có component riêng để task test-case không tự nạp toàn bộ profiling context. Retrieval ưu tiên evidence hiện tại: test result, defect trace, baseline và comparison artifact.

## Verification

```bash
contextd pack-validate --pack pack-qc --format text
contextd context "Review regression gate with latency baseline" --preview --format json
python scripts/validate.py --file <quality-fixture> --workspace <workspace-with-pack>
```
