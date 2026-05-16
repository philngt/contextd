# Evidence Q&A

Q&A loop với user dựa trên question pool + knowledge gaps + contradictions. Hỏi theo priority batches (P0→P3), hỗ trợ **defer-to-expert** (checkpoint cho người trả lời chậm), tự build `verified-facts.md`.

> Step 3 trong pipeline: ingest → analyze → **qa** → apply.
> Reference: [agents/pipeline/qa-batching.md](../../agents/pipeline/qa-batching.md), [agents/pipeline/evidence-lifecycle.md](../../agents/pipeline/evidence-lifecycle.md).

---

## Input

| Arg            | Required | Notes                                                                  |
|----------------|----------|------------------------------------------------------------------------|
| `--id`         | optional | Evid-id. Default: latest entry state ∈ `analyzed|qa_in_progress|qa_awaiting_external` |
| `--batch-size` | optional | 1-4. Default 4 (max do `AskUserQuestion` 4 questions/call).            |
| `--resume`     | optional | Flag — resume từ `qa_awaiting_external`. Đọc `external-answers.md`/hỏi user về pending. |
| `--priority`   | optional | Chỉ chạy 1 priority bucket: `P0|P1|P2|P3`. Default: P0 → P3 sequence.   |

---

## Bước 0 — Workspace check + Pack detection

