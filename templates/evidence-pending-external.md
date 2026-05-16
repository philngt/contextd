# Pending External Q&A — Evidence `{evid-id}`

> Template — auto-generated tại `{ws}/evidence/qa/{evid-id}/pending-external.md` khi user mark câu hỏi `defer-to-expert`.
> Format được tối ưu để **copy-paste vào email/Slack/Jira** gửi expert.
> KHI expert trả lời: hoặc (a) user paste answer khi chạy `/evidence-qa --resume --id <evid-id>`, hoặc (b) user edit `external-answers.md` rồi chạy resume.

**Workspace**: example-surgery
**Evidence**: 2026-05-04-paste-PROJ-1234 — PROJ-1234 timeout config change
**Created**: 2026-05-04T10:50:00+07:00
**Open count**: 1

---

## ✉️ Copy-paste block (gửi cho expert)

```
Hi {expert_name},

Mình đang sync wiki cho service surgery-service dựa trên changelog PROJ-1234.
Có {N} điểm cần bạn xác nhận để mình update đúng. Mỗi câu kèm context để bạn đỡ phải đào lại.

──────────────────────────────────────────────
Q1 (priority: P0, blocks_apply)
Topic: Retry policy cho Kafka consumer

Câu hỏi:
  Trong context PROJ-1234, retry policy mới cho Kafka consumer của
  surgery-service là 3 lần exponential backoff (2s/4s/8s) — đúng chưa?
  Nếu khác, giá trị chính xác là gì?

Context:
  - Wiki hiện tại (projects/surgery-service/services/kafka-consumer.md)
    ghi: 5 lần linear backoff 2s.
  - Changelog PROJ-1234 ghi: "exponential retry, max 3 attempts".
  - Mình cần con số chính xác để update bảng Failure Handling.

Trả lời:
  → (vui lòng reply inline)

──────────────────────────────────────────────

Cảm ơn bạn. Reply trước {expected_by} giúp mình nhé — sau đó wiki sẽ
được sync và team các bên không bị lag context.

— {your_name}
```

---

## Tracking table (machine-readable, dùng bởi `/evidence-qa --resume`)

| q-id  | priority | assigned_to             | channel | requested_at         | expected_by          | status              | resolved_at          |
|-------|----------|-------------------------|---------|----------------------|----------------------|---------------------|----------------------|
| q-002 | P0       | be-lead@example.com     | email   | 2026-05-04T10:50:00+07:00 | 2026-05-06T18:00:00+07:00 | awaiting_external   | —                    |

---

## Resume instructions

Khi có answer từ expert:

**Cách 1 — paste inline qua slash command** (đơn giản nhất):
```
/evidence-qa --resume --id 2026-05-04-paste-PROJ-1234
```
Claude sẽ hỏi từng câu pending → user paste answer → claude ghi `batch-{n}-answers.md` + update `todo.json`.

**Cách 2 — edit file thủ công** (nếu nhiều câu, expert reply qua text):
1. Mở `{ws}/evidence/qa/{evid-id}/external-answers.md` (tạo nếu chưa có).
2. Format mỗi answer:
   ```
   ## q-002
   - **From**: be-lead@example.com
   - **Received at**: 2026-05-06T09:15:00+07:00
   - **Answer**: 3 lần exponential 2s/4s/8s là đúng. Confirm.
   ```
3. Chạy `/evidence-qa --resume --id <evid-id>` → claude đọc `external-answers.md` và sync vào todo.

---

## Notes

- Nếu expert trả lời conflict với answer cũ → entry mới với `supersedes: q-XXX@<timestamp>`.
- Nếu expired (`expected_by` đã qua mà chưa có answer) → `/evidence-qa --resume` sẽ hỏi: extend deadline / escalate / skip / re-assign.
- Pending-external KHÔNG được delete tay — sẽ được tự động xóa khi tất cả entry resolved.
