# pack-product — Validator Rules

Layer-1 rule. Implement: [`scripts/rules.py`](../../scripts/rules.py). Prefix `pack-product-`.

Áp dụng cho file `.md` trong `{ws}/product/` (và file output của `/product-brief`).

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-product-brief-missing-metric` | error | Brief file (`product/briefs/*.md`) thiếu section heading chứa từ "Metric" / "Success Metric" |
| `pack-product-brief-missing-acceptance` | error | Brief file thiếu section "Acceptance Criteria" / "Acceptance" |
| `pack-product-brief-missing-problem` | error | Brief file thiếu section "Problem" / "Problem Statement" |
| `pack-product-okr-missing-number` | warn | Key Result line không chứa số đo (`%`, digit, hoặc currency) |
| `pack-product-jargon-leak` | warn | Product doc chứa technical jargon (controller, schema, deployment, container, microservice, refactor, endpoint, payload, ORM, JPA, ...) trong body |
| `pack-product-roadmap-vague-date` | warn | Roadmap dùng "soon", "next sprint", "Q?", "TBD" thay vì `YYYY-Qx` / `YYYY-MM` |
| `pack-product-brief-dictates-impl` | warn | Brief chứa instruction kỹ thuật cụ thể (`use Postgres`, `build REST API`, `deploy on AWS`, `use Kafka`, ...) — implementation là quyết định engineering |

## Layer-2 self-check

```md
### Product Documentation (pack-product)
- Brief có đủ 4 section: Problem, Target User, Success Metric, Acceptance Criteria
- OKR Key Results đều measurable
- Persona có evidence base
- Roadmap commitment link brief
- Không jargon kỹ thuật trong body
- Không dictate implementation
```

## Limitations

- Regex-only — jargon detection có thể false-positive khi từ kỹ thuật xuất hiện trong link description hoặc footnote "Technical reference".
- `brief-dictates-impl`: chỉ catch keyword phổ biến, không hiểu context (vd "we already use Postgres for data" trong context section là OK, không phải dictate).
- Section detection dựa trên markdown heading (`## Section`) — brief dùng format khác (vd HTML, table-only) sẽ false-negative.
- Roadmap date check không validate date trong tương lai vs quá khứ.
