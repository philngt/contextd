# pack-product — Constraints

Hard rules cho product/business documentation. Additive trên engine constraints. Áp dụng cho mọi file trong `{ws}/product/` và mọi output của `/product-brief`, `/business-view`, `/contextd-explain`.

## Brief Completeness (`pack-product-brief-completeness`)

- **Mỗi product brief PHẢI có 4 section bắt buộc**: `Problem`, `Target User`, `Success Metric`, `Acceptance Criteria`. Thiếu bất kỳ section nào → không phải brief, là idea note.
- **Brief PHẢI link tới persona** (file trong `{ws}/product/personas/`) hoặc khai báo "no specific persona — broad audience" với lý do.
- **Acceptance criteria PHẢI testable** — diễn đạt dạng "User can X" / "When Y, then Z", không phải "Improve UX" / "Make it better".

## Measurability (`pack-product-measurability`)

- **OKR Key Result PHẢI measurable** — chứa số (`%`, count, currency) + deadline. "Increase signups" không phải KR; "Increase weekly signups by 30% by `<target-date>`" là KR.
- **Success metric PHẢI có baseline + target + measurement window**. "Conversion rate" không đủ; "Conversion rate from landing → signup, baseline 2.1%, target 4%, measured weekly" là đủ.
- **Không dùng vanity metrics standalone** (page views, total users, ...) — phải pair với engagement/retention.

## Plain Language (`pack-product-plain-language`)

- **KHÔNG dùng jargon kỹ thuật trong product docs**: controller, schema, deployment, container, microservice, refactor, migration, endpoint, payload, ...
- Nếu cần reference component kỹ thuật → dùng business term + link tới technical doc. Vd: thay vì "auth-service refactor", viết "login experience improvement (technical: auth-service refactor — see [link])".
- **KHÔNG dùng "AI"/"machine learning" như buzzword** — phải nói rõ ai dùng cái gì để làm gì.

## Persona & Journey Integrity (`pack-product-persona-journey`)

- **Persona PHẢI có evidence base** — source IDs, method, sample/context và collection date. Persona không có evidence → `status: hypothesis`; không invent demographic detail để làm persona có vẻ thật.
- **Customer journey PHẢI có touchpoints + observed/inferred friction rõ ràng**; label evidence vs hypothesis và include drop-off/qualitative signal khi có. Emotion chỉ ghi khi research hỗ trợ.

## Roadmap Discipline (`pack-product-roadmap`)

- **Mỗi roadmap commitment PHẢI link tới brief** trong `{ws}/product/briefs/`. "Q2: improve onboarding" không link brief = wishlist, không phải commitment.
- **KHÔNG promise dates công khai trước khi engineering estimate**. Roadmap có 2 trạng thái: `committed` (engineering đã estimate + capacity) hoặc `exploring` (chưa).

## Cross-Reference với Engineering (`pack-product-engineering-links`)

- **Brief KHÔNG được dictate implementation** — không viết "use Postgres", "build REST API", "deploy on AWS". Implementation là quyết định của engineering dựa trên contracts/patterns.
- **Brief CÓ THỂ ràng buộc constraint**: response time, data residency, compliance, cost ceiling — đó là requirement, không phải implementation.

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