1. Theo [workspace-resolution.md Profile A](../../agents/pipeline/workspace-resolution.md#profile-a--active-workspace-required). Set: `wiki_json_dir`, `workspace`, `effective_wiki_root`, `{ws}`.

2. **Pack detection** — resolve **effective_packs** theo [workspace-resolution.md Effective Packs Resolution](../../agents/pipeline/workspace-resolution.md#effective-packs-resolution) (`wiki.json#packs` override `workspace.md ## Packs`):
   - `solo_builder_active = "pack-solo-builder" in effective_packs`
   - Nếu `solo_builder_active = true` → **áp Non-tech UX overrides** suốt slash command này (xem [qa-batch-non-tech.md](../../packs/pack-solo-builder/agents/pipeline/qa-batch-non-tech.md)).
   - In: `📋 Non-tech UX mode active (pack-solo-builder)` ở đầu output.

   Cụ thể overrides ảnh hưởng:
   - **Bước 4b**: AskUserQuestion options dùng wording plain hơn ("Tôi biết — paste câu trả lời" thay vì "Trả lời", v.v.)
   - **Bước 4c "Defer to expert"**: hỏi thêm `expert_role` + `standard_to_check`; copy-paste block trong `pending-external.md` dùng template ngành (xem qa-batch-non-tech.md Override 4)
   - **Bước 4d Mini Contradiction Hunter**: SKIP (domain content thường có multiple valid views, contradiction check engineering-flavored sẽ false-positive)
   - **Bước 5 stop check**: wording plain ("câu hỏi quan trọng nhất" thay vì "P0+P1")
   - **Bước 6 verified-facts.md**: thêm fields `Field`, `Standard cited`, `Expert validated`; group thêm "Block: Glossary terms", "Block: Domain workflows", "Block: Standards & references"
   - **Bước 7 output**: wording plain (xem qa-batch-non-tech.md Override 6)

   Nếu `solo_builder_active = false` → giữ nguyên flow gốc (engineering UX).

## Bước 1 — Resolve evidence + state

1. Resolve `--id` (latest state ∈ {`analyzed`, `qa_in_progress`, `qa_awaiting_external`} nếu không truyền).
2. Workspace lock check (I-2).
3. Validate state theo flag:
   - Không `--resume`: state PHẢI = `analyzed`. Nếu = `qa_in_progress` → in warning "đã có Q&A đang chạy, dùng `--resume`".
   - Có `--resume`: state PHẢI ∈ {`qa_in_progress`, `qa_awaiting_external`}. Nếu `analyzed` → in warning "chưa có Q&A để resume, bỏ flag".

## Bước 2 — Build/load todo.json

### Initial run (state = `analyzed`)

1. Đọc `analysis/{id}/04-questions.md`, `analysis/{id}/02-contradiction.md`, `analysis/{id}/08-knowledge-gaps.md`.
2. Score mỗi question theo formula trong [qa-batching.md](../../agents/pipeline/qa-batching.md).
3. Tạo `qa/{id}/todo.json` từ template `templates/evidence-qa-todo.json`:
   - `state = qa_in_progress`
   - `questions[]` populated với priority + batch assignment
   - `batches[]` empty list ban đầu, sẽ append khi dispatch
4. Update `_index.md`: state → `qa_in_progress`.

### Resume run

1. Đọc `qa/{id}/todo.json` — bỏ qua questions đã `answered|skipped|deferred`.
2. Nếu có `qa/{id}/external-answers.md` → parse và sync:
   - Mỗi entry `## q-XXX` trong file → match question → status `awaiting_external` → `answered`, ghi `answer_ref`.
   - Append vào `batch-{n}-answers.md` của batch gốc với note "from external-answers.md".

## Bước 3 — Conversation context scan (heuristic, optional)

Trước khi mở batch đầu, scan recent user messages trong session hiện tại:
- Nếu user đã state thông tin liên quan đến 1 question pending → auto-fill answer với `confidence: medium` + flag `needs_confirm: true`.
- Push các câu này vào batch confirm-only đầu tiên (chỉ cần user gật đầu).

## Bước 3.5 — QA Recommendations pre-analysis  (source_type=code only)

Nếu `source.yaml#source_type == "code"`:

**Nếu `qa/{id}/recommendations.md` chưa tồn tại** (lần đầu hoặc fresh run):
1. In: `⏳ Đang phân tích code evidence để chuẩn bị gợi ý trả lời P0/P1...`
2. Invoke **C8 — QA Recommender** theo spec tại [code-analysis-prompts.md](../../agents/pipeline/code-analysis-prompts.md):
   - Inputs: `analysis/{id}/04-questions.md`, `analysis/{id}/c01-c04`, `sources/{id}/raw.md` (hoặc `raw.normalized.md`), `{ws}/platform/patterns/*.md`, `{ws}/platform/contracts/*.md`
   - Output: `qa/{id}/recommendations.md`
3. **Blocking**: chờ hoàn thành trước khi mở batch đầu tiên.
4. Parse `recommendations.md` → đếm theo Kết luận và Độ tin cậy.
5. In:
   ```
   ✅ Phân tích hoàn thành — {N} câu P0/P1 đã có gợi ý:
      ● ● ●  Chắc chắn : {n_h} câu
      ● ● ○  Cần xem xét: {n_m} câu
      ● ○ ○  Cần xác nhận: {n_l} câu
   ```

**Nếu `recommendations.md` đã tồn tại** (resume hoặc re-run) → skip generation, dùng file hiện có. In: `ℹ️  Dùng recommendations đã có từ lần trước.`

**Nếu `source_type ≠ code`** → skip toàn bộ Bước 3.5, không in gì.

## Bước 4 — Batch loop

For mỗi `priority ∈ [P0, P1, P2, P3]` (skip nếu `--priority` chỉ định 1 bucket):

  Lấy questions chưa answered/skipped/deferred ở priority này.
  Chia thành batches ≤ `--batch-size`.

  For mỗi batch:

  ### 4a. Display context

  Hiển thị `batch-{n}-questions.md` (tạo từ template `templates/evidence-qa-answers.md` ở trạng thái câu hỏi-only):
  - List N câu hỏi với context inline (vd nếu hỏi về `Config Overrides`, in 5 dòng table hiện tại của service doc).

  **Nếu `qa/{id}/recommendations.md` tồn tại**: với mỗi q-XXX trong batch có entry trong recommendations.md, render block gợi ý **trước** AskUserQuestion:

  ```
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📋  q-XXX [{P0|P1} — Blocking]
      "{question text đầy đủ}"
      Liên quan: {analysis file#section} | Ảnh hưởng: {ws}/{target-file}

  💡  Gợi ý (Độ tin cậy: {CAO ●●● | VỪA ●●○ | THẤP ●○○}):
      → {Kết luận: NÊN THÊM | KHÔNG NÊN THÊM | CẦN XEM XÉT THÊM | CHUYỂN CHUYÊN GIA}
      {Lý do phân tích: 2–3 câu rõ ràng, cite cụ thể}
      Trích dẫn: {citations}

  📝  Đề xuất câu trả lời (chỉnh sửa nếu cần):
      "{suggested answer text hoàn chỉnh}"
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```

  Nếu Độ tin cậy = THẤP → thêm: `⚠️ Gợi ý này cần xác nhận thêm — chỉ có 1 điểm trích dẫn.`

  Câu hỏi P2/P3 hoặc không có entry trong recommendations.md → hiển thị bình thường, không có block gợi ý.

  ### 4b. AskUserQuestion (1 call, N≤4 questions)

  Nếu câu hỏi có recommendation:
  ```
  - "Chấp nhận gợi ý" (description: dùng đề xuất câu trả lời phía trên, ghi credited to code-analyst)
  - "Chỉnh sửa gợi ý" (description: paste đề xuất vào Other rồi sửa trước khi submit)
  - "Tự viết câu trả lời" (description: bỏ qua gợi ý, paste answer riêng vào Other)
  - "Defer to expert" (description: claude sẽ hỏi assignee + channel + deadline)
  - "Skip" (description: P0/P1 sẽ block apply; P2/P3 OK)
  ```

  Nếu câu hỏi KHÔNG có recommendation (P2/P3 hoặc không có entry):
  ```
  - "Trả lời" (description: paste answer in Other text input)
  - "Defer to expert" (description: claude sẽ hỏi assignee + channel + deadline)
  - "Skip" (description: P0/P1 sẽ block apply; P2/P3 OK)
  - "Defer to next session" (description: park, không gửi expert)
  ```

  ### 4c. Process answers

  Loop từng question:

  - **"Chấp nhận gợi ý"**:
    - Đọc `recommendations.md#q-XXX#Đề xuất câu trả lời` → lấy suggested answer text.
    - Append `## q-XXX` block vào `batch-{n}-answers.md`:
      ```
      - Status: answered
      - Answered by: self
      - Via: code-analyst-recommend (confidence: {CAO→high | VỪA→medium | THẤP→low})
      - Confidence: {high|medium|low}
      ```
      Answer = suggested answer text từ recommendations.md. Evidence cited = citations từ recommendations.md.
    - Update `todo.json`: `status=answered`, `answered_by=self`.

  - **"Chỉnh sửa gợi ý"** + Other text (bản đã sửa):
    - Xử lý như "Trả lời" với answer = text user paste (đã chỉnh từ gợi ý).
    - Ghi `Via: code-analyst-recommend (user-modified)` để audit trail.
    - Update `todo.json`: `status=answered`, `answered_by=self`.

  - **"Tự viết câu trả lời"** + Other text:
    - Xử lý như "Trả lời" gốc — không ghi `Via`.
    - Append `## q-XXX` block vào `batch-{n}-answers.md` (status=answered, by=self, confidence=high).
    - Update `todo.json`: `status=answered`, `answered_by=self`.

  - **"Trả lời"** + Other text (P2/P3 không có recommendation):
    - Append `## q-XXX` block vào `batch-{n}-answers.md` (status=answered, by=self, confidence=high)
    - Update `todo.json`: `status=answered`, `answer_ref`, `answered_at`, `answered_by=self`

  - **"Defer to expert"**:
    - Gọi AskUserQuestion lần nữa (1 question gộp): "Expert info cho q-XXX: assigned_to (email/name)? channel (email/slack/jira/teams/in_person/other)? expected_by (date)?" → user paste structured.
    - Update `todo.json`: `status=awaiting_external`, populate `external{}`.
    - Append/update `pending-external.md` (template `templates/evidence-pending-external.md`):
      - Tạo file nếu chưa có
      - Append section `## ✉️ Copy-paste block` cho question này (gồm context wiki + question phrased cho expert)
      - Update tracking table

  - **"Skip"**:
    - AskUserQuestion 1 lần ngắn: "Lý do skip? (optional)"
    - Update `todo.json`: `status=skipped`, log reason vào `batch-{n}-answers.md`

  - **"Defer to next session"**:
    - Update `todo.json`: `status=deferred`. Không touch pending-external.

  ### 4d. Mini Contradiction Hunter

  Sau khi process xong batch:
  - Chạy mini prompt: "Có answer nào trong batch này mâu thuẫn với (a) answers trước đó trong evidence này, (b) `02-contradiction.md`, (c) wiki hiện tại của `{ws}`?"
  - Nếu có conflict → tạo follow-up question `q-XXX-followup` với cùng priority gốc, push vào batch tiếp theo (cùng priority bucket).

  ### 4e. Update todo.json + _index.md

  - `todo.json#updated_at` = now
  - Nếu có ≥1 `awaiting_external` → state `qa_awaiting_external` (in `_index.md` cập nhật cột `blocked_on`).
  - Else state vẫn `qa_in_progress`.

## Bước 5 — Stop check (sau khi finish 1 priority bucket)

After P0+P1 batches done:
- Nếu mọi P0/P1 question status ∈ {`answered`, `skipped`, `deferred`} (KHÔNG awaiting_external):
  - Hỏi 1 lần qua AskUserQuestion: **"P0+P1 đã clear. Tiếp tục P2/P3 hay đủ?"** Options: ["Continue P2/P3", "Stop here"].
  - Nếu Stop → mọi P2/P3 pending mark `deferred` → đi tới Bước 6.
  - Nếu Continue → tiếp Bước 4 cho P2 → P3.

After all assigned priorities done:
- Nếu state vẫn `qa_in_progress` (không awaiting_external) → đi Bước 6.
- Nếu `qa_awaiting_external` → STOP, in instruction (xem Bước 8).

## Bước 6 — Build verified-facts.md

Khi state ready để chuyển `qa_done`:

1. Tạo/overwrite `qa/{id}/verified-facts.md` theo schema trong [qa-batching.md](../../agents/pipeline/qa-batching.md).
2. Group facts theo affected file (`Block: Contracts`, `Block: Service config`, `Block: Domain workflow`, ...).
3. Mỗi fact PHẢI có:
   - `Confidence: high|medium|low`
   - `Source: q-XXX (self|expert: <email>) — answered <date>`
   - `Affects: {ws}/path/to/file.md` (relative)
4. Section "Open / deferred" liệt kê P2/P3 deferred (informational).

## Bước 7 — Transition to qa_done

1. Update `_index.md`: state → `qa_done`, `last_updated` = today, `blocked_on` = `—`.
2. Update `todo.json#state = qa_done`.
3. In:
   ```
   ✅ Q&A complete — {evid-id}
      Answered : {N} (self: {x}, expert: {y})
      Skipped  : {N}
      Deferred : {N} (P2/P3 only)
      State    : qa_done

   Verified facts ready: {ws}/evidence/qa/{id}/verified-facts.md

   Next:
     /evidence-apply --id {id} --mode update    → push facts to wiki
     /evidence-apply --id {id} --mode rebase    → rebase wiki using facts as source-of-truth
   ```

## Bước 8 — Pause for awaiting_external

Khi có ≥1 P0/P1 status=`awaiting_external` và không thể đi tiếp:

1. Update `_index.md`: state=`qa_awaiting_external`, `blocked_on` = list `assigned_to (q-id, due {date})`.
2. Đảm bảo `pending-external.md` đã có copy-paste block cho mọi external entry.
3. In:
   ```
   ⏸  Q&A paused — waiting for external answers
      Evidence : {evid-id}
      Pending  : {N} questions (P0={x}, P1={y})
      File     : {ws}/evidence/qa/{id}/pending-external.md

   To send to experts:
     1. Open pending-external.md
     2. Copy ✉️ blocks → email/slack/jira
     3. Set deadline reminders

   When answers arrive:
     /evidence-qa --resume --id {evid-id}
     (paste answers inline OR edit external-answers.md first)
   ```

---

## Resume mode chi tiết

`--resume` flow:

1. Đọc `todo.json` lọc `status=awaiting_external`.
2. Đọc `external-answers.md` nếu có:
   - Format expected: section `## q-XXX` + `**Answer**: ...` + `**From**: <expert>` + `**Received at**: <ts>`.
   - Parse → match q-id → process như "Trả lời" trong Bước 4c (status → answered, by=expert).
3. Cho mọi entry awaiting_external CHƯA có trong external-answers.md:
   - Gọi AskUserQuestion: "q-XXX (assigned to {expert}, due {date}): Đã có answer?"
   - Options: ["Yes — paste answer", "Still waiting", "Expired/escalate", "Skip"]
   - "Yes" → user paste answer → process như answered (by=expert)
   - "Still waiting" → giữ awaiting_external, optional update expected_by
   - "Expired/escalate" → ask cho new assignee/deadline OR mark `skipped` với reason "expired"
   - "Skip" → status=skipped
4. Sau khi xử lý hết → re-evaluate stop condition (Bước 5).
5. Nếu mọi P0/P1 cleared → đi tiếp Bước 6 (verified-facts) và Bước 7.
6. Nếu vẫn còn awaiting_external → trở lại Bước 8.

---

## Common errors

| Error                              | Fix                                                                |
|------------------------------------|--------------------------------------------------------------------|
| State ≠ analyzed (no --resume)     | `/evidence-analyze` first                                          |
| State = qa_done                    | Đã xong, dùng `/evidence-apply`                                    |
| Workspace lock fail                | `/switch-workspace {workspace_at_ingest}`                          |
| `external-answers.md` malformed    | Edit theo schema; rerun `--resume`                                 |
| User dừng giữa batch (Ctrl+C)      | Re-run command — state đã persist trong `todo.json`                |
| Câu hỏi đã answered nhưng follow-up vô tận | Hard cap: 2 follow-up rounds per question; thứ 3 → mark `INVESTIGATE` trong verified-facts |
| `recommendations.md` trống / thiếu câu | C8 agent không tìm thấy analysis files — chạy `/evidence-analyze --id {id}` trước |
| Recommendations.md sai / outdated  | Xóa `qa/{id}/recommendations.md`, re-run `/evidence-qa` để tạo lại |
| source_type != code nhưng vẫn chờ recommendations | Không xảy ra — Bước 3.5 skip khi source_type ≠ code |
