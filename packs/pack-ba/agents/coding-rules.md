# pack-ba — Coding Rules

Idioms cho BA writing — requirement, acceptance criteria, process map, stakeholder doc. Less strict than constraints — đây là convention.

## Requirement Format

- Cấu trúc ưu tiên: **Actor → Trigger → Action → Business Outcome**; format khác được phép nếu vẫn traceable và testable.
- Viết assumptions, dependencies và out-of-scope đủ ngắn để scan nhưng không cắt mất điều kiện/rationale quan trọng.
- Một requirement nên có một outcome có thể accept/version độc lập; conjunction chỉ là tín hiệu để review, không phải rule split tự động.
- Tag mỗi requirement với ID stable theo workspace convention để trace xuyên acceptance/test.
- Source attribution dùng evidence/ticket/interview ID; private conversation link phải theo access/redaction policy, không chỉ dán URL.

## Acceptance Criteria Format

- Dùng **Given/When/Then** (Gherkin) hoặc **Rule-based** (data table). Chọn 1, dùng nhất quán per epic.
- Mỗi tiêu chí: 1 condition path; happy + edge + error case tách thành scenario riêng.
- Có owner xác nhận / nguồn xác minh (PM, domain expert, regulation doc).
- Testable: dev/QA đọc xong viết được test case mà không cần hỏi lại.

## Non-Functional Requirement (NFR)

- Mỗi epic có **NFR/risk review** theo domain: performance, security, accessibility, localization, compliance hoặc `N/A` + rationale.
- Mỗi NFR có metric đo được + verification method (load test, audit, manual check).
- KHÔNG "fast/easy/user-friendly" không kèm số.

## Persona & User Story

- User-story format là một option; artifact phải nêu role/context, capability và outcome dù dùng format khác.
- Link persona/role evidence khi có; không invent tên hoặc demographic để tránh từ generic "user".
- Permission/role được nêu rõ cho mọi capability (admin / standard / read-only / guest).

## Process Map (As-Is / To-Be)

- Swimlane theo role/actor; mỗi lane chỉ chứa step actor đó thực hiện.
- Decision point đặt tên dạng câu hỏi (`Is invoice approved?`); branch label `Yes/No` rõ.
- As-Is + To-Be cùng template để diff rõ; gap analysis section liệt kê delta + change impact.
- Notation chuẩn: BPMN 2.0 subset (event, task, gateway, sequence flow) — không free-form box.

## Stakeholder Doc

- Chọn DRI/RACI/decision owner theo governance và mức độ handoff; không tạo matrix khi một owner rõ là đủ.
- Owner có thể là role/team theo policy, nhưng escalation/approval boundary phải xác định được.
- Communication cadence và sign-off log chỉ bắt buộc khi risk/dependency/policy cần; ghi actor, artifact version và date.

## Glossary & Term Hygiene

- Mỗi epic có **Glossary** section với business term + 1-line definition + first-use link.
- Acronym expand ở first use trong mọi document.
- Term mơ hồ ("system", "user", "data") PHẢI specify trong context cụ thể.

## Versioning & Change Log

- Doc có version footer + last-modified date + author.
- Change log section: ngày, người, lý do, scope impact.
- Major version bump khi behavior thay đổi; minor cho clarification.
