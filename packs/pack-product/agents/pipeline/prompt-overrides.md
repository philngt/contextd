# pack-product — Prompt Overrides

## Self-Check append (cho mọi product doc generation)

```
### Product Documentation (pack-product)
- Brief có đủ 4 section: Problem, Target User, Success Metric, Acceptance Criteria
- OKR Key Results đều measurable (số + deadline)
- Persona có evidence base (n=, sources, date) — hoặc đánh dấu status: hypothesis
- Customer journey có touchpoints + emotion + drop-off (nếu có data)
- Roadmap commitment link brief tương ứng
- KHÔNG có jargon kỹ thuật trong main body (controller, schema, deployment, ...)
- KHÔNG dictate implementation (no "use Postgres", "build REST API", ...)
- Brief đủ ngắn để người quyết định scan; tách khi chứa nhiều outcome/owner/metric lifecycle độc lập, không theo word quota cố định
```

## Output style override

- **Audience**: assume reader là non-tech (PM, business, executive, customer-facing role).
- **Tone**: professional but plain. KHÔNG dùng condescending tone ("simply", "just"), KHÔNG dùng marketing fluff ("revolutionary", "next-gen", "cutting-edge").
- **Format**: prefer table + bullet over wall of text. Bold key numbers + dates.
- **Language**: match workspace language (mặc định Vietnamese nếu workspace dùng VN).

## Context priority cho `/business-view`

Khi dịch engineering doc sang business view, ưu tiên context theo thứ tự:

1. `{ws}/domains/` — business rule (highest, đây là ngôn ngữ chung)
2. `{ws}/product/personas/` — ai dùng cái này
3. `{ws}/product/briefs/` — tại sao build cái này
4. `{ws}/projects/{p}/services/` — service mô tả ngắn
5. `{ws}/platform/contracts/` — chỉ để biết boundary, KHÔNG copy schema vào output
6. `{ws}/platform/patterns/` — chỉ 1 câu "how it's built", KHÔNG copy chi tiết

Output `/business-view` luôn end with footnote: `> Technical reference: {list of source files}` để engineer track được nguồn.

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
