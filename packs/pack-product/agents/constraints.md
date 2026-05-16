# pack-product — Constraints

Hard rules cho product/business documentation. Additive trên engine constraints. Áp dụng cho mọi file trong `{ws}/product/` và mọi output của `/product-brief`, `/business-view`, `/wiki-explain`.

## Brief Completeness

- **Mỗi product brief PHẢI có 4 section bắt buộc**: `Problem`, `Target User`, `Success Metric`, `Acceptance Criteria`. Thiếu bất kỳ section nào → không phải brief, là idea note.
- **Brief PHẢI link tới persona** (file trong `{ws}/product/personas/`) hoặc khai báo "no specific persona — broad audience" với lý do.
- **Acceptance criteria PHẢI testable** — diễn đạt dạng "User can X" / "When Y, then Z", không phải "Improve UX" / "Make it better".

## Measurability

- **OKR Key Result PHẢI measurable** — chứa số (`%`, count, currency) + deadline. "Increase signups" không phải KR; "Increase weekly signups by 30% by 2026-06-30" là KR.
- **Success metric PHẢI có baseline + target + measurement window**. "Conversion rate" không đủ; "Conversion rate from landing → signup, baseline 2.1%, target 4%, measured weekly" là đủ.
- **Không dùng vanity metrics standalone** (page views, total users, ...) — phải pair với engagement/retention.

## Plain Language

- **KHÔNG dùng jargon kỹ thuật trong product docs**: controller, schema, deployment, container, microservice, refactor, migration, endpoint, payload, ...
- Nếu cần reference component kỹ thuật → dùng business term + link tới technical doc. Vd: thay vì "auth-service refactor", viết "login experience improvement (technical: auth-service refactor — see [link])".
- **KHÔNG dùng "AI"/"machine learning" như buzzword** — phải nói rõ ai dùng cái gì để làm gì.

## Persona & Journey Integrity

- **Persona PHẢI có evidence base** — ghi nguồn (user interviews, survey, analytics), số mẫu (n=...), ngày thu thập. Persona không có evidence → đánh dấu `status: hypothesis`, không phải validated persona.
- **Customer journey PHẢI có touchpoints rõ ràng** + emotional state per touchpoint + drop-off data nếu có. Journey thiếu drop-off/friction = chỉ là happy path map, không phải journey thực.

## Roadmap Discipline

- **Mỗi roadmap commitment PHẢI link tới brief** trong `{ws}/product/briefs/`. "Q2: improve onboarding" không link brief = wishlist, không phải commitment.
- **KHÔNG promise dates công khai trước khi engineering estimate**. Roadmap có 2 trạng thái: `committed` (engineering đã estimate + capacity) hoặc `exploring` (chưa).

## Cross-Reference với Engineering

- **Brief KHÔNG được dictate implementation** — không viết "use Postgres", "build REST API", "deploy on AWS". Implementation là quyết định của engineering dựa trên contracts/patterns.
- **Brief CÓ THỂ ràng buộc constraint**: response time, data residency, compliance, cost ceiling — đó là requirement, không phải implementation.
