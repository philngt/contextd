# pack-product — Retrieval Map

| Component | Docs to Retrieve (relative `{ws}/`) |
|-----------|-------------------------------------|
| `brief`    | `product/briefs/`, `product/personas/`, `product/metrics.md` |
| `okr`      | `product/okrs/`, `product/roadmap.md`, `product/metrics.md` |
| `roadmap`  | `product/roadmap.md`, `product/briefs/`, `product/okrs/` |
| `persona`  | `product/personas/`, `product/journeys/` |
| `journey`  | `product/journeys/`, `product/personas/`, `product/metrics.md` |
| `metric`   | `product/metrics.md`, `product/okrs/`, `product/briefs/` |

## Cross-pack retrieval (khi feature span product ↔ engineering)

Khi `/business-view` hoặc `/wiki-explain` được gọi, retrieval CÓ THỂ kéo từ các path engineering nhưng **chỉ để summarize, không expose jargon**:

| Source | Use |
|--------|-----|
| `platform/contracts/*.md` | Identify capability boundary, không dùng schema chi tiết |
| `platform/patterns/*.md` | Identify "how this is built" (1 câu mô tả, không deep) |
| `projects/{p}/services/*.md` | Identify "what this service does for users" |
| `domains/{domain}/*.md` | Business rules — dùng nguyên văn, đây là cầu nối product ↔ engineering |

> Path là gợi ý chuẩn — workspace có thể đặt tên khác. Nếu file không tồn tại → ghi vào Knowledge Gaps, không guess.
