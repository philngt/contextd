# QA Recommendations — {evid-id}

> Template — auto-generated tại `{ws}/evidence/qa/{evid-id}/recommendations.md`
> bởi C8 (QA Recommender) khi `/evidence-qa` chạy với `source_type=code`.
>
> **READ-ONLY trong QA session** — agent và user KHÔNG sửa file này trực tiếp.
> Để override recommendation → chọn "Chỉnh sửa gợi ý" hoặc "Tự viết câu trả lời" trong AskUserQuestion.

**Evidence ID**: `{evid-id}`
**Generated**: {timestamp}
**Source snapshot**: raw.md@{git_sha[..7]}
**Scope**: P0 + P1 questions only.

> P2/P3 questions không có gợi ý — trả lời trực tiếp trong QA session.

---

## q-001 — {question title}  [P0]

**Kết luận**: NÊN THÊM
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**:
Pattern này xuất hiện đồng nhất ở 3 service với cùng cấu trúc (@KafkaListener + @Retryable(3) + DLQ routing). Tìm thấy đầy đủ trong c03#P-001. Extends kafka-consumer-pattern đã có trong wiki — không phải pattern mới hoàn toàn.

**Trích dẫn chính**:
- `(c03-pattern-proposals.md#P-001)` — 3 occurrences với cùng canonical flow
- `(raw.md#section-5:L42-L58)` — @KafkaListener + @Retryable annotation
- `({ws}/platform/patterns/kafka-consumer-pattern.md)` — base pattern để extends

**Đề xuất câu trả lời** _(hoàn chỉnh, dùng trực tiếp hoặc chỉnh sửa)_:
> Có, nên thêm vào platform patterns với tên `kafka-retry-dlq.md`.
> Pattern này extends `kafka-consumer-pattern.md` hiện có. Canonical flow theo c03#P-001.
> Config mặc định: retry_max=3, backoff=2s/4s/8s (exponential), DLQ suffix: `.dlq`.
> File tạo mới: `{ws}/platform/patterns/kafka-retry-dlq.md`

---

## q-002 — {question title}  [P1]

**Kết luận**: CẦN XEM XÉT THÊM
**Độ tin cậy**: VỪA ●●○

**Lý do phân tích**:
Service doc tìm thấy trong c02#S-003. Tuy nhiên ownership project chưa rõ — raw.md không có `@Owner` annotation hay comment rõ ràng. Cần user xác nhận project scope trước khi tạo file.

**Trích dẫn chính**:
- `(c02-service-map.md#S-003)` — service entry với type=kafka-consumer
- `(raw.md#section-6:L91-L110)` — @Service class có Javadoc ngắn

**Đề xuất câu trả lời** _(bổ sung thêm ownership trước khi accept)_:
> Có, cần service doc riêng với tên `{service-name}.md`.
> Ownership project: **[USER CẦN ĐIỀN]** — thuộc `{ws}/projects/{?}/services/`.
> Type: kafka-consumer. Entry-point: topic `{topic-name}`.

⚠️ _Gợi ý này cần xác nhận thêm: điền ownership project trước khi accept._

---

## q-003 — {question title}  [P1]

**Kết luận**: CHUYỂN CHUYÊN GIA
**Độ tin cậy**: THẤP ●○○

**Lý do phân tích**:
Câu hỏi về architectural decision (retry policy, SLA) — không có đủ evidence kỹ thuật trong code snapshot để kết luận chắc chắn. Cần xác nhận từ domain expert hoặc BA.

**Trích dẫn chính**:
- `(raw.md#section-3:L25)` — config value được redact hoặc thiếu
- `(c04-contract-proposals.md#C-002)` — contract proposal nhưng confidence = low

**Đề xuất câu trả lời**:
> _(Không đủ evidence kỹ thuật — nên defer to expert để xác nhận.)_

---

## P2/P3 — Không có gợi ý

_(P2/P3 questions được trả lời trực tiếp trong QA session. Danh sách: q-004, q-005, q-006.)_

<!-- Append entries theo format trên. KHÔNG sửa entries đã ghi. -->
