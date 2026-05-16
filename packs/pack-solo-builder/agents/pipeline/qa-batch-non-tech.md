# QA UX Overrides for Non-tech (`/evidence-qa`)

UX adjustments áp dụng khi `pack-solo-builder` active. Áp lên `/evidence-qa` đã có — KHÔNG tạo command mới, chỉ điều chỉnh hành vi.

## Detect rule

`/evidence-qa` Bước 0 sau khi resolve workspace, đọc `workspace.md ## Packs`:
- `pack-solo-builder` active → áp toàn bộ overrides bên dưới.
- Else → giữ nguyên flow gốc.

## Override 1: Skip Bước 3.5 (QA Recommender) khi không phải code source

Đã có sẵn trong `/evidence-qa` Bước 3.5 (`source_type ≠ code → skip`). Không cần đổi gì.

## Override 2: Wording adjustments cho AskUserQuestion

Khi pack-solo-builder active, thay vì:

```
- "Trả lời" (paste answer in Other text input)
- "Defer to expert" (claude sẽ hỏi assignee + channel + deadline)
- "Skip" (P0/P1 sẽ block apply)
- "Defer to next session"
```

Dùng wording plain hơn:

```
- "Tôi biết — paste câu trả lời" (description: gõ trực tiếp vào Other)
- "Hỏi expert giúp tôi" (description: claude sẽ chuẩn bị câu hỏi cho expert + ghi tên/email/channel để bạn forward)
- "Bỏ qua câu này — không quan trọng" (description: đánh dấu skip, KHÔNG block các bước sau)
- "Tạm dừng — hỏi lại sau" (description: lưu lại để session sau)
```

Đặc biệt: KHÔNG dùng từ "P0/P1 sẽ block apply" — non-tech không hiểu priority code. Thay bằng "câu này khá quan trọng, nếu bỏ qua thì wiki sẽ thiếu thông tin".

## Override 3: Skip Mini Contradiction Hunter (Bước 4d) cho domain content

Mini Contradiction Hunter so sánh answer mới với wiki hiện tại — assume wiki có structured contracts/patterns. Domain knowledge thường có **multiple valid views** (vd 2 phương pháp tính moment uốn đều đúng tuỳ standard). Skip để tránh false-positive contradiction.

Khi pack-solo-builder active:
- Skip Bước 4d hoàn toàn.
- Thay bằng: log "Note: domain content — manual review recommended" vào `batch-{n}-answers.md` nếu user trả lời khác nhiều với raw.

## Override 4: Defer-to-expert UX cho domain expert

`/evidence-qa` Bước 4c "Defer to expert" hỏi: assignee + channel + deadline. Khi non-tech mode, hỏi thêm:

```
- expert_role: vd "kỹ sư thiết kế kết cấu senior", "kế toán trưởng", "bác sĩ chuyên khoa nội"
- standard_to_check: vd "JIS B 8265", "Thông tư 78/2014/TT-BTC", "ICD-10 chương 9"
```

Pull `expert_hint` từ `04-questions.md` của câu đang defer — đã có sẵn trong DOMAIN 4 output schema.

Pre-fill copy-paste block `pending-external.md` với context phù hợp expert ngành (thay vì engineering context):

```
Hi {expert_name},

Tôi đang build wiki kiến thức cho {field} workspace. Có 1 điểm cần xác nhận từ chuyên gia:

Term/quy tắc: {term hoặc rule từ raw}
Source: {raw filename + line range}
Câu hỏi: {q-XXX text}

(Nếu có) Standard tham chiếu: {standard_to_check}

Có thể giúp confirm trong vòng {deadline}?

Cảm ơn!
```

## Override 5: verified-facts.md format

Khi pack-solo-builder active, mỗi fact ngoài fields chuẩn (`Confidence`, `Source`, `Affects`) có thêm:
- `Field: {co-khi|ke-toan|y-te|...}` — ngành nào
- `Standard cited: {nếu có}` — standard official được fact này refer
- `Expert validated: {yes|no}` — answer đến từ expert (expert role) hay self

Group section thêm:
- "Block: Glossary terms" → facts add term mới
- "Block: Domain workflows" → facts mô tả quy trình
- "Block: Standards & references" → facts cite standard

Schema mở rộng phía trên cũng phải tương thích `/evidence-apply` parse — apply route theo `Affects` path như cũ.

## Override 6: Wording trong stop check + verified-facts output

Bước 5: Thay vì "P0+P1 đã clear. Tiếp tục P2/P3 hay đủ?", dùng:

> "Đã trả lời các câu hỏi quan trọng nhất. Bạn muốn tiếp tục các câu hỏi sâu hơn hay dừng ở đây?"

Bước 7: Output console plain hơn:

```
✅ Q&A xong — {evid-id}
   Trả lời      : {N} (tự bạn: {x}, expert: {y})
   Bỏ qua       : {N}
   Hỏi lại sau  : {N}
   Trạng thái   : Sẵn sàng đưa vào wiki

Facts đã verify nằm tại: {ws}/evidence/qa/{id}/verified-facts.md

Bước tiếp:
  /evidence-apply --id {id} --mode update
  → Đưa các facts đã verify vào wiki ({ws}/domains/...)
```

## Apply pipeline note

`/evidence-apply` không cần phân nhánh — nó đọc `verified-facts.md#Affects` field và route theo path. Khi pack-solo-builder active, paths sẽ point tới `{ws}/domains/...` thay vì `{ws}/platform/...` → tự động đúng layer, không cần override.
