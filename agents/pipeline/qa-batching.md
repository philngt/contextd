# Q&A Batching Strategy

Reference cho `/evidence-qa`. Quy tắc score câu hỏi → priority bucket → batch order → stop condition.

---

## Priority scoring

Mỗi câu hỏi sinh ra từ `04-questions.md` được score dựa trên 4 factor:

| Factor               | Weight | Source                                                |
|----------------------|--------|-------------------------------------------------------|
| `blocks_apply`       | 4      | Derived — xem rule bên dưới                            |
| `contradiction_weight` | 3    | True nếu câu hỏi resolve mâu thuẫn raw vs wiki trong `02-contradiction.md` |
| `gap_severity`       | 2      | Derived từ `08-knowledge-gaps.md` — xem rule bên dưới  |
| `user_cost_inverse`  | 1      | Câu hỏi user trả nhanh (≤ 30s) cộng điểm; cần expert trừ điểm |

**Authoritative source** cho gap classification:

> [`08-knowledge-gaps.md`](critical-analysis-prompts.md) là **single source of truth** cho việc 1 câu hỏi có blocking hay không. qa-batching KHÔNG re-classify — chỉ derive.

Rule:
- `blocks_apply = true` ⇔ câu hỏi resolve 1 gap được mark `[BLOCKING]` trong `08-knowledge-gaps.md` HOẶC resolve 1 contradiction (b) trong `02-contradiction.md` mà bên thắng cuộc đòi sửa wiki.
- `gap_severity` mapping từ 08:
  - `[BLOCKING]` → High (giá trị 2)
  - `[NICE-TO-HAVE]` → Low (giá trị 0.5)
  - Gap inferred từ `02-contradiction.md` (không có trong 08) → Med (giá trị 1)
- Nếu câu hỏi không link tới gap nào trong 08 → `gap_severity = 0`.

Mọi disagreement giữa 08 và qa-batching phải được giải bằng cách re-run prompt CORE 8, KHÔNG chỉnh tay trong qa.

**Formula**:
```
score = 4*blocks_apply + 3*contradiction_weight + 2*gap_severity + user_cost_inverse
```

**Bucket mapping**:
- `score ≥ 7` → **P0** (blocks_apply)
- `5 ≤ score < 7` → **P1** (contradictions)
- `3 ≤ score < 5` → **P2** (gaps non-blocking)
- `score < 3` → **P3** (nice-to-know, insight, counter-arg)

---

## Batch construction

- **Batch size default**: 4 (giới hạn `AskUserQuestion` API).
- **Max questions per batch**: 4.
- **Batch order**: P0 → P1 → P2 → P3.
- Trong cùng priority, sắp theo `score` desc.
- Nếu cùng batch có câu cần expert (`user_cost_inverse < 0`) → tách ra batch riêng để user dễ quyết định "trả lời ngay" vs "defer to expert" cùng lúc.

---

## Asking flow (per batch)

1. Hiển thị `batch-{n}-questions.md` (markdown preview cho user).
2. Gọi `AskUserQuestion` với 4 question objects. Mỗi question có **3 explicit options** (AskUserQuestion tự thêm "Other" làm option thứ 4):
   - **Defer to expert** (description: claude sẽ thu metadata assigned_to + channel + deadline ở bước sau)
   - **Skip** (description: P0/P1 sẽ block apply; P2/P3 OK)
   - **Defer to next session** (description: park lại, không gửi expert)
   - "Other" (auto-provided) → user paste **answer trực tiếp** vào field này
3. Process answers:
   - **Other (direct answer)** → ghi `batch-{n}-answers.md` + status=`answered`. Note `answered_by: self`.
   - **Defer to expert** → xem section "Expert metadata batch flow" bên dưới → status=`awaiting_external` + push vào `pending-external.md`.
   - **Skip** → status=`skipped` + record reason (optional follow-up).
   - **Defer to next session** → status=`deferred`, không vào pending-external.
4. **Mini Contradiction Hunter** trên answer mới:
   - Đọc lại `02-contradiction.md` + `verified-facts.md`.
   - Nếu answer mâu thuẫn → tạo follow-up question `q-XXX-followup` ở batch tiếp.
5. Update `todo.json`.

### Expert metadata batch flow

Khi ≥1 question trong batch chọn `Defer to expert`:

