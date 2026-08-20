# pack-ba — Prompt Overrides

Section bổ sung vào `agents/pipeline/prompt-template.md` self-check khi pack active.

## System prompt addition

Nếu task thuộc BA, ưu tiên clarity của requirement, traceability của assumption, và tính testable của acceptance criteria. Mọi statement non-trivial cần source attribution (interview/ticket/regulation). Tránh dùng jargon kỹ thuật trong artifact dành cho stakeholder business.

## Self-Check Constraints (append vào `Constraints to check` của prompt-template)

```
### Requirement (pack-ba)
- Requirement nêu actor + trigger + action + business outcome
- ID stable theo workspace convention + source/evidence ID
- Requirement independently traceable/testable; split khi outcome có lifecycle độc lập, không chỉ vì câu có and/or
- Cross-team dependency có DRI per side

### Acceptance (pack-ba)
- AC measurable/testable, Gherkin hoặc rule-based
- Coverage theo state/risk: success, boundary, failure và recovery nào relevant
- Assumption tách section riêng, KHÔNG trộn vào AC
- NFR/risk review theo domain; item không áp dụng ghi N/A + rationale

### Process & Terminology (pack-ba)
- As-Is/To-Be + gap analysis khi task thực sự thay đổi process; không tạo To-Be giả cho documentation-only work
- Chọn BPMN/swimlane/step table theo audience/tooling; actor ownership và branch phải rõ
- Business term nhất quán; glossary chỉ chứa term material/ambiguous của scope
- Acronym expand ở first use

### Scope & Stakeholder (pack-ba)
- Non-goals section nêu các boundary dễ gây scope creep, không quota số dòng
- Decision ownership theo governance workspace (DRI/RACI khi phù hợp)
- Sign-off evidence khi policy yêu cầu approval
- Change log nếu scope thay đổi
```

## Layer-2 LLM self-check (append vào validator-rules Layer 2)

```md
### Business Analysis
- Mỗi requirement có Actor/Trigger/Outcome rõ
- AC không chứa "fast/easy/friendly" thiếu số
- Process change có As-Is/To-Be/gap evidence khi relevant
- Material/ambiguous terms được define hoặc link canonical glossary
- Decision ownership đáp ứng workspace governance; RACI không bắt buộc khi DRI đủ
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
