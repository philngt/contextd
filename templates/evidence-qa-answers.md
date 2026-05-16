# Q&A Answers — Batch {N}

> Template — copy thành `{ws}/evidence/qa/{evid-id}/batch-{N}-answers.md`.
> Append-only. KHÔNG sửa câu trả lời cũ. Nếu sai → tạo entry mới với `supersedes: <q-id>@<timestamp>`.

**Evidence ID**: `{evid-id}`
**Batch**: {N}
**Priority bucket**: P{0|1|2|3}
**Asked at**: 2026-05-04T10:40:00+07:00

---

## q-001 — Topic name mới `surgery.event.timeout` đã được register ở contract chưa?

- **Status**: answered
- **Answered at**: 2026-05-04T10:45:00+07:00
- **Answered by**: self
- **Confidence**: high

**Answer**:
Chưa. Contract hiện tại trong `platform/contracts/mqtt-topic-contract.md` không có entry cho `surgery.event.timeout`. Cần thêm dòng mới vào bảng Registered Types trước khi update service doc.

**Evidence cited**:
- `platform/contracts/mqtt-topic-contract.md` (Registered Types table — không có entry này)
- Raw source: `sources/2026-05-04-paste-PROJ-1234/raw.json#/changes/0`

---

## q-002 — BE lead xác nhận retry policy mới là 3 lần exponential 2s/4s/8s?

- **Status**: awaiting_external
- **Assigned to**: be-lead@example.com
- **Channel**: email
- **Requested at**: 2026-05-04T10:50:00+07:00
- **Expected by**: 2026-05-06T18:00:00+07:00
- **Note**: Cần confirm trước khi update wiki cho release Friday.

**Question paraphrased for expert** (xem `pending-external.md` để paste):
> Trong context của PROJ-1234, retry policy mới cho Kafka consumer của surgery-service là 3 lần exponential 2s/4s/8s — đúng chưa? Nếu khác, giá trị chính xác là gì?

---

## q-003 — Mâu thuẫn: changelog ghi timeout 30s nhưng service doc ghi 45s

- **Status**: skipped
- **Skipped at**: 2026-05-04T10:55:00+07:00
- **Reason**: User chưa kiểm tra được production config, defer P2.

---

<!-- Append future entries dưới dòng này. KHÔNG xóa entry cũ. -->