- **Nếu chỉ 1 question defer**: gọi `AskUserQuestion` 1 lần nữa với 3 question objects (assigned_to, channel, expected_by).
- **Nếu nhiều question defer cùng batch**: gọi `AskUserQuestion` 1 lần với 3 question objects, **shared metadata cho tất cả questions defer trong batch**. User chọn "Other" cho 1 trong 3 nếu cần override per-question.
  - Default options cho `assigned_to`: gợi ý expert đã từng dùng (đọc `pending-external.md` past entries) + 1 option "Different per question (loop hỏi từng câu)".
  - Nếu user chọn "Different per question" → loop từng question còn pending external metadata.
- Tạo 1 checkpoint `ckpt-{NNN}` per batch (KHÔNG merge với checkpoint batch trước, để audit trail rõ ràng theo thời gian).

---

## Stop conditions

`/evidence-qa` kết thúc khi mỗi câu P0 và P1 đều ở 1 trong 4 trạng thái:
- `answered`
- `awaiting_external` (tạm OK — sẽ block ở `evidence-apply`)
- `skipped`
- `deferred`

Khi P0+P1 đã clear (không còn `pending`):
- Hỏi user: **"P0+P1 đã xử lý. Tiếp tục P2/P3 hay đủ?"** (AskUserQuestion 2 options: "Continue P2/P3" | "Stop here").
- Nếu `Stop here` → P2/P3 còn `pending` được auto-mark `deferred`.

State transition:
- Nếu mọi P0/P1 = `answered|skipped` (KHÔNG có `awaiting_external`) → state `qa_done`.
- Nếu có ≥1 `awaiting_external` ở P0/P1 → state `qa_awaiting_external`. User chạy `/evidence-qa --resume` sau khi expert reply.

---

## Resume flow (`--resume`)

Khi user chạy `/evidence-qa --resume --id <evid-id>`:

1. Đọc `todo.json` + `pending-external.md`.
2. Cho mỗi entry `awaiting_external`:
   - Đọc `external-answers.md` (nếu user đã edit tay) → parse Q-ID → answer.
   - Nếu không có entry trong `external-answers.md` → gọi `AskUserQuestion` hỏi: "Đã có answer cho `q-XXX`?" (options: Yes/paste | Still waiting | Expired/escalate | Skip).
3. Update `todo.json` + ghi append vào `batch-{n}-answers.md` của batch gốc.
4. Re-evaluate stop condition. Nếu mọi P0/P1 cleared → `qa_done`.
5. Re-generate `verified-facts.md`.

---

## Verified facts synthesis (when state → qa_done)

`/evidence-qa` build `verified-facts.md` theo format:

```markdown
# Verified Facts — Evidence `{evid-id}`

> Authoritative answers, sẵn sàng cho `/evidence-apply`.
> Mỗi fact = (claim, answer, confidence, source, target_wiki_file).

## Block: Contracts
### F-001 — Topic `surgery.event.timeout` chưa register, cần thêm
- Confidence: high
- Source: q-001 (self) — answered 2026-05-04
- Affects: `{ws}/platform/contracts/mqtt-topic-contract.md` (Registered Types table)

## Block: Service config
### F-002 — Retry policy = 3 lần exponential 2s/4s/8s
- Confidence: high (expert confirmed)
- Source: q-002 (expert: be-lead@example.com) — answered 2026-05-06
- Affects: `{ws}/projects/surgery-service/services/kafka-consumer.md` (Failure Handling)

## Block: Domain workflow
(... v.v.)

## Open / deferred (informational, không block apply)
- q-004 (P3, insight): ... — deferred
```

---

## Heuristics

- **Đừng hỏi câu user vừa trả qua context khác**. Trước batch, scan recent conversation messages — nếu user đã state thông tin đó, auto-fill answer + flag `confidence: medium` + ask confirm 1 câu.
- **Group related questions**. Nếu 2 câu cùng affect 1 file/section → đặt cùng batch (user load context 1 lần).
- **Show wiki context inline**. Khi hỏi q-XXX về `Config Overrides` table, hiển thị bảng hiện tại 5 dòng để user không phải mở file.
- **Time-box**. Nếu 1 batch tốn > 5 phút → dump hết câu còn lại của batch vào `defer to next session` rồi thoát; user chạy lại sau.
