# pack-ba — Prompt Overrides

Section bổ sung vào `agents/pipeline/prompt-template.md` self-check khi pack active.

## System prompt addition

Nếu task thuộc BA, ưu tiên clarity của requirement, traceability của assumption, và tính testable của acceptance criteria. Mọi statement non-trivial cần source attribution (interview/ticket/regulation). Tránh dùng jargon kỹ thuật trong artifact dành cho stakeholder business.

## Self-Check Constraints (append vào `Constraints to check` của prompt-template)

```
### Requirement (pack-ba)
- Requirement nêu actor + trigger + action + business outcome
- ID stable (R-{epic}-{nn}) + source link (interview/ticket/regulation)
- 1 requirement = 1 testable outcome (no composite and/or)
- Cross-team dependency có DRI per side

### Acceptance (pack-ba)
- AC measurable/testable, Gherkin hoặc rule-based
- ≥ 3 AC per story (happy + edge + error)
- Assumption tách section riêng, KHÔNG trộn vào AC
- NFR section: perf + security + a11y + i18n + compliance

### Process & Terminology (pack-ba)
- Process map As-Is + To-Be cùng template + gap analysis
- BPMN swimlane chuẩn (mỗi lane = role)
- Business term nhất quán trong cùng doc; Glossary section per epic
- Acronym expand ở first use

### Scope & Stakeholder (pack-ba)
- Non-goals section liệt kê 3-5 điều out-of-scope
- RACI/DRI cho major decision
- Sign-off log với version + date + approver
- Change log nếu scope thay đổi
```

## Layer-2 LLM self-check (append vào validator-rules Layer 2)

```md
### Business Analysis
- Mỗi requirement có Actor/Trigger/Outcome rõ
- AC không chứa "fast/easy/friendly" thiếu số
- Process map As-Is ≠ To-Be và có gap analysis
- Glossary có entry cho mọi business term
- RACI present cho major decision
- Non-goals enumerated
```

## Inclusion logic

Pack loader (`scripts/pack_loader.py`) merge nội dung file này vào prompt context khi build `current-task.md` cho `/use-contextd`.

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS (pack-ba-*)
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
