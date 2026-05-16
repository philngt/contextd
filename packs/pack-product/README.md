# pack-product

Product / business knowledge pack — dành cho **người non-tech** (PM, product owner, business analyst, stakeholder) đóng góp vào wiki mà không cần hiểu code.

## Khi nào bật

- Workspace có người non-tech tham gia maintain wiki
- Cần track product roadmap, OKR, customer journey, success metrics
- Engineering muốn link feature implementation ↔ product context (brief, persona, metric)

## Components

- `brief`: product brief / PRD / feature spec
- `okr`: objectives & key results, KPI tracking
- `roadmap`: milestones, quarterly plans, release plan
- `persona`: user/customer persona, ICP
- `journey`: customer journey, funnel, touchpoint
- `metric`: success metrics, north star, retention/activation/conversion

## Constraints highlights

- Mỗi product brief PHẢI có: problem statement, target user, success metric, acceptance criteria — không có thì không phải brief
- Mỗi OKR PHẢI measurable (Key Result có số + deadline)
- Persona phải dựa trên user research / data, không tự nghĩ ra
- Roadmap commitments phải link tới brief tương ứng
- Plain-language: KHÔNG dùng jargon kỹ thuật (controller, schema, container, ...) trong product docs — đó là việc của `/business-view` translate sang

## Validator rules

| Rule | Severity | Check |
|------|----------|-------|
| `pack-product-brief-missing-metric` | error | Product brief thiếu section "Success Metric" hoặc "Metric" |
| `pack-product-brief-missing-acceptance` | error | Product brief thiếu "Acceptance Criteria" |
| `pack-product-okr-missing-number` | warn  | Key Result không chứa số đo (`%`, số tuyệt đối, ngày) |
| `pack-product-jargon-leak` | warn  | Product doc chứa từ kỹ thuật (controller, schema, deployment, container, ...) — gợi ý dịch sang business |

## Bật pack

```md
## Packs

- pack-product
```

## Slash commands liên quan

- `/product-brief` — wizard tạo product brief mới (cho PM/business, không cần biết code)
- `/business-view {feature|service}` — dịch service/contract kỹ thuật sang góc nhìn business
- `/wiki-explain {topic}` — giải thích pattern/contract bằng plain language

## Cấu trúc khuyến nghị trong workspace

```
workspaces/{ws}/product/
├── briefs/              # product briefs / PRD
│   └── {slug}.md
├── okrs/                # OKR per quarter
│   └── 2026-Q1.md
├── roadmap.md           # high-level roadmap
├── personas/            # user personas
│   └── {persona-name}.md
├── journeys/            # customer journeys
│   └── {journey-name}.md
└── metrics.md           # north star + supporting metrics
```

> Folder `product/` song song với `platform/`, `domains/`, `projects/`. Engineers đọc `platform/`, PMs đọc `product/`. Cả hai liên kết qua `domains/` (business rules dùng chung).
