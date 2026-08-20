# pack-ba — Constraints

Hard rules cho business analysis (requirement, acceptance, process, stakeholder). Additive trên engine constraints. Strict-only direction.

## Requirement Clarity (`pack-ba-requirement-clarity`)

- **Requirement PHẢI mô tả outcome business, actor, và trigger** — không chấp nhận requirement chỉ mô tả solution kỹ thuật.
- **Requirement PHẢI independently traceable/testable** — split only when outcomes can change or be accepted independently; conjunction text alone không phải bằng chứng phải tách.
- **Requirement có impact cross-team PHẢI nêu dependency/handoff** rõ ràng + DRI per side.
- **Source attribution bắt buộc** — evidence/decision ID, owner và date; redact/restrict private conversation links theo workspace policy. KHÔNG "user wants" mơ hồ.

## Acceptance Discipline (`pack-ba-acceptance-discipline`)

- **Acceptance criteria PHẢI measurable + testable** — tránh từ mơ hồ ("nhanh", "tốt hơn", "thân thiện") khi không có metric.
- **KHÔNG trộn assumption ngầm vào acceptance criteria** — assumption ghi rõ và reviewable trong section riêng.
- **Acceptance coverage follows state/risk** — include relevant success, boundary, failure and recovery rules; Gherkin là optional representation, không phải quota.
- **NFR/risk review bắt buộc** cho epic — performance, security, accessibility, localization, compliance hoặc `N/A` + rationale theo domain.

## Terminology Consistency (`pack-ba-terminology-consistency`)

- **Business term chính (entity/process/status) PHẢI nhất quán** trong cùng tài liệu — tránh dùng nhiều tên cho cùng khái niệm.
- **Khi thay đổi nghĩa của term đã có** — phải nêu migration note cho stakeholder liên quan + version bump.
- **Acronym PHẢI expand ở first use** trong mọi document; có Glossary section per epic.

## Scope Discipline (`pack-ba-scope-discipline`)

- **Non-goals/out-of-scope section bắt buộc** — nêu các boundary dễ bị hiểu nhầm hoặc gây scope creep; không quota số dòng.
- **Scope change PHẢI có change log** — ngày, người, lý do, impact metric/timeline.
- **KHÔNG silently expand scope** giữa epic — revisit AC + estimate.

## Stakeholder & Sign-off (`pack-ba-stakeholder-signoff`)

- **Decision ownership PHẢI documented** cho decision cần approval/handoff; dùng DRI/RACI theo governance của workspace.
- **Sign-off evidence bắt buộc khi policy yêu cầu approval** — actor, artifact version, date và accepted residual risk.

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
